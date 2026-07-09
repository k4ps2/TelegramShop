from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_cart_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="Очистить корзину", callback_data="clear_cart")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
