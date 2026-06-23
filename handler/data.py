from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from core.core import settings
from database.token import Token
from database.users import User
from handler.user import dp
from product import data
from servise.data import UzumScraper
from states.user import CustomerState
from utils.keyboard import phone_number, reply_buttons
from utils.utils import format_weekly_top, format_total_top


@dp.message(CustomerState.get_category, F.text == "Orqaga 🔙")
@dp.message(F.text == 'Sotuvlarni analis qilish 📊')
async def command_get_category(message: Message, state: FSMContext):
    user = await User.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Registrat(siyadan otish uchun telephone raqamingizni yuboring ☎️",
                             reply_markup=phone_number())
    else:
        await message.answer(
            "qaysi categorialar boyicha analiz qilmoqchisiz", reply_markup=reply_buttons(data.keys())
        )
        await state.set_state(CustomerState.get_category)


@dp.message(F.text == 'Orqaga 🔙', CustomerState.get_child_category_products)
@dp.message(F.text, CustomerState.get_category)
async def command_get_child_category(message: Message, state: FSMContext):
    # print(data[message.text])
    if not message.text in data:
        await message.answer('Togri narsa yuboring!!')
        return
    await state.update_data(category=message.text)

    await message.answer("Aniqroq bolishi uchun yana tanglang 🎯",
                         reply_markup=reply_buttons(data[message.text].keys()))
    await state.set_state(CustomerState.get_child_category)


@dp.message(F.text, CustomerState.get_child_category)
async def command_get_child_category(message: Message, state: FSMContext):
    buttons = ['Haftalik', 'Umumiy']
    data_state = await state.get_data()
    category = data_state["category"]

    if not message.text in data[category]:
        await message.answer('Togri narsa yuboring!!')
        return

    await message.answer('Sotuvni qaysi mudatad analiz qilay 📊', reply_markup=reply_buttons(buttons))
    await state.set_state(CustomerState.get_child_category_products)
    await state.update_data(category_product=message.text)


@dp.message(F.text, CustomerState.get_child_category_products)
async def command_get_child_category_products(message: Message, state: FSMContext):
    await message.answer('Analitikani boshladim, ozgina kuting 📊', reply_markup=ReplyKeyboardRemove())

    if message.text not in ['Haftalik', 'Umumiy']:
        await message.answer('Togri narsa yuboring!!')
        return

    user = await User.check_coin(message.from_user.id)
    state_date = await state.get_data()
    category = state_date.get('category')
    is_active = state_date.get('is_active')
    category_product = state_date.get('category_product')
    category_id = data[category][category_product]
    token = await Token.get_token()
    await state.clear()

    if not is_active is None:
        await message.answer('Jarayon boshlangan iltimos kuting 🫰🏻')
        return

    if message.text == 'Haftalik':
        if user.coin < 30:
            await message.answer(
                f"Sizda coin etarli emas. Balansingiz: {user.coin} 💰\n"
                f"Haftalik ko'rish narxi: 35 coin"
            )
            return

        scraper = UzumScraper(category_id=category_id, token=token.token)
        if scraper.has_auth_error or scraper.has_server_error:
            await message.answer("Xatolik adminga murojat qiling")
            return
        await state.update_data(is_active=True)
        top = await scraper.get_weekly_trends(15)
        text = format_weekly_top(top, category_product)

        await message.answer(f"{text}")
        await User.update_coin(message.from_user.id, 35)
        buttons = ['Sotuvlarni analis qilish 📊', 'Coin sotib olish 🪙', 'Admin bilan boglanish 👮', ]

        await message.answer(f"Sizda {user.coin} qoldi", reply_markup=reply_buttons(buttons))
        return




    elif message.text == 'Umumiy':
        if user.coin < 35:
            await message.answer(
                f"Sizda coin etarli emas. Balansingiz: {user.coin} 💰\n"
                f"Umumiy ko'rish narxi: 40 coin"
            )
            return
        await state.update_data(is_active=True)
        scraper = UzumScraper(category_id=category_id, token=token.token)
        top = await scraper.get_total_leaders(15)
        text = format_total_top(top, category_product)
        if scraper.has_auth_error or scraper.has_server_error:
            await message.answer("Xatolik adminga murojat qiling")
            return
        await message.answer(f"{text}")

    await User.update_coin(message.from_user.id, 40)

    buttons = ['Sotuvlarni analis qilish 📊', 'Coin sotib olish 🪙', 'Admin bilan boglanish 👮', ]
    await message.answer(f"Sizda {user.coin} qoldi", reply_markup=reply_buttons(buttons))


@dp.message(F.text == 'Tozalash')
async def clear(message: Message, state: FSMContext):
    if message.from_user.id != settings.AUTH_USER_ID:
        return
    await state.clear()
    await message.answer("Tozalandi")
