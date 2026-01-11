from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    waiting_for_bathhouse = State()
    waiting_for_date = State()
    waiting_for_slot = State()
    waiting_for_payment = State()