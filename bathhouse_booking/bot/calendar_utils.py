from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
import datetime

async def get_calendar_keyboard(show_back_button: bool = True, back_callback: str = "back_to_bathhouse_selection"):
    """Получить клавиатуру с календарем и кнопкой назад
    :param show_back_button: показывать кнопку назад
    :param back_callback: callback_data для кнопки назад
    """
    calendar = SimpleCalendar()
    calendar_markup = await calendar.start_calendar()
    
    if show_back_button:
        # Создаем новую клавиатуру с кнопкой назад
        from aiogram.types import InlineKeyboardMarkup
        
        # Получаем текущие кнопки календаря
        calendar_buttons = calendar_markup.inline_keyboard
        
        # Добавляем кнопку назад как новую строку
        new_buttons = calendar_buttons + [[
            InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)
        ]]
        
        return InlineKeyboardMarkup(inline_keyboard=new_buttons)
    
    return calendar_markup

async def process_calendar_selection(callback_query: CallbackQuery, state: FSMContext, 
                                     next_state: str, action: str = "select_date"):
    """Обработать выбор даты из календаря"""
    # Распаковываем callback данные
    data = SimpleCalendarCallback.unpack(callback_query.data)
    selected, date = await SimpleCalendar().process_selection(callback_query, data)
    
    if selected:
        # Сохраняем выбранную дату в состоянии
        await state.update_data(selected_date=date)
        
        # Переходим к следующему состоянию
        from .states import BookingStates
        
        if action == "select_date":
            await state.set_state(BookingStates.waiting_for_slot)
        elif action == "view_schedule":
            # Для просмотра расписания сразу показываем слоты
            await state.set_state(BookingStates.waiting_for_slot)
        
        return date
    
    return None

def format_date_for_display(date: datetime.date) -> str:
    """Отформатировать дату для отображения"""
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    
    return f"{date.day} {months[date.month - 1]} {date.year} года"

def is_date_in_past(date: datetime.date) -> bool:
    """Проверить, является ли дата прошедшей"""
    return date < datetime.date.today()

def is_date_too_far(date: datetime.date, max_days: int = 365) -> bool:
    """Проверить, не слишком ли далекая дата"""
    max_date = datetime.date.today() + datetime.timedelta(days=max_days)
    return date > max_date