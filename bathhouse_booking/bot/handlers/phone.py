from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from bathhouse_booking.bookings.models import Client, Bathhouse
from bathhouse_booking.bookings import services
from bathhouse_booking.bookings.config_init import get_config
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
import logging

from ..states import BookingStates

logger = logging.getLogger(__name__)

router = Router()

def validate_phone_number(phone: str) -> bool:
    """Проверить валидность номера телефона"""
    if not phone:
        return False
    
    # Убираем все нецифровые символы
    digits = re.sub(r'\D', '', phone)
    
    # Проверяем российские форматы
    if len(digits) == 11:
        # Форматы: 7XXXXXXXXXX или 8XXXXXXXXXX
        if digits.startswith('7') or digits.startswith('8'):
            return True
    
    return False

def format_phone_number(phone: str) -> str:
    """Отформатировать номер телефона"""
    if not phone:
        return ""
    
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 11:
        if digits.startswith('7'):
            return f"+7{digits[1:4]} {digits[4:7]}-{digits[7:9]}-{digits[9:]}"
        elif digits.startswith('8'):
            return f"8{digits[1:4]} {digits[4:7]}-{digits[7:9]}-{digits[9:]}"
    
    return phone

@router.callback_query(lambda c: c.data == "skip_phone")
async def skip_phone(callback: types.CallbackQuery, state: FSMContext):
    """Пропустить ввод номера телефона"""
    await create_booking_with_phone(callback, state, phone="")

@router.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_phone_input(message: types.Message, state: FSMContext):
    """Обработать ввод номера телефона"""
    current_state = await state.get_state()
    if current_state != BookingStates.waiting_for_phone.state:
        return
    
    phone = message.text.strip()
    
    # Проверяем валидность номера
    if phone and not validate_phone_number(phone):
        await message.answer(
            "❌ Неверный формат номера телефона.\n\n"
            "Пожалуйста, введите номер в формате:\n"
            "+7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
            "Или нажмите 'Пропустить' в предыдущем сообщении."
        )
        return
    
    # Форматируем номер
    formatted_phone = format_phone_number(phone) if phone else ""
    
    # Создаем callback для имитации callback_query
    class MockCallback:
        def __init__(self, message):
            self.message = message
            self.from_user = message.from_user
    
    mock_callback = MockCallback(message)
    await create_booking_with_phone(mock_callback, state, phone=formatted_phone)

async def create_booking_with_phone(callback, state: FSMContext, phone: str):
    """Создать бронирование с указанным номером телефона"""
    from ..keyboards import payment_confirmation_keyboard, back_to_main_keyboard
    
    # Получаем данные из состояния
    data = await state.get_data()
    start_datetime = data.get('start_datetime')
    end_datetime = data.get('end_datetime')
    bathhouse_id = data.get('bathhouse_id')
    
    if not all([start_datetime, end_datetime, bathhouse_id]):
        await callback.message.answer(
            "❌ Ошибка: отсутствуют необходимые данные. Пожалуйста, начните бронирование заново.",
            reply_markup=back_to_main_keyboard()
        )
        await state.clear()
        return
    
    # Проверяем, что время начала не в прошлом
    if start_datetime < timezone.now():
        await callback.message.answer(
            "Нельзя забронировать баню в прошлом. Пожалуйста, выберите будущую дату и время.",
            reply_markup=back_to_main_keyboard()
        )
        await state.clear()
        return
    
    try:
        # Получаем или создаем клиента
        client, created = await sync_to_async(Client.objects.get_or_create)(
            telegram_id=str(callback.from_user.id),
            defaults={
                'name': callback.from_user.full_name or callback.from_user.first_name or "Unknown",
                'phone': phone,
                'telegram_id': str(callback.from_user.id)
            }
        )
        
        # Если клиент уже существует, обновляем номер телефона если он был указан
        if not created and phone:
            client.phone = phone
            await sync_to_async(client.save)()
        
        bathhouse = await sync_to_async(Bathhouse.objects.get)(id=bathhouse_id)
        booking = await sync_to_async(services.create_booking_request)(
            client=client,
            bathhouse=bathhouse,
            start=start_datetime,
            end=end_datetime
        )
        
        # Сохраняем ID бронирования в состоянии
        await state.update_data(booking_id=booking.id)
        await state.set_state(BookingStates.waiting_for_payment)
        
        # Показываем инструкцию по оплате из конфига
        payment_text = await sync_to_async(get_config)(
            "PAYMENT_INSTRUCTION", 
            "Пожалуйста, переведите оплату на карту •1234 5678 9012 3456• и нажмите 'Я оплатил'"
        )
        
        keyboard = payment_confirmation_keyboard()
        
        # Форматируем время для отображения
        from datetime import datetime
        import pytz
        
        bathhouse_tz = pytz.timezone('Asia/Jakarta')
        start_local = start_datetime.astimezone(bathhouse_tz)
        end_local = end_datetime.astimezone(bathhouse_tz)
        
        booking_info = (
            f"✅ Бронирование создано!\n\n"
            f"📅 Дата: {start_local.strftime('%d.%m.%Y')}\n"
            f"⏰ Время: {start_local.strftime('%H:%M')} - {end_local.strftime('%H:%M')}\n"
            f"🏠 Баня: {bathhouse.name}\n"
            f"📱 Телефон: {phone if phone else 'не указан'}\n"
            f"🔢 ID бронирования: {booking.id}\n\n"
            f"{payment_text}"
        )
        
        # Отправляем новое сообщение с информацией о бронировании
        msg = await callback.message.answer(
            booking_info,
            reply_markup=keyboard
        )
        
        # Сохраняем ID сообщения для возможного удаления при отмене
        await state.update_data(booking_created_message_id=msg.message_id)
        
        # Пытаемся удалить предыдущее сообщение с запросом телефона (если есть)
        try:
            if hasattr(callback, 'message') and callback.message:
                await callback.message.delete()
        except Exception as e:
            logger.debug(f"Could not delete previous message: {e}")
        
    except ValidationError as e:
        error_message = str(e)
        if "У вас уже есть" in error_message and "активных бронирований" in error_message:
            await callback.message.answer(
                error_message,
                reply_markup=back_to_main_keyboard()
            )
        elif "прошлом" in error_message:
            await callback.message.answer(
                "Нельзя забронировать баню в прошлом. Пожалуйста, выберите будущую дату и время.",
                reply_markup=back_to_main_keyboard()
            )
        else:
            logger.error(f"Validation error creating booking: {e}", exc_info=True)
            await callback.message.answer(
                "Произошла ошибка при создании бронирования. Пожалуйста, проверьте данные и попробуйте еще раз.",
                reply_markup=back_to_main_keyboard()
            )
        await state.clear()
    except Exception as e:
        logger.error(f"Error creating booking: {e}", exc_info=True)
        await callback.message.answer(
            "Произошла ошибка при создании бронирования. Пожалуйста, попробуйте позже или обратитесь к администратору.",
            reply_markup=back_to_main_keyboard()
        )
        await state.clear()