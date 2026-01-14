from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..keyboards import main_menu_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    # Очищаем любое предыдущее состояние
    await state.clear()
    
    await message.answer(
        "Добро пожаловать в систему бронирования бани!\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard()
    )