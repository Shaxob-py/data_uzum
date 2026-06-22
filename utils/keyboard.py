from aiogram.types import KeyboardButton , InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def reply_buttons(button: list):
    rkb = ReplyKeyboardBuilder()
    for button in button:
        rkb.add(KeyboardButton(text=button))

    rkb.add(KeyboardButton(text="Orqaga 🔙"))

    rkb.adjust(3)
    return rkb.as_markup(resize_keyboard=True)


def phone_number():
    rkb = ReplyKeyboardBuilder()
    rkb.add(KeyboardButton(text='Telephone raqam yuborish ☎️', request_contact=True),
            KeyboardButton(text='Orqaga 🔙'))
    size = [1]
    rkb.adjust(*size)
    return rkb.as_markup(resize_keyboard=True)

def call_with_admin():
    ikb = InlineKeyboardBuilder()
    ikb.add(InlineKeyboardButton(text='admin 👮', url='https://t.me/shaxob_x'),
    )
    ikb.adjust(1)
    return ikb.as_markup()


def inline_keyboard(buttons: list):
    ikb = InlineKeyboardBuilder()
    for button in buttons:
        ikb.add(InlineKeyboardButton(text='admin 👮', url='https://t.me/shaxob_x'),
        )
    ikb.adjust(1)
    return ikb.as_markup()
