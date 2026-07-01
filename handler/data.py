from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.types import ReplyKeyboardRemove

from database.token import Token
from database.users import User
from handler.user import dp
from product import data
from servise.data import UzumScraper
from states.user import CustomerState
from utils.keyboard import phone_number, reply_buttons
from utils.utils import format_weekly_top, format_total_top


@dp.message(CustomerState.get_category, F.text == "Orqaga 🔙")
@dp.message(F.text == 'Sotuvlarni tahlil qilish 📊')
async def command_get_category(message: Message, state: FSMContext):
    user = await User.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Ro‘yxatdan o‘tish uchun telefon raqamingizni yuboring ☎️",
                             reply_markup=phone_number())
    else:
        await message.answer(
            "Qaysi kategoriya bo‘yicha tahlil qilmoqchisiz? 📊", reply_markup=reply_buttons(data.keys())
        )
        await state.set_state(CustomerState.get_category)


@dp.message(F.text == 'Orqaga 🔙', CustomerState.get_child_category_products)
@dp.message(F.text, CustomerState.get_category)
async def command_get_child_category(message: Message, state: FSMContext):
    if not message.text in data:
        await message.answer('Togri narsa yuboring!!')
        return
    await state.update_data(category=message.text)

    await message.answer("Qaysi kategoriya bo‘yicha tahlil qilmoqchisiz? 📊",
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
    await message.answer(
        '📊 Analitika tayyorlanmoqda. Iltimos, biroz kuting.\n🔍 Minglab mahsulotlar tahlil qilinmoqda...',
        reply_markup=ReplyKeyboardRemove())

    if message.text not in ['Haftalik', 'Umumiy']:
        await message.answer('Togri narsa yuboring!!')
        return
    buttons = ['Sotuvlarni tahlil qilish 📊', 'Coin sotib olish 🪙', 'Admin bilan boglanish 👮', ]

    user = await User.check_coin(message.from_user.id)
    state_date = await state.get_data()
    category = state_date.get('category')
    is_active = state_date.get('is_active')
    category_product = state_date.get('category_product')
    category_id = data[category][category_product]
    token = await Token.get_token()

    if not is_active is None:
        await message.answer('🚀 Jarayon boshlandi. Natijalar tayyorlanmoqda, iltimos kuting. 🫰🏻')
        return

    if message.text == 'Haftalik':
        if user.coin < 30:
            await message.answer(
                f"Sizda coin etarli emas. Balansingiz: {user.coin} 💰\n"
                f"Haftalik ko'rish narxi: 35 coin"
            )
            return

        scraper = UzumScraper(category_id=category_id, token=token.token)
        if scraper.has_auth_error:
            await message.answer("Xatolik boldi boshqattan urinib koring", reply_markup=reply_buttons(buttons))

            await state.clear()
            return
        await state.update_data(is_active=True)
        top = await scraper.get_weekly_trends(25)
        text = format_weekly_top(top, category_product)

        await message.answer(f"{text}")
        await User.update_coin(message.from_user.id, 35)

        await message.answer(f"Sizda {user.coin} coin qoldi", reply_markup=reply_buttons(buttons))
        await state.clear()
        return




    elif message.text == 'Umumiy':
        if user.coin < 35:
            await message.answer(
                f'''❌ Sizda coin yetarli emas.\n

                💰 Balansingiz: {user.coin} coin\n
                🪙 Tahlil narxi: 40 coin\n
        
                Davom etish uchun coin balansingizni to‘ldiring.'''
            )
            return
        await state.update_data(is_active=True)
        scraper = UzumScraper(category_id=category_id, token=token.token)
        top = await scraper.get_total_leaders(25)
        text = format_total_top(top, category_product)
        if scraper.has_auth_error:
            await message.answer("Xatolik boldi boshqattan urinib koring", reply_markup=reply_buttons(buttons))

            await state.clear()
            return
        await message.answer(f"{text}")

    await User.update_coin(message.from_user.id, 40)

    await state.clear()
    await message.answer(f"Sizda {user.coin} qoldi", reply_markup=reply_buttons(buttons))
