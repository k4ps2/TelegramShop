import structlog
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.bot.i18n import i18n
from src.bot.keyboards import MainKeyboards, AdminKeyboards
from src.services import UserService
from src.core.database import AsyncSessionLocal
from src.bot.config import settings

logger = structlog.get_logger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Start command handler"""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name or "User"

    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        user = await user_service.get_or_create_user(
            user_id=user_id,
            username=username,
            full_name=full_name,
            language="en"
        )
        language = user.language
        is_admin = user.is_admin

    await state.clear()
    text = i18n("welcome", language)
    await message.answer(
        text,
        reply_markup=MainKeyboards.main_menu(is_admin=is_admin, language=language)
    )
    logger.info("User started bot", user_id=user_id, username=username)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Help command"""
    await message.answer(
        "<b>Available Commands:</b>\n"
        "/start - Start the bot\n"
        "/help - Show this message\n"
        "/admin - Admin panel (admins only)\n\n"
        "Use the buttons below to navigate."
    )


@router.message(F.text.contains("🌍"))
async def select_language(message: Message) -> None:
    """Select language"""
    text = i18n("choose_language", "en")
    await message.answer(
        text,
        reply_markup=MainKeyboards.language_selector()
    )
    logger.info("User accessed language selection", user_id=message.from_user.id)


@router.callback_query(F.data.startswith("language:"))
async def set_language(callback: CallbackQuery, state: FSMContext) -> None:
    """Set user language"""
    user_id = callback.from_user.id
    language = callback.data.split(":")[1]

    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        await user_service.update_user_language(user_id, language)

    await state.clear()
    text = i18n("language_changed", language)
    await callback.message.answer(
        text,
        reply_markup=MainKeyboards.main_menu(is_admin=False, language=language)
    )
    await callback.answer()
    logger.info("User language changed", user_id=user_id, language=language)


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    """Admin panel command"""
    user_id = message.from_user.id
    if user_id not in settings.ADMIN_IDS:
        await message.answer("❌ " + i18n("error_access_denied", "en"))
        return

    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        user = await user_service.repository.get_by_id(user_id)
        language = user.language if user else "en"

    text = i18n("admin_menu", language)
    await message.answer(text, reply_markup=AdminKeyboards.admin_menu(language))
    await state.clear()


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery) -> None:
    """Back to main menu"""
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        user = await user_service.repository.get_by_id(user_id)
        language = user.language if user else "en"
        is_admin = user.is_admin if user else False

    text = i18n("menu", language)
    await callback.message.answer(
        text,
        reply_markup=MainKeyboards.main_menu(is_admin=is_admin, language=language)
    )
    await callback.answer()
