from dotenv import load_dotenv, find_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

import os

env_path = find_dotenv()
print(f"Loading .env from: {env_path}")
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

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        message_type: str = update.message.chat.type
        text: str = update.message.text

        print(f"--- Message ---\nReceived message: {text}\nChat type: {message_type}\nUser: {update.message.chat.id}")

        response: str

        if message_type == "private":
            response = "پیام شما دریافت شد. در اسرع وقت پاسخ داده خواهد شد."

        print(f"Bot: {response}")
        await update.message.reply_text(response)
        
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="یک مشکلی پیش آمد. لطفا دوباره تلاش کنید.")

if __name__ == '__main__':
    print("Starting the bot ...")

    if not TOKEN:
        print("Please Setup the Environment Variables First (Bot token missing).")
        exit()
    else:
        app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))

    app.add_handler(MessageHandler(filters.TEXT, message_handler))

    app.add_error_handler(error_handler)

    print("Polling ...")

    app.run_polling(poll_interval=60)