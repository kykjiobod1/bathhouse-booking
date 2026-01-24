from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
import logging
import time
import pytz

from ..states import BookingStates
from ..keyboards import bathhouses_keyboard, date_selection_keyboard, slots_keyboard, payment_confirmation_keyboard
from bathhouse_booking.bookings.models import Bathhouse, Client, SystemConfig
from bathhouse_booking.bookings import services

logger = logging.getLogger(__name__)


async def _cleanup_previous_messages(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """Удалить предыдущие сообщения с клавиатурами"""
    try:
        # Проверяем, что сообщение доступно
        if not callback_query.message or isinstance(callback_query.message, types.InaccessibleMessage):
            return
            
        data = await state.get_data()
        chat_id = callback_query.message.chat.id
        
        # Удаляем сообщения с клавиатурами, если они есть
        message_ids_to_delete = []
        
        if 'bathhouse_selection_message_id' in data and data['bathhouse_selection_message_id']:
            message_ids_to_delete.append(data['bathhouse_selection_message_id'])
        
        if 'date_selection_message_id' in data and data['date_selection_message_id']:
            message_ids_to_delete.append(data['date_selection_message_id'])
        
        if 'slots_selection_message_id' in data and data['slots_selection_message_id']:
            message_ids_to_delete.append(data['slots_selection_message_id'])
        
        # Удаляем сообщения
        for msg_id in message_ids_to_delete:
            try:
                await callback_query.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                # Игнорируем ошибки удаления (сообщение уже удалено или недоступно)
                logger.debug(f"Failed to delete message {msg_id}: {e}")
        
        # Очищаем сохраненные ID сообщений
        await state.update_data(
            bathhouse_selection_message_id=None,
            date_selection_message_id=None,
            slots_selection_message_id=None
        )
        
    except Exception as e:
        logger.error(f"Error in cleanup_previous_messages: {e}")


async def _update_activity_timestamp(state: FSMContext) -> None:
    """Обновить timestamp последней активности"""
    await state.update_data(last_activity=time.time())

router = Router()


@router.callback_query(lambda c: c.data == "book_bathhouse")
async def start_booking(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    if callback_query.message:
        # Удаляем предыдущие сообщения с клавиатурами
        await _cleanup_previous_messages(callback_query, state)
        
        try:
            # Получаем или создаем клиента
            client, created = await sync_to_async(Client.objects.get_or_create)(
                telegram_id=str(callback_query.from_user.id),
                defaults={
                    'name': callback_query.from_user.full_name or callback_query.from_user.first_name or "Unknown",
                    'phone': "",
                    'telegram_id': str(callback_query.from_user.id)
                }
            )
            
            # Проверяем лимит активных бронирований
            await sync_to_async(services.check_booking_limit)(client)
            
            # Лимит не превышен, продолжаем процесс бронирования
            start_msg = await callback_query.message.answer("Начинаем процесс бронирования...")
            await state.set_state(BookingStates.waiting_for_bathhouse)
            await _update_activity_timestamp(state)
            
            # Сохраняем ID стартового сообщения
            await state.update_data(start_message_id=start_msg.message_id)
            
            # Получить список активных бань из БД (асинхронно)
            bathhouses = await sync_to_async(lambda: list(Bathhouse.objects.filter(is_active=True)))()
            if bathhouses:
                keyboard = bathhouses_keyboard(bathhouses)
                selection_msg = await callback_query.message.answer("Выберите баню:", reply_markup=keyboard)
                # Сохраняем ID сообщения с выбором бани
                await state.update_data(bathhouse_selection_message_id=selection_msg.message_id)
            else:
                await callback_query.message.answer("К сожалению, сейчас нет доступных бань для бронирования.")
                await state.clear()
                
        except ValidationError as e:
            from ..keyboards import back_to_main_keyboard
            # Обрабатываем ошибку лимита бронирований
            error_message = str(e)
            if "У вас уже есть" in error_message and "активных бронирований" in error_message:
                # Показываем пользователю понятное сообщение об ошибке лимита
                await callback_query.message.answer(
                    error_message,
                    reply_markup=back_to_main_keyboard()
                )
            else:
                # Для других ValidationError показываем общее сообщение
                logger.error(f"Validation error checking booking limit: {e}", exc_info=True)
                await callback_query.message.answer(
                    "Произошла ошибка при проверке возможности бронирования. Пожалуйста, попробуйте позже.",
                    reply_markup=back_to_main_keyboard()
                )
            await state.clear()
        except Exception as e:
            from ..keyboards import back_to_main_keyboard
            logger.error(f"Error starting booking: {e}", exc_info=True)
            await callback_query.message.answer(
                "Произошла ошибка при начале бронирования. Пожалуйста, попробуйте позже или обратитесь к администратору.",
                reply_markup=back_to_main_keyboard()
            )
            await state.clear()


@router.callback_query(lambda c: c.data and c.data.startswith("select_bathhouse:"))
async def select_bathhouse(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    if callback_query.message and callback_query.data:
        # Удаляем предыдущие сообщения с клавиатурами
        await _cleanup_previous_messages(callback_query, state)
        
        # Разделяем только по первому двоеточию
        parts = callback_query.data.split(":", 1)
        if len(parts) < 2:
            await callback_query.message.answer("Ошибка: некорректный формат данных.")
            return
        bathhouse_id = int(parts[1])
        
        # Сохраняем выбранную баню в состоянии
        await state.update_data(bathhouse_id=bathhouse_id)
        await state.set_state(BookingStates.waiting_for_date)
        await _update_activity_timestamp(state)
        
        keyboard = await date_selection_keyboard()
        date_msg = await callback_query.message.answer("Выберите дату:", reply_markup=keyboard)
        # Сохраняем ID сообщения с выбором даты
        await state.update_data(date_selection_message_id=date_msg.message_id)


@router.callback_query(BookingStates.waiting_for_date, SimpleCalendarCallback.filter())
async def process_calendar_date(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора даты из календаря бронирования"""
    if not callback_query.message or not callback_query.data:
        return
    
    try:
        # Используем стандартный обработчик календаря
        calendar = SimpleCalendar(cancel_btn='Отмена', today_btn='Сегодня')
        # Распаковываем callback данные
        data = SimpleCalendarCallback.unpack(callback_query.data)
        selected, selected_date = await calendar.process_selection(callback_query, data)
        
        if not selected:
            # Пользователь переключил месяц, календарь уже обновился
            return
        
        logger.info(f"Selected date for booking: {selected_date}")
        
        # Сохраняем дату в состоянии
        await state.update_data(selected_date=selected_date)
        await state.set_state(BookingStates.waiting_for_slot)
        await _update_activity_timestamp(state)
        
        # Получаем bathhouse_id из состояния
        data = await state.get_data()
        bathhouse_id = data.get("bathhouse_id")
        if not bathhouse_id:
            from ..keyboards import back_to_main_keyboard
            await callback_query.message.answer(
                "Ошибка: баня не выбрана. Начните заново.",
                reply_markup=back_to_main_keyboard()
            )
            await state.clear()
            return
        
        # Получаем доступные слоты
        try:
            bathhouse = await sync_to_async(Bathhouse.objects.get)(id=bathhouse_id)
            available_slots = await sync_to_async(services.get_available_slots)(bathhouse, selected_date)
            
            logger.info(f"Available slots for bathhouse {bathhouse_id} on {selected_date}: {len(available_slots)} slots")
            
            if available_slots:
                from ..keyboards import slots_keyboard
                keyboard = slots_keyboard(available_slots)
                slots_msg = await callback_query.message.answer("Выберите доступное время:", reply_markup=keyboard)
                # Сохраняем ID сообщения с выбором времени
                await state.update_data(slots_selection_message_id=slots_msg.message_id)
            else:
                await callback_query.message.answer("К сожалению, на эту дату нет доступных слотов. Выберите другую дату.")
                # Возвращаем к выбору даты
                await state.set_state(BookingStates.waiting_for_date)
                from ..keyboards import date_selection_keyboard
                keyboard = await date_selection_keyboard()
                date_msg = await callback_query.message.answer("Выберите другую дату:", reply_markup=keyboard)
                await state.update_data(date_selection_message_id=date_msg.message_id)
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            await callback_query.message.answer(f"Ошибка при получении доступных слотов: {str(e)}")
            await state.clear()
            
    except Exception as e:
        logger.error(f"Error processing calendar date: {e}", exc_info=True)
        await callback_query.message.answer("Произошла ошибка при обработке даты. Пожалуйста, попробуйте позже.")
        await state.clear()


@router.callback_query(lambda c: c.data and c.data.startswith("select_date:"))
async def select_date(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    if callback_query.message and callback_query.data:
        # Удаляем предыдущие сообщения с клавиатурами
        await _cleanup_previous_messages(callback_query, state)
        
        # Разделяем только по первому двоеточию
        parts = callback_query.data.split(":", 1)
        if len(parts) < 2:
            await callback_query.message.answer("Ошибка: некорректный формат даты.")
            return
        date_str = parts[1]
        
        # Определяем выбранную дату
        today = timezone.now().date()
        if date_str == "today":
            selected_date = today
        elif date_str == "tomorrow":
            selected_date = today + timedelta(days=1)
        elif date_str == "day_after_tomorrow":
            selected_date = today + timedelta(days=2)
        else:
            await callback_query.message.answer("Неверная дата. Попробуйте еще раз.")
            return
        
        # Сохраняем дату в состоянии
        await state.update_data(selected_date=selected_date)
        await state.set_state(BookingStates.waiting_for_slot)
        await _update_activity_timestamp(state)
        
        # Получаем bathhouse_id из состояния
        data = await state.get_data()
        bathhouse_id = data.get("bathhouse_id")
        if not bathhouse_id:
            from ..keyboards import back_to_main_keyboard
            await callback_query.message.answer(
                "Ошибка: баня не выбрана. Начните заново.",
                reply_markup=back_to_main_keyboard()
            )
            await state.clear()
            return
        
        # Получаем доступные слоты
        try:
            bathhouse = await sync_to_async(Bathhouse.objects.get)(id=bathhouse_id)
            available_slots = await sync_to_async(services.get_available_slots)(bathhouse, selected_date)
            
            logger.info(f"Available slots for bathhouse {bathhouse_id} on {selected_date}: {len(available_slots)} slots")
            
            if available_slots:
                keyboard = slots_keyboard(available_slots)
                slots_msg = await callback_query.message.answer("Выберите доступное время:", reply_markup=keyboard)
                # Сохраняем ID сообщения с выбором времени
                await state.update_data(slots_selection_message_id=slots_msg.message_id)
            else:
                await callback_query.message.answer("К сожалению, на эту дату нет доступных слотов. Выберите другую дату.")
                # Возвращаем к выбору даты
                await state.set_state(BookingStates.waiting_for_date)
                keyboard = await date_selection_keyboard()
                date_msg = await callback_query.message.answer("Выберите другую дату:", reply_markup=keyboard)
                await state.update_data(date_selection_message_id=date_msg.message_id)
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            await callback_query.message.answer(f"Ошибка при получении доступных слотов: {str(e)}")
            await state.clear()


@router.callback_query(lambda c: c.data and c.data.startswith("select_slot:"))
async def select_slot(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    if callback_query.message and callback_query.data:
        # Удаляем предыдущие сообщения с клавиатурами
        await _cleanup_previous_messages(callback_query, state)
        
        logger.info(f"select_slot callback_data: {callback_query.data}")
        
        try:
            # Правильно разбираем callback_data: select_slot:HH:MM-HH:MM
            # Нужно разделить только по первому двоеточию
            parts = callback_query.data.split(":", 1)
            if len(parts) < 2:
                logger.error(f"Invalid callback_data format: {callback_query.data}")
                await callback_query.message.answer("Ошибка: некорректный формат времени. Попробуйте еще раз.")
                return
                
            slot_str = parts[1]  # Получаем "HH:MM-HH:MM"
            logger.info(f"slot_str: {slot_str}")
            
            # Проверяем, что строка содержит дефис
            if "-" not in slot_str:
                logger.error(f"Slot string doesn't contain '-': {slot_str}")
                await callback_query.message.answer("Ошибка: некорректный формат времени. Попробуйте еще раз.")
                return
                
            # Разделяем по дефису
            time_parts = slot_str.split("-")
            if len(time_parts) != 2:
                logger.error(f"Invalid time format, expected HH:MM-HH:MM, got: {slot_str}")
                await callback_query.message.answer("Ошибка: некорректный формат времени. Попробуйте еще раз.")
                return
                
            start_str, end_str = time_parts
            logger.info(f"Parsed: start_str={start_str}, end_str={end_str}")
            
            # Проверяем, что строки времени не пустые
            if not start_str or not end_str:
                logger.error(f"Empty time strings: start='{start_str}', end='{end_str}'")
                await callback_query.message.answer("Ошибка: некорректный формат времени. Попробуйте еще раз.")
                return
                
        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing slot data: {e}, callback_data={callback_query.data}")
            await callback_query.message.answer("Ошибка: некорректный формат времени. Попробуйте еще раз.")
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        bathhouse_id = data.get("bathhouse_id")
        selected_date = data.get("selected_date")
        
        if not bathhouse_id or not selected_date:
            from ..keyboards import back_to_main_keyboard
            await callback_query.message.answer(
                "Ошибка: отсутствуют необходимые данные. Начните заново.",
                reply_markup=back_to_main_keyboard()
            )
            await state.clear()
            return
        
        # Создаем datetime объекты в UTC
        # Предполагаем, что выбранное время - в часовом поясе бани (GMT+7)
        import pytz
        bathhouse_tz = pytz.timezone('Asia/Jakarta')  # GMT+7
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        
        # Создаем datetime в часовом поясе бани, затем конвертируем в UTC
        start_datetime_local = bathhouse_tz.localize(datetime.combine(selected_date, start_time))
        end_datetime_local = bathhouse_tz.localize(datetime.combine(selected_date, end_time))
        
        # Конвертируем в UTC для хранения в базе данных
        start_datetime = start_datetime_local.astimezone(pytz.UTC)
        end_datetime = end_datetime_local.astimezone(pytz.UTC)
        
        # Сохраняем слот в состоянии
        await state.update_data(
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )
        await _update_activity_timestamp(state)
        
        # Получаем или создаем клиента
        try:
            client, created = await sync_to_async(Client.objects.get_or_create)(
                telegram_id=str(callback_query.from_user.id),
                defaults={
                    'name': callback_query.from_user.full_name or callback_query.from_user.first_name or "Unknown",
                    'phone': "",
                    'telegram_id': str(callback_query.from_user.id)
                }
            )
            
            # Проверяем, есть ли у клиента номер телефона
            if client.phone and client.phone.strip():
                # Телефон есть, создаем бронирование сразу
                await state.set_state(BookingStates.waiting_for_payment)
                bathhouse = await sync_to_async(Bathhouse.objects.get)(id=bathhouse_id)
                booking = await sync_to_async(services.create_booking_request)(
                    client=client,
                    bathhouse=bathhouse,
                    start=start_datetime,
                    end=end_datetime
                )
                
                # Сохраняем ID бронирования в состоянии
                await state.update_data(booking_id=booking.id)
                
                # Показываем инструкцию по оплате из конфига (асинхронно)
                from bathhouse_booking.bookings.config_init import get_config
                payment_text = await sync_to_async(get_config)("PAYMENT_INSTRUCTION", 
                                         "Пожалуйста, переведите оплату на карту •1234 5678 9012 3456• и нажмите 'Я оплатил'")
                
                # Форматируем сумму оплаты
                amount = booking.price_total or 0
                if amount <= 0:
                    logger.warning(f"Booking {booking.id} has invalid price: {booking.price_total}")
                    amount = 1000  # fallback цена
                
                amount_text = f"Сумма к оплате: {amount} руб.\n\n"
                
                keyboard = payment_confirmation_keyboard()
                msg = await callback_query.message.answer(
                    f"Бронирование создано! ID: {booking.id}\n{amount_text}{payment_text}",
                    reply_markup=keyboard
                )
                # Сохраняем ID сообщения для возможного удаления при отмене
                await state.update_data(booking_created_message_id=msg.message_id)
            else:
                # Телефона нет, переходим к вводу телефона
                await state.set_state(BookingStates.waiting_for_phone)
                from ..keyboards import skip_phone_keyboard
                await callback_query.message.answer(
                    "📱 *У вас не указан номер телефона*\n\n"
                    "Хотите добавить его для связи? Отправьте номер телефона в формате:\n"
                    "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
                    "Или нажмите 'Пропустить' чтобы продолжить без телефона.",
                    reply_markup=skip_phone_keyboard(),
                    parse_mode="Markdown"
                )
            
        except ValidationError as e:
            from ..keyboards import back_to_main_keyboard
            # Обрабатываем ошибку лимита бронирований
            error_message = str(e)
            if "У вас уже есть" in error_message and "активных бронирований" in error_message:
                # Показываем пользователю понятное сообщение об ошибке лимита
                await callback_query.message.answer(
                    error_message,
                    reply_markup=back_to_main_keyboard()
                )
            elif "прошлом" in error_message:
                # Ошибка бронирования в прошлое
                await callback_query.message.answer(
                    "Нельзя забронировать баню в прошлом. Пожалуйста, выберите будущую дату и время.",
                    reply_markup=back_to_main_keyboard()
                )
            else:
                # Для других ValidationError показываем общее сообщение
                logger.error(f"Validation error creating booking: {e}", exc_info=True)
                await callback_query.message.answer(
                    "Произошла ошибка при создании бронирования. Пожалуйста, проверьте данные и попробуйте еще раз.",
                    reply_markup=back_to_main_keyboard()
                )
            await state.clear()
        except Exception as e:
            from ..keyboards import back_to_main_keyboard
            logger.error(f"Error creating booking: {e}", exc_info=True)
            await callback_query.message.answer(
                "Произошла ошибка при создании бронирования. Пожалуйста, попробуйте позже или обратитесь к администратору.",
                reply_markup=back_to_main_keyboard()
            )
            await state.clear()


@router.callback_query(lambda c: c.data == "payment_reported")
async def report_payment(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    if callback_query.message and not isinstance(callback_query.message, types.InaccessibleMessage):
        chat_id = callback_query.message.chat.id
        
        # Удаляем сообщение с кнопкой "Я оплатил", чтобы пользователь не мог нажать снова
        try:
            await callback_query.message.delete()
        except Exception as e:
            logger.debug(f"Could not delete payment message: {e}")
        
        # Удаляем предыдущие сообщения с клавиатурами
        await _cleanup_previous_messages(callback_query, state)
        
        data = await state.get_data()
        booking_id = data.get("booking_id")
        
        if not booking_id:
            from ..keyboards import main_menu_keyboard
            await callback_query.bot.send_message(
                chat_id=chat_id,
                text="Ошибка: ID бронирования не найден. Начните заново.",
                reply_markup=main_menu_keyboard()
            )
            await state.clear()
            return
        
        try:
            await sync_to_async(services.report_payment)(booking_id)
            
            from ..keyboards import main_menu_keyboard
            await callback_query.bot.send_message(
                chat_id=chat_id,
                text="✅ Оплата принята! Ожидайте подтверждения от администратора.",
                reply_markup=main_menu_keyboard()
            )
            await state.clear()
        except Exception as e:
            logger.error(f"Error processing payment: {e}", exc_info=True)
            from ..keyboards import main_menu_keyboard
            await callback_query.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Ошибка при обработке оплаты: {str(e)}",
                reply_markup=main_menu_keyboard()
            )
            await state.clear()


@router.callback_query(lambda c: c.data == "cancel_booking")
async def cancel_booking(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    if callback_query.message and not isinstance(callback_query.message, types.InaccessibleMessage):
        chat_id = callback_query.message.chat.id
        
        # Удаляем сообщение с кнопкой отмены, чтобы пользователь не мог нажать снова
        try:
            await callback_query.message.delete()
        except Exception as e:
            logger.debug(f"Could not delete cancel message: {e}")
        
        # Удаляем предыдущие сообщения с клавиатурами
        await _cleanup_previous_messages(callback_query, state)
        
        data = await state.get_data()
        booking_id = data.get("booking_id")
        
        from ..keyboards import main_menu_keyboard
        
        if booking_id:
            try:
                await sync_to_async(services.cancel_booking)(booking_id)
                await callback_query.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Бронирование отменено.",
                    reply_markup=main_menu_keyboard()
                )
            except Exception as e:
                await callback_query.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Ошибка при отмене бронирования: {str(e)}",
                    reply_markup=main_menu_keyboard()
                )
        else:
            await callback_query.bot.send_message(
                chat_id=chat_id,
                text="✅ Бронирование отменено.",
                reply_markup=main_menu_keyboard()
            )
        
        await state.clear()


# Обработчики кнопок "назад"
@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """Вернуться в главное меню"""
    await callback_query.answer()
    if callback_query.message:
        # Проверяем, есть ли активное бронирование в состоянии ожидания оплаты
        current_state = await state.get_state()
        data = await state.get_data()
        
        # Если пользователь в состоянии ожидания оплаты и есть booking_id, отменяем бронирование
        if current_state == BookingStates.waiting_for_payment and 'booking_id' in data:
            try:
                booking_id = data['booking_id']
                await sync_to_async(services.cancel_booking)(booking_id)
                logger.info(f"Auto-cancelled booking {booking_id} when user clicked 'назад'")
            except Exception as e:
                logger.error(f"Failed to auto-cancel booking: {e}")

            # Удаляем сообщение с созданным бронированием
            if 'booking_created_message_id' in data:
                try:
                    await callback_query.bot.delete_message(
                        chat_id=callback_query.message.chat.id,
                        message_id=data['booking_created_message_id']
                    )
                except Exception as e:
                    logger.debug(f"Could not delete booking created message: {e}")

        await _cleanup_previous_messages(callback_query, state)
        await state.clear()
        
        from ..keyboards import main_menu_keyboard
        await callback_query.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard()
        )


@router.callback_query(lambda c: c.data == "back_to_bathhouse_selection")
async def back_to_bathhouse_selection(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """Вернуться к выбору бани"""
    await callback_query.answer()
    if callback_query.message:
        # Проверяем, есть ли активное бронирование в состоянии ожидания оплаты
        current_state = await state.get_state()
        data = await state.get_data()
        
        # Если пользователь в состоянии ожидания оплаты и есть booking_id, отменяем бронирование
        if current_state == BookingStates.waiting_for_payment and 'booking_id' in data:
            try:
                booking_id = data['booking_id']
                await sync_to_async(services.cancel_booking)(booking_id)
                logger.info(f"Auto-cancelled booking {booking_id} when user clicked 'назад' to bathhouse selection")
            except Exception as e:
                logger.error(f"Failed to auto-cancel booking: {e}")

            # Удаляем сообщение с созданным бронированием
            if 'booking_created_message_id' in data:
                try:
                    await callback_query.bot.delete_message(
                        chat_id=callback_query.message.chat.id,
                        message_id=data['booking_created_message_id']
                    )
                except Exception as e:
                    logger.debug(f"Could not delete booking created message: {e}")

        await _cleanup_previous_messages(callback_query, state)
        
        # Возвращаемся к состоянию выбора бани
        await state.set_state(BookingStates.waiting_for_bathhouse)
        await _update_activity_timestamp(state)
        
        # Получаем список активных бань
        bathhouses = await sync_to_async(lambda: list(Bathhouse.objects.filter(is_active=True)))()
        if bathhouses:
            from ..keyboards import bathhouses_keyboard
            keyboard = bathhouses_keyboard(bathhouses)
            selection_msg = await callback_query.message.answer("Выберите баню:", reply_markup=keyboard)
            await state.update_data(bathhouse_selection_message_id=selection_msg.message_id)
        else:
            await callback_query.message.answer("К сожалению, сейчас нет доступных бань для бронирования.")
            await state.clear()


@router.callback_query(lambda c: c.data == "back_to_date_selection")
async def back_to_date_selection(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """Вернуться к выбору даты"""
    await callback_query.answer()
    if callback_query.message:
        # Проверяем, есть ли активное бронирование в состоянии ожидания оплаты
        current_state = await state.get_state()
        data = await state.get_data()
        
        # Если пользователь в состоянии ожидания оплаты и есть booking_id, отменяем бронирование
        if current_state == BookingStates.waiting_for_payment and 'booking_id' in data:
            try:
                booking_id = data['booking_id']
                await sync_to_async(services.cancel_booking)(booking_id)
                logger.info(f"Auto-cancelled booking {booking_id} when user clicked 'назад' to date selection")
            except Exception as e:
                logger.error(f"Failed to auto-cancel booking: {e}")

            # Удаляем сообщение с созданным бронированием
            if 'booking_created_message_id' in data:
                try:
                    await callback_query.bot.delete_message(
                        chat_id=callback_query.message.chat.id,
                        message_id=data['booking_created_message_id']
                    )
                except Exception as e:
                    logger.debug(f"Could not delete booking created message: {e}")

        await _cleanup_previous_messages(callback_query, state)
        
        # Возвращаемся к состоянию выбора даты
        await state.set_state(BookingStates.waiting_for_date)
        await _update_activity_timestamp(state)
        
        from ..keyboards import date_selection_keyboard
        keyboard = await date_selection_keyboard()
        date_msg = await callback_query.message.answer("Выберите дату:", reply_markup=keyboard)
        await state.update_data(date_selection_message_id=date_msg.message_id)


@router.callback_query(lambda c: c.data == "back_to_slots_selection")
async def back_to_slots_selection(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """Вернуться к выбору времени"""
    await callback_query.answer()
    if callback_query.message:
        # Проверяем, есть ли активное бронирование в состоянии ожидания оплаты
        current_state = await state.get_state()
        data = await state.get_data()
        
        # Если пользователь в состоянии ожидания оплаты и есть booking_id, отменяем бронирование
        if current_state == BookingStates.waiting_for_payment and 'booking_id' in data:
            try:
                booking_id = data['booking_id']
                await sync_to_async(services.cancel_booking)(booking_id)
                logger.info(f"Auto-cancelled booking {booking_id} when user clicked 'назад' to slots selection")
            except Exception as e:
                logger.error(f"Failed to auto-cancel booking: {e}")

            # Удаляем сообщение с созданным бронированием
            if 'booking_created_message_id' in data:
                try:
                    await callback_query.bot.delete_message(
                        chat_id=callback_query.message.chat.id,
                        message_id=data['booking_created_message_id']
                    )
                except Exception as e:
                    logger.debug(f"Could not delete booking created message: {e}")

        await _cleanup_previous_messages(callback_query, state)
        
        # Возвращаемся к состоянию выбора времени
        await state.set_state(BookingStates.waiting_for_slot)
        await _update_activity_timestamp(state)
        
        # Получаем данные из состояния
        data = await state.get_data()
        bathhouse_id = data.get("bathhouse_id")
        selected_date = data.get("selected_date")
        
        if not bathhouse_id or not selected_date:
            from ..keyboards import back_to_main_keyboard
            await callback_query.message.answer(
                "Ошибка: отсутствуют необходимые данные. Начните заново.",
                reply_markup=back_to_main_keyboard()
            )
            await state.clear()
            return
        
        try:
            # Получаем доступные слоты
            bathhouse = await sync_to_async(Bathhouse.objects.get)(id=bathhouse_id)
            available_slots = await sync_to_async(services.get_available_slots)(bathhouse, selected_date)
            
            if available_slots:
                from ..keyboards import slots_keyboard
                keyboard = slots_keyboard(available_slots)
                slots_msg = await callback_query.message.answer("Выберите доступное время:", reply_markup=keyboard)
                await state.update_data(slots_selection_message_id=slots_msg.message_id)
            else:
                await callback_query.message.answer("К сожалению, на эту дату нет доступных слотов. Выберите другую дату.")
                # Возвращаем к выбору даты
                await state.set_state(BookingStates.waiting_for_date)
                from ..keyboards import date_selection_keyboard
                keyboard = await date_selection_keyboard()
                date_msg = await callback_query.message.answer("Выберите другую дату:", reply_markup=keyboard)
                await state.update_data(date_selection_message_id=date_msg.message_id)
                
        except Exception as e:
            logger.error(f"Error getting available slots on back: {e}")
            await callback_query.message.answer(f"Ошибка при получении доступных слотов: {str(e)}")
            await state.clear()


@router.callback_query(lambda c: c.data == "view_schedule")
async def view_schedule(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """Показать календарь для выбора даты просмотра расписания"""
    await callback_query.answer()
    if callback_query.message:
        await _cleanup_previous_messages(callback_query, state)
        await _update_activity_timestamp(state)
        
        try:
            # Получаем список активных бань
            bathhouses = await sync_to_async(lambda: list(Bathhouse.objects.filter(is_active=True)))()
            
            if not bathhouses:
                await callback_query.message.answer("К сожалению, сейчас нет доступных бань.")
                return
            
            # Сохраняем список бань в состоянии
            bathhouse_ids = [bh.id for bh in bathhouses]
            await state.update_data(schedule_bathhouse_ids=bathhouse_ids)
            
            # Устанавливаем состояние ожидания выбора даты для расписания
            await state.set_state(BookingStates.waiting_for_schedule_date)
            
            # Показываем календарь для выбора даты
            from ..calendar_utils import get_calendar_keyboard
            keyboard = await get_calendar_keyboard(back_callback="back_to_main")
            await callback_query.message.answer(
                "Выберите дату для просмотра расписания:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error showing schedule calendar: {e}", exc_info=True)
            await callback_query.message.answer("Произошла ошибка при получении расписания. Пожалуйста, попробуйте позже.")


@router.callback_query(BookingStates.waiting_for_schedule_date, SimpleCalendarCallback.filter())
async def process_schedule_calendar_date(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора даты в календаре расписания"""
    await callback_query.answer()
    if callback_query.message and callback_query.data:
        await _cleanup_previous_messages(callback_query, state)
        await _update_activity_timestamp(state)
        
        try:
            # Используем стандартный обработчик календаря
            calendar = SimpleCalendar(cancel_btn='Отмена', today_btn='Сегодня')
            # Распаковываем callback данные
            data = SimpleCalendarCallback.unpack(callback_query.data)
            selected, selected_date = await calendar.process_selection(callback_query, data)
            
            if not selected:
                # Пользователь переключил месяц, календарь уже обновился
                return
            
            logger.info(f"Selected date for schedule: {selected_date}")
            
            # Получаем список ID бань из состояния
            data = await state.get_data()
            bathhouse_ids = data.get("schedule_bathhouse_ids", [])
            
            if not bathhouse_ids:
                await callback_query.message.answer("Ошибка: список бань не найден. Начните заново.")
                await state.clear()
                return
            
            # Получаем бани по ID
            bathhouses = []
            for bh_id in bathhouse_ids:
                try:
                    bathhouse = await sync_to_async(Bathhouse.objects.get)(id=bh_id)
                    bathhouses.append(bathhouse)
                except Bathhouse.DoesNotExist:
                    logger.warning(f"Bathhouse with id {bh_id} not found")
            
            if not bathhouses:
                await callback_query.message.answer("К сожалению, сейчас нет доступных бань.")
                await state.clear()
                return
            
            # Собираем информацию о расписании на выбранную дату
            schedule_text = f"📅 *Расписание свободных окон на {selected_date.strftime('%d.%m.%Y')}*\n\n"
            
            for bathhouse in bathhouses:
                schedule_text += f"*{bathhouse.name}:*\n"
                
                try:
                    # Получаем свободные интервалы
                    free_intervals = await sync_to_async(services.get_free_intervals)(bathhouse, selected_date)
                    
                    # Объединяем смежные интервалы (с допуском 30 минут)
                    merged_intervals = await sync_to_async(services.merge_adjacent_intervals)(free_intervals, gap_minutes=30)
                    
                    # Форматируем свободные интервалы
                    formatted_intervals = await sync_to_async(services.format_free_intervals)(merged_intervals)
                    
                    if formatted_intervals:
                        schedule_text += f"  Свободно: {formatted_intervals}\n"
                    else:
                        schedule_text += f"  Нет свободного времени\n"
                        
                except Exception as e:
                    logger.error(f"Error getting free intervals for {bathhouse.name} on {selected_date}: {e}")
                    schedule_text += f"  Ошибка получения данных\n"
                
                schedule_text += "\n"
            
            # Отправляем расписание пользователю с кнопкой возврата на главную
            from ..keyboards import back_to_main_keyboard
            await callback_query.message.answer(
                schedule_text, 
                parse_mode="Markdown",
                reply_markup=back_to_main_keyboard()
            )
            
            # Очищаем состояние
            await state.clear()
            
        except ValueError as e:
            logger.error(f"Error parsing date from callback: {callback_query.data}, error: {e}")
            await callback_query.message.answer("Ошибка: некорректный формат даты. Попробуйте еще раз.")
        except Exception as e:
            logger.error(f"Error processing schedule date: {e}", exc_info=True)
            await callback_query.message.answer("Произошла ошибка при получении расписания. Пожалуйста, попробуйте позже.")
            await state.clear()