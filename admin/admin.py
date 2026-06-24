from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from core.core import settings
from database.token import Token
from database.users import User
from handler.user import dp
from states.user import AdminState
from utils.keyboard import reply_buttons


@dp.message(F.text == "admin")
async def admin_command_handler(message: Message, state: FSMContext):
    if message.from_user.id != settings.ADMIN_TELEGRAM_ID:
        return
    buttons = ['JWT yangilash', 'Userlarni korish', "Coin berish"]

    await message.answer('Tanglang aka', reply_markup=reply_buttons(buttons))
    await state.set_state(AdminState.register_admin)


@dp.message(AdminState.register_admin, F.text == 'Userlarni korish')
async def admin_command_handler(message: Message, state: FSMContext):
    users = await User.get_all()
    all_users = ''
    for user in users:
        all_users += f'Name:  {user.name}   Phone:  {user.phone} Coin:  {user.coin}\n\n'
    await message.answer(f'{all_users}')

    buttons = ['JWT yangilash', 'Userlarni korish', "Coin berish"]
    await message.answer("Tanglang aka", reply_markup=reply_buttons(buttons))


@dp.message(AdminState.register_admin, F.text == 'Coin berish')
async def admin_command_handler(message: Message, state: FSMContext):
    await message.answer('Telephon raqamini kriting raqam')
    await state.set_state(AdminState.get_phone)


@dp.message(AdminState.get_phone)
async def admin_command_handler(message: Message, state: FSMContext):
    await message.answer('coin miqdorini kroting')
    await state.update_data(phone=message.text)
    await state.set_state(AdminState.give_coin)


@dp.message(AdminState.get_phone)
async def admin_command_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    phone = data['phone']
    user = await User.get_by_phone(phone)

    if user is None:
        await message.answer('User yoq')
        return

    await User.give_coin(phone, int(message.text))


@dp.message(F.text == "JWT yangilash")
async def admin_command_handler(message: Message, state: FSMContext):
    await message.answer("JWT ni kriting")
    await state.set_state(AdminState.update_jwt)


@dp.message(AdminState.update_jwt)
async def admin_command_handler(message: Message, state: FSMContext):
    await Token.update_token(message.text)
    await message.answer("JWT yangilandi")
    buttons = ['JWT yangilash', 'Userlarni korish', "Coin berish"]
    await state.clear()

    await message.answer("Tanglang aka", reply_markup=reply_buttons(buttons))
