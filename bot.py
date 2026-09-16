import asyncio
import html
import logging
import os
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("sb24gz_live")
router = Router()

# Telegram-native content. No external URLs are used anywhere in the user flow.
LIVE_CONTENT = {
    "live": "🔴 <b>Live Now</b>\n\nSB24GZ is ready for live updates. New content will appear here when published.",
    "latest": "📣 <b>Latest Updates</b>\n\nNo new update is published yet. Check back here for the latest SB24GZ content.",
}


class LiveState(StatesGroup):
    waiting_for_update_text = State()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔴 Live Now", callback_data="live_now"),
                InlineKeyboardButton(text="📣 Latest Updates", callback_data="latest_updates"),
            ],
            [InlineKeyboardButton(text="📝 Submit Update", callback_data="submit_update")],
            [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")],
        ]
    )


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="↩️ Main Menu", callback_data="main_menu")]]
    )


def retry_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Try Again", callback_data="submit_update")],
            [InlineKeyboardButton(text="↩️ Main Menu", callback_data="main_menu")],
        ]
    )


WELCOME = (
    "<b>SB24GZ – ផ្សាយផ្ទាល់</b>\n\n"
    "Live updates and recent content, directly inside Telegram.\n\n"
    "🔴 <b>Live Now</b> — view the current live update.\n"
    "📣 <b>Latest Updates</b> — read the latest published update.\n"
    "📝 <b>Submit Update</b> — send text to the bot.\n\n"
    "Choose an option below."
)

HELP_TEXT = (
    "<b>SB24GZ – ផ្សាយផ្ទាល់</b>\n\n"
    "This bot provides live updates and recent content directly inside Telegram.\n\n"
    "🔴 Live Now — view the current live content.\n"
    "📣 Latest Updates — view the latest available content.\n"
    "📝 Submit Update — send a text update to the bot.\n\n"
    "No external website is required. Use /start to return to the main menu."
)


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_menu())


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu())


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(WELCOME, reply_markup=main_menu())


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(HELP_TEXT, reply_markup=back_menu())


@router.callback_query(F.data == "live_now")
async def live_now_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(LIVE_CONTENT["live"], reply_markup=back_menu())


@router.callback_query(F.data == "latest_updates")
async def latest_updates_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(LIVE_CONTENT["latest"], reply_markup=back_menu())


@router.callback_query(F.data == "submit_update")
async def submit_update_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(LiveState.waiting_for_update_text)
    if callback.message:
        await callback.message.edit_text(
            "<b>📝 Submit Update</b>\n\n"
            "Send the text you want to submit.\n\n"
            "Your submission stays inside Telegram. You can cancel with /start.",
            reply_markup=back_menu(),
        )


@router.message(LiveState.waiting_for_update_text, F.text)
async def receive_update_text(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()

    if not text:
        await message.answer("Please send some text.", reply_markup=retry_menu())
        return

    if len(text) > 3000:
        await message.answer(
            "That update is too long. Please keep it under 3,000 characters.",
            reply_markup=retry_menu(),
        )
        return

    # Echo the submitted text safely inside Telegram. No external destination.
    safe_text = html.escape(text)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    await state.clear()
    await message.answer(
        "<b>✅ Update received</b>\n\n"
        "Your text was received successfully inside Telegram.\n\n"
        f"<blockquote>{safe_text}</blockquote>\n"
        f"<i>Received: {timestamp}</i>",
        reply_markup=main_menu(),
    )


@router.message(LiveState.waiting_for_update_text)
async def reject_non_text_update(message: Message) -> None:
    await message.answer(
        "Please send a text message for the update.",
        reply_markup=retry_menu(),
    )


async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Starting SB24GZ live bot")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("SB24GZ live bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
