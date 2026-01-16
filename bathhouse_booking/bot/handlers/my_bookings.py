from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from bathhouse_booking.bookings.models import Client, Booking
from bathhouse_booking.bookings.services import cancel_booking
from datetime import datetime
import pytz

router = Router()

BATHHOUSE_TIMEZONE = pytz.timezone('Asia/Jakarta')

async def get_user_bookings(telegram_id: str):
    """Получить активные бронирования пользователя"""
    try:
        # Находим клиента по telegram_id
        client = await sync_to_async(Client.objects.get)(telegram_id=telegram_id)
        
        # Получаем активные бронирования с prefetch_related для bathhouse
        bookings = await sync_to_async(list)(
            Booking.objects.filter(
                client=client,
                status__in=['pending', 'payment_reported', 'approved']
            ).select_related('bathhouse').order_by('start_datetime')
        )
        
        return bookings
    except Client.DoesNotExist:
        return []
    except Exception as e:
        print(f"Error getting user bookings: {e}")
        return []

def format_booking_for_display(booking):
    """Форматировать бронирование для отображения"""
    local_start = booking.start_datetime.astimezone(BATHHOUSE_TIMEZONE)
    local_end = booking.end_datetime.astimezone(BATHHOUSE_TIMEZONE)
    
    status_map = {
        'pending': '⏳ Ожидает оплаты',
        'payment_reported': '💰 Оплата сообщена',
        'approved': '✅ Подтверждено',
        'rejected': '❌ Отклонено',
        'cancelled': '🗑️ Отменено'
    }
    
    status_text = status_map.get(booking.status, booking.status)
    
    return (
        f"📅 Бронирование #{booking.id}\n"
        f"Баня: {booking.bathhouse.name}\n"
        f"Дата: {local_start.strftime('%d.%m.%Y')}\n"
        f"Время: {local_start.strftime('%H:%M')} - {local_end.strftime('%H:%M')}\n"
        f"Статус: {status_text}\n"
        f"Создано: {booking.created_at.strftime('%d.%m.%Y %H:%M')}"
    )

def create_bookings_keyboard(bookings):
    """Создать клавиатуру с бронированиями"""
    builder = InlineKeyboardBuilder()
    
    for booking in bookings:
        local_start = booking.start_datetime.astimezone(BATHHOUSE_TIMEZONE)
        # Используем booking.bathhouse_id для получения имени бани
        # Имя будет доступно через select_related
        bathhouse_name = booking.bathhouse.name if hasattr(booking.bathhouse, 'name') else f"Баня #{booking.bathhouse_id}"
        builder.add(types.InlineKeyboardButton(
            text=f"{local_start.strftime('%d.%m %H:%M')} - {bathhouse_name}",
            callback_data=f"view_booking:{booking.id}"
        ))
    
    builder.add(types.InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def create_booking_detail_keyboard(booking_id, can_cancel=True):
    """Создать клавиатуру для детального просмотра бронирования"""
    builder = InlineKeyboardBuilder()
    
    if can_cancel:
        builder.add(types.InlineKeyboardButton(
            text="❌ Отменить бронирование",
            callback_data=f"cancel_booking:{booking_id}"
        ))
    
    builder.add(types.InlineKeyboardButton(
        text="⬅️ Назад к списку",
        callback_data="back_to_my_bookings"
    ))
    
    builder.add(types.InlineKeyboardButton(
        text="🏠 На главную",
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

@router.callback_query(lambda c: c.data == "my_bookings")
async def show_my_bookings(callback: types.CallbackQuery, state: FSMContext):
    """Показать активные бронирования пользователя"""
    await state.clear()
    
    bookings = await get_user_bookings(str(callback.from_user.id))
    
    if not bookings:
        await callback.message.edit_text(
            "📭 У вас нет активных бронирований.\n\n"
            "Вы можете забронировать баню, нажав кнопку 'Забронировать баню'.",
            reply_markup=create_bookings_keyboard([])
        )
        return
    
    await callback.message.edit_text(
        f"📋 Ваши активные бронирования ({len(bookings)}):\n\n"
        "Выберите бронирование для просмотра деталей или отмены:",
        reply_markup=create_bookings_keyboard(bookings)
    )

@router.callback_query(lambda c: c.data.startswith("view_booking:"))
async def view_booking_detail(callback: types.CallbackQuery, state: FSMContext):
    """Показать детали бронирования"""
    booking_id = int(callback.data.split(":")[1])
    
    try:
        # Используем select_related для получения связанных объектов
        booking = await sync_to_async(Booking.objects.select_related('bathhouse', 'client').get)(id=booking_id)
        
        # Проверяем, принадлежит ли бронирование текущему пользователю
        client = await sync_to_async(Client.objects.get)(telegram_id=str(callback.from_user.id))
        if booking.client.id != client.id:
            await callback.answer("❌ Это не ваше бронирование!")
            return
        
        # Проверяем, можно ли отменить бронирование
        can_cancel = booking.status in ['pending', 'payment_reported', 'approved']
        
        await callback.message.edit_text(
            format_booking_for_display(booking),
            reply_markup=create_booking_detail_keyboard(booking_id, can_cancel)
        )
        
    except Booking.DoesNotExist:
        await callback.answer("❌ Бронирование не найдено!")
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(lambda c: c.data.startswith("cancel_booking:"))
async def cancel_user_booking(callback: types.CallbackQuery, state: FSMContext):
    """Отменить бронирование пользователем"""
    booking_id = int(callback.data.split(":")[1])
    
    try:
        # Проверяем, принадлежит ли бронирование текущему пользователю
        client = await sync_to_async(Client.objects.get)(telegram_id=str(callback.from_user.id))
        booking = await sync_to_async(Booking.objects.select_related('client').get)(id=booking_id)
        
        if booking.client.id != client.id:
            await callback.answer("❌ Это не ваше бронирование!")
            return
        
        # Отменяем бронирование
        await sync_to_async(cancel_booking)(booking_id)
        
        await callback.message.edit_text(
            "✅ Бронирование успешно отменено!\n\n"
            "Вы можете забронировать другую дату или посмотреть текущие бронирования.",
            reply_markup=create_bookings_keyboard([])
        )
        
    except Booking.DoesNotExist:
        await callback.answer("❌ Бронирование не найдено!")
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Не удалось отменить бронирование: {str(e)}\n\n"
            "Пожалуйста, попробуйте позже или свяжитесь с администратором.",
            reply_markup=create_bookings_keyboard([])
        )

@router.callback_query(lambda c: c.data == "back_to_my_bookings")
async def back_to_my_bookings(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к списку бронирований"""
    await show_my_bookings(callback, state)