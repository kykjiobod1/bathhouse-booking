from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Забронировать баню", callback_data="book_bathhouse"))
    builder.add(InlineKeyboardButton(text="Посмотреть расписание", callback_data="view_schedule"))
    builder.add(InlineKeyboardButton(text="Мои бронирования", callback_data="my_bookings"))
    builder.add(InlineKeyboardButton(text="Написать админу", callback_data="message_admin"))
    builder.adjust(1)
    return builder.as_markup()


def bathhouses_keyboard(bathhouses) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for bathhouse in bathhouses:
        builder.add(InlineKeyboardButton(
            text=bathhouse.name,
            callback_data=f"select_bathhouse:{bathhouse.id}"
        ))
    # Добавляем кнопку "назад" к главному меню
    builder.add(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_to_main"
    ))
    builder.adjust(1)
    return builder.as_markup()


async def date_selection_keyboard() -> InlineKeyboardMarkup:
    """Устаревшая функция, используйте календарь вместо этого"""
    from .calendar_utils import get_calendar_keyboard
    return await get_calendar_keyboard()


def slots_keyboard(slots) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        start_str = slot[0].strftime("%H:%M")
        end_str = slot[1].strftime("%H:%M")
        builder.add(InlineKeyboardButton(
            text=f"{start_str} - {end_str}",
            callback_data=f"select_slot:{start_str}-{end_str}"
        ))
    # Добавляем кнопку "назад" к выбору даты
    builder.add(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_to_date_selection"
    ))
    builder.adjust(1)
    return builder.as_markup()


def payment_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Я оплатил", callback_data="payment_reported"))
    builder.add(InlineKeyboardButton(text="Отменить", callback_data="cancel_booking"))
    # Добавляем кнопку "назад" к выбору времени (но не к отмене бронирования)
    builder.add(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back_to_slots_selection"
    ))
    builder.adjust(1)
    return builder.as_markup()


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата на главную"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="⬅️ Вернуться на главную",
        callback_data="back_to_main"
    ))
    return builder.as_markup()