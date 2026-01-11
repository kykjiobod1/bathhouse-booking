from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Забронировать баню", callback_data="book_bathhouse"))
    return builder.as_markup()


def bathhouses_keyboard(bathhouses) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for bathhouse in bathhouses:
        builder.add(InlineKeyboardButton(
            text=bathhouse.name,
            callback_data=f"select_bathhouse:{bathhouse.id}"
        ))
    builder.adjust(1)
    return builder.as_markup()


def date_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Сегодня", callback_data="select_date:today"))
    builder.add(InlineKeyboardButton(text="Завтра", callback_data="select_date:tomorrow"))
    builder.add(InlineKeyboardButton(text="Послезавтра", callback_data="select_date:day_after_tomorrow"))
    builder.adjust(1)
    return builder.as_markup()


def slots_keyboard(slots) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        start_str = slot[0].strftime("%H:%M")
        end_str = slot[1].strftime("%H:%M")
        builder.add(InlineKeyboardButton(
            text=f"{start_str} - {end_str}",
            callback_data=f"select_slot:{start_str}-{end_str}"
        ))
    builder.adjust(1)
    return builder.as_markup()


def payment_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Я оплатил", callback_data="payment_reported"))
    builder.add(InlineKeyboardButton(text="Отменить", callback_data="cancel_booking"))
    builder.adjust(1)
    return builder.as_markup()