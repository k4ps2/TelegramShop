from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🛒 Каталог")],
        [KeyboardButton(text="🛍 Мои заказы"), KeyboardButton(text="👤 Профиль")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_catalog_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📱 Смартфоны")],
        [KeyboardButton(text="💻 Ноутбуки")],
        [KeyboardButton(text="🔙 Главное меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
