from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from src.bot.i18n import i18n
from src.models.product import Product
from src.models.order import Order, OrderStatus
from typing import Optional


class ProductKeyboards:
    """Keyboards for product browsing"""

    @staticmethod
    def catalog_pagination(
        page: int,
        total_pages: int,
        language: str = "en"
    ) -> InlineKeyboardMarkup:
        """Create pagination keyboard for catalog"""
        buttons = []

        if page > 1:
            buttons.append(
                InlineKeyboardButton(
                    text=i18n("previous", language),
                    callback_data=f"catalog_page:{page-1}"
                )
            )

        buttons.append(
            InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="catalog_info"
            )
        )

        if page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    text=i18n("next", language),
                    callback_data=f"catalog_page:{page+1}"
                )
            )

        return InlineKeyboardMarkup(inline_keyboard=[buttons])

    @staticmethod
    def product_detail(
        product_id: int,
        language: str = "en"
    ) -> InlineKeyboardMarkup:
        """Keyboard for product detail view"""
        buttons = [
            [
                InlineKeyboardButton(
                    text=i18n("add_to_cart", language),
                    callback_data=f"add_to_cart:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n("back", language),
                    callback_data="catalog_back"
                )
            ],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def select_quantity(product_id: int, language: str = "en") -> InlineKeyboardMarkup:
        """Keyboard for selecting quantity"""
        buttons = []
        for qty in [1, 2, 3, 5, 10]:
            buttons.append(
                InlineKeyboardButton(
                    text=str(qty),
                    callback_data=f"qty_select:{product_id}:{qty}"
                )
            )

        buttons = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
        buttons.append([
            InlineKeyboardButton(
                text=i18n("back", language),
                callback_data="catalog_back"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=buttons)


class CartKeyboards:
    """Keyboards for cart operations"""

    @staticmethod
    def cart_menu(is_empty: bool, language: str = "en") -> InlineKeyboardMarkup:
        """Menu for cart view"""
        buttons = []

        if not is_empty:
            buttons.append([
                InlineKeyboardButton(
                    text=i18n("checkout", language),
                    callback_data="checkout"
                )
            ])
            buttons.append([
                InlineKeyboardButton(
                    text=i18n("clear_cart", language),
                    callback_data="clear_cart_confirm"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                text=i18n("catalog", language),
                callback_data="catalog_view"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def cart_item_actions(
        product_id: int,
        quantity: int,
        language: str = "en"
    ) -> InlineKeyboardMarkup:
        """Actions for cart item"""
        buttons = []

        if quantity > 1:
            buttons.append(
                InlineKeyboardButton(
                    text="➖",
                    callback_data=f"cart_decrease:{product_id}"
                )
            )

        buttons.append(
            InlineKeyboardButton(
                text=f"qty: {quantity}",
                callback_data="cart_qty_info"
            )
        )

        buttons.append(
            InlineKeyboardButton(
                text="➕",
                callback_data=f"cart_increase:{product_id}"
            )
        )

        buttons.append(
            InlineKeyboardButton(
                text=i18n("remove_item", language),
                callback_data=f"cart_remove:{product_id}"
            )
        )

        return InlineKeyboardMarkup(inline_keyboard=[buttons])

    @staticmethod
    def confirm_clear_cart(language: str = "en") -> InlineKeyboardMarkup:
        """Confirmation for clearing cart"""
        buttons = [
            [
                InlineKeyboardButton(
                    text="✅ Yes",
                    callback_data="clear_cart_yes"
                ),
                InlineKeyboardButton(
                    text="❌ No",
                    callback_data="clear_cart_no"
                ),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)


class OrderKeyboards:
    """Keyboards for order operations"""

    @staticmethod
    def orders_list(page: int, total_pages: int, language: str = "en") -> InlineKeyboardMarkup:
        """Pagination for orders list"""
        buttons = []

        if page > 1:
            buttons.append(
                InlineKeyboardButton(
                    text=i18n("previous", language),
                    callback_data=f"orders_page:{page-1}"
                )
            )

        buttons.append(
            InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="orders_info"
            )
        )

        if page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    text=i18n("next", language),
                    callback_data=f"orders_page:{page+1}"
                )
            )

        return InlineKeyboardMarkup(inline_keyboard=[buttons])

    @staticmethod
    def order_detail(order_id: int, language: str = "en") -> InlineKeyboardMarkup:
        """Detail view for order"""
        buttons = [
            [
                InlineKeyboardButton(
                    text=i18n("back", language),
                    callback_data="orders_back"
                )
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)


class AdminKeyboards:
    """Keyboards for admin operations"""

    @staticmethod
    def admin_menu(language: str = "en") -> InlineKeyboardMarkup:
        """Main admin menu"""
        buttons = [
            [
                InlineKeyboardButton(
                    text=i18n("add_product", language),
                    callback_data="admin_add_product"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n("manage_products", language),
                    callback_data="admin_products"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n("view_orders", language),
                    callback_data="admin_orders"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n("statistics", language),
                    callback_data="admin_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n("back", language),
                    callback_data="main_menu"
                )
            ],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def orders_status_selector(order_id: int, language: str = "en") -> InlineKeyboardMarkup:
        """Select order status"""
        buttons = []
        for status in [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            buttons.append([
                InlineKeyboardButton(
                    text=i18n(f"status_{status.value}", language),
                    callback_data=f"order_status:{order_id}:{status.value}"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                text=i18n("back", language),
                callback_data="admin_orders"
            )
        ])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def admin_orders_pagination(
        page: int,
        total_pages: int,
        language: str = "en"
    ) -> InlineKeyboardMarkup:
        """Pagination for admin orders"""
        buttons = []

        if page > 1:
            buttons.append(
                InlineKeyboardButton(
                    text=i18n("previous", language),
                    callback_data=f"admin_orders_page:{page-1}"
                )
            )

        buttons.append(
            InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="admin_orders_info"
            )
        )

        if page < total_pages:
            buttons.append(
                InlineKeyboardButton(
                    text=i18n("next", language),
                    callback_data=f"admin_orders_page:{page+1}"
                )
            )

        return InlineKeyboardMarkup(inline_keyboard=buttons)


class MainKeyboards:
    """Main menu keyboards"""

    @staticmethod
    def main_menu(is_admin: bool = False, language: str = "en") -> ReplyKeyboardMarkup:
        """Main menu keyboard"""
        buttons = [
            [KeyboardButton(text=i18n("catalog", language))],
            [KeyboardButton(text=i18n("cart", language)), KeyboardButton(text=i18n("my_orders", language))],
            [KeyboardButton(text=i18n("language", language))],
        ]

        if is_admin:
            buttons.append([KeyboardButton(text=i18n("admin_panel", language))])

        return ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=False,
            selective=False
        )

    @staticmethod
    def language_selector() -> InlineKeyboardMarkup:
        """Language selection keyboard"""
        buttons = [
            [
                InlineKeyboardButton(
                    text="🇬🇧 English",
                    callback_data="language:en"
                ),
                InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data="language:ru"
                ),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def back_to_menu(language: str = "en") -> InlineKeyboardMarkup:
        """Back to menu button"""
        buttons = [
            [
                InlineKeyboardButton(
                    text=i18n("back", language),
                    callback_data="main_menu"
                )
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
