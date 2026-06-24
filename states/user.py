from aiogram.fsm.state import StatesGroup, State


class CustomerState(StatesGroup):
    get_category = State()
    get_child_category = State()
    get_child_category_products = State()


class AdminState(StatesGroup):
    register_admin = State()
    get_phone = State()
    update_jwt = State()
    give_coin = State()


