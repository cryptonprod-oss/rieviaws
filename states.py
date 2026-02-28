from aiogram.fsm.state import State, StatesGroup


class ReviewFSM(StatesGroup):
    username = State()
    payment_date = State()
    review_text = State()
    rating = State()
    confirm = State()
