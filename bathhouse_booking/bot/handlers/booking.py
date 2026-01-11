from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from ..states import BookingStates

router = Router()


@router.callback_query(lambda c: c.data == "book_bathhouse")
async def start_booking(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer()
    if callback_query.message:
        await callback_query.message.answer("Начинаем процесс бронирования...")
        await state.set_state(BookingStates.waiting_for_bathhouse)
        
        # TODO: Получить список бань из БД через services
        await callback_query.message.answer("Выберите баню (заглушка)")