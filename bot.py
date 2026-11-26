"""
Бот-ретранслятор для Telegram.

Как работает:
1. Вы пишете боту в личку (это "пульт управления").
2. Бот пересылает ваш текст в целевой чат.
3. По желанию к тексту добавляется подпись ("Клиент: текст") - включается кнопкой.

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

TOGGLE_SIGN = "toggle_sign"  # служебное значение для кнопки "Подпись"


def panel(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    """Кнопки пульта: выбор отправителя + переключатель подписи."""
    current = context.user_data.get("sender", SENDERS[0])
    sign_on = context.user_data.get("sign", False)

    sender_row = [
        InlineKeyboardButton(("✅ " if name == current else "") + name, callback_data=name)
        for name in SENDERS
    ]
    sign_row = [
        InlineKeyboardButton(
            "Подпись: включена" if sign_on else "Подпись: выключена",
            callback_data=TOGGLE_SIGN,
        )
    ]
    return InlineKeyboardMarkup([sign_row, sender_row])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.setdefault("sender", SENDERS[0])
    context.user_data.setdefault("sign", False)
    await update.message.reply_text(
        "Пульт управления.\n"
        "Просто отправляйте текст - я перешлю его в целевой чат.\n"
        "Кнопкой можно включить подпись отправителя.",
        reply_markup=panel(context),
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        await query.answer()
        return
    await query.answer()

    if query.data == TOGGLE_SIGN:
        context.user_data["sign"] = not context.user_data.get("sign", False)
    else:
        context.user_data["sender"] = query.data

    await query.edit_message_reply_markup(reply_markup=panel(context))


async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if context.user_data.get("sign", False):
        sender = context.user_data.get("sender", SENDERS[0])
        text = f"{sender}: {text}"
    await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=text)


def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start, filters=only_owner))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(only_owner & filters.TEXT & ~filters.COMMAND, relay))
    app.run_polling()


if __name__ == "__main__":
    main()
