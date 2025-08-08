from dotenv import load_dotenv, find_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

import os

# Explicitly load .env from the project root
env_path = find_dotenv()
print(f"Loading .env from: {env_path}")  # Debug: show where .env is loaded from
load_dotenv(env_path)

TOKEN = os.environ.get("BOT_TOKEN")
BOT_USERNAME = os.environ.get("BOT_USERNAME")

CHANNEL_USERNAME = f"@{os.environ.get("CHANNEL_USERNAME")}"
CHANNEL_LINK = f"https://t.me/{os.environ.get("CHANNEL_LINK")}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    if chat_member.status in ["member", "administrator", "creator"]:
        await update.message.reply_text("خوش آمدید.")
    else:
        keyboard = [
            [InlineKeyboardButton("عضویت در چنل", url=CHANNEL_LINK)],
            [InlineKeyboardButton("بررسی عضویت", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "برای ثبت آگهی در پولبیا، نیاز است که شما عضو چنل باشید.",
            reply_markup=reply_markup
        )

async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    if chat_member.status in ["member", "administrator", "creator"]:
        await query.answer()
        await query.edit_message_text("عضویت شما تایید شد! خوش آمدید.")
    else:
        await query.answer()
        keyboard = [
            [InlineKeyboardButton("عضویت در چنل", url=CHANNEL_LINK)],
            [InlineKeyboardButton("بررسی عضویت", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "هنوز عضو چنل نیستید. لطفا عضو شوید و دوباره بررسی کنید.",
            reply_markup=reply_markup
        )


if __name__ == '__main__':
    print("Starting the bot ...")

    if not TOKEN:
        print("Please Setup the Environment Variables First (Bot token missing).")
        exit()
    else:
        app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))

    print("Polling ...")

    app.run_polling(poll_interval=60)