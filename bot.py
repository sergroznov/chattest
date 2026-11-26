"""
Бот-ретранслятор для Telegram.

Как работает:
1. Вы пишете боту в личку (это "пульт управления").
2. Выбираете, от чьего имени сообщение (кнопки "Клиент", "Мастер" и т.д.).
3. Бот пересылает текст в нужный чат с подписью: "Клиент: текст".

Время сообщения всегда настоящее - его ставит сам Telegram.
"""

import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])  # только этот человек может управлять ботом
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", OWNER_ID))  # куда доставлять
SENDERS = [s.strip() for s in os.getenv("SENDERS", "Клиент,Мастер").split(",") if s.strip()]

only_owner = filters.User(user_id=OWNER_ID)


def sender_keyboard(current: str | None) -> InlineKeyboardMarkup:
    """Кнопки выбора отправителя. Выбранный помечаем галочкой."""
    buttons = [
        InlineKeyboardButton(("✅ " if name == current else "") + name, callback_data=name)
        for name in SENDERS
    ]
    return InlineKeyboardMarkup([buttons])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current = context.user_data.get("sender", SENDERS[0])
    context.user_data["sender"] = current
    await update.message.reply_text(
        "Пульт управления.\n"
        "Выберите, от чьего имени писать, и просто отправляйте текст - "
        "я перешлю его в целевой чат с подписью.",
        reply_markup=sender_keyboard(current),
    )


async def choose_sender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["sender"] = query.data
    await query.edit_message_reply_markup(reply_markup=sender_keyboard(query.data))


async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sender = context.user_data.get("sender", SENDERS[0])
    text = update.message.text
    await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=f"{sender}: {text}")


def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start, filters=only_owner))
    app.add_handler(CallbackQueryHandler(choose_sender))
    app.add_handler(MessageHandler(only_owner & filters.TEXT & ~filters.COMMAND, relay))
    app.run_polling()


if __name__ == "__main__":
    main()
