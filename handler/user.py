from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from database.users import User
from product import data
from states.user import CustomerState
from utils.keyboard import reply_buttons, call_with_admin

dp = Dispatcher()


@dp.message(F.text == "Orqaga 🔙", CustomerState.get_category)
@dp.message(F.text == "Orqaga 🔙")
@dp.message(Command("start"))
async def command_start_handler(message: Message):
    buttons = ['Sotuvlarni analis qilish 📊', 'Coin sotib olish 🪙', 'Admin bilan boglanish 👮', ]

    user = await User.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer(
            "Salom 😉 men uzumni analez qiladigan botman 📊. Bot orqali siz xoxlagan cotegoriyadagi"
            " maxsulotlarni umumiy sotuvi va haftalik sotivini korishingiz mumkun. Sizda 100 coin bor 🪙",
            reply_markup=reply_buttons(buttons))
    else:
        await message.answer("Tanlang", reply_markup=reply_buttons(buttons))


@dp.message(F.contact)
async def command_contact(message: Message):
    if message.contact.user_id == message.from_user.id:
        await User.create(
            name=message.from_user.username or message.from_user.first_name,
            telegram_id=message.from_user.id,
            phone=message.contact.phone_number
        )
        await message.answer(
            "Registratsiyadan otingiz 😊",)

    else:
        await message.answer('Faqat ozingizni raqamingizni kriting 🚫')


@dp.message(F.text == 'Admin bilan boglanish 👮')
async def command_admin(message: Message):
    await message.answer('Admin 👮', reply_markup=call_with_admin())


@dp.message(F.text == 'Coin sotib olish 🪙')
async def command_coin(message: Message):
    await message.answer('Coin narxlari\n'
                         '45 coin 25.000 UZB Som\n'
                         '55 coin 32.000 UZB Som\n'
                         '65 coin 45.000 UZB Som\n'
                         '120 coin 85.000 UZB Som\n'
                         'adminga murojat qiling tashlang')

    await message.answer('Admin 👮', reply_markup=call_with_admin())
