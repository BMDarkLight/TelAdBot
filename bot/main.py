import os
from dotenv import load_dotenv, find_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)
from enum import Enum

env_path = find_dotenv()
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

TOKEN = os.environ.get("BOT_TOKEN")
BOT_USERNAME = os.environ.get("BOT_USERNAME")
ADMIN_ID = os.environ.get("ADMIN_ID")
PAYMENT_CARD_NUMBER = os.environ.get("PAYMENT_CARD_NUMBER")

CHANNEL_ID = f"@{os.environ.get('CHANNEL_USERNAME')}"
CHANNEL_LINK = f"https://t.me/{os.environ.get('CHANNEL_USERNAME')}"

class ConversationState(Enum):
    AWAITING_RULES_AGREEMENT = 1
    AWAITING_AD_TYPE = 2
    AWAITING_AD_CONTENT = 3
    AWAITING_PAYMENT_RECEIPT = 4

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules_text = """
قوانین ثبت آگهی:
۱- از ثبت آگهی‌های تکراری خودداری کنید.
۲- محتوای آگهی باید مطابق با قوانین کشور باشد.
۳- مسئولیت صحت اطلاعات آگهی بر عهده آگهی‌دهنده است.

لطفا پس از مطالعه، موافقت خود را اعلام کنید.
    """
    keyboard = [[InlineKeyboardButton("✅ مطالعه کردم و موافقم", callback_data="agree_rules")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=rules_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=rules_text, reply_markup=reply_markup)
        
    return ConversationState.AWAITING_RULES_AGREEMENT

async def show_ad_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    menu_text = """
لطفا نوع آگهی خود را انتخاب کنید:

- آگهی عادی: ۲۵۰,۰۰۰ تومان
    """
    keyboard = [
        [InlineKeyboardButton("آگهی عادی (250,000 تومان)", callback_data="ad_type_normal")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=menu_text, reply_markup=reply_markup)
    
    return ConversationState.AWAITING_AD_TYPE

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            raise Exception("User not in channel")
            
        await update.message.reply_text(f"سلام {user.first_name}، خوش آمدید!")
        return await show_rules(update, context)

    except Exception:
        keyboard = [
            [InlineKeyboardButton("عضویت در چنل", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ عضو شدم، بررسی کن", callback_data="check_membership_in_convo")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "برای ثبت آگهی، ابتدا باید در چنل ما عضو شوید.",
            reply_markup=reply_markup
        )
        return ConversationState.AWAITING_RULES_AGREEMENT

async def check_membership_in_convo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            return await show_rules(update, context)
        else:
            await query.answer("هنوز عضو چنل نیستید. لطفا عضو شوید و دوباره تلاش کنید.", show_alert=True)
            return ConversationState.AWAITING_RULES_AGREEMENT
            
    except Exception as e:
        print(e)
        await query.answer("خطایی در بررسی عضویت رخ داد. لطفا لحظاتی دیگر تلاش کنید.", show_alert=True)
        return ConversationState.AWAITING_RULES_AGREEMENT

async def ad_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data['ad_type'] = query.data
    
    ad_type_text = "عادی" if query.data == "ad_type_normal" else "ویژه"
    
    await query.edit_message_text(text=f"شما آگهی «{ad_type_text}» را انتخاب کردید.\n\n"
                                       "اکنون لطفا متن و/یا تصویر آگهی خود را ارسال کنید.")
                                       
    return ConversationState.AWAITING_AD_CONTENT

async def receive_ad_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    ad_id = message.message_id
    context.user_data['ad_id'] = ad_id

    user = update.effective_user
    user_id = user.id
    user_username = user.username

    if message.text:
        context.bot_data[ad_id] = {'type': 'text', 'content': message.text, 'user_id': user_id, 'user_username': user_username}
    elif message.photo:
        photo_file_id = message.photo[-1].file_id
        context.bot_data[ad_id] = {'type': 'photo', 'file_id': photo_file_id, 'content': message.caption, 'user_id': user_id, 'user_username': user_username}

    price = "250,000 تومان"
    
    payment_text = f"""
آگهی شما دریافت شد. ✅

مبلغ قابل پرداخت: {price}

لطفا هزینه را به شماره کارت زیر واریز کرده و سپس تصویر رسید پرداخت را ارسال نمایید.

💳 شماره کارت:
{PAYMENT_CARD_NUMBER}
    """
    
    await update.message.reply_text(text=payment_text)
    
    return ConversationState.AWAITING_PAYMENT_RECEIPT

async def receive_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ad_id = context.user_data.get('ad_id')

    if not ad_id:
        await update.message.reply_text("خطایی رخ داد. لطفا مجددا با /start تلاش کنید.")
        return ConversationHandler.END

    await update.message.reply_text(
        " رسید شما دریافت شد. آگهی شما جهت بررسی و انتشار برای ادمین ارسال گردید.\n"
        "از صبر و شکیبایی شما متشکریم. 🙏"
    )

    ad_type_raw = context.user_data.get('ad_type')
    ad_type_display = 'عادی' if ad_type_raw == 'ad_type_normal' else 'ویژه (پین شده)'
        
    admin_caption = f"""
#آگهی_جدید

کاربر: {user.full_name} (@{user.username or 'N/A'})
ID: {user.id}
نوع آگهی: {ad_type_display}
    """
    
    keyboard = [[InlineKeyboardButton("✅ تایید و پست تبلیغ", callback_data=f"accept_{ad_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_caption)

    ad_data = context.bot_data.get(ad_id, {})
    if ad_data.get('type') == 'text':
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"--- متن آگهی 👇 ---\n{ad_data.get('content')}")
    elif ad_data.get('type') == 'photo':
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=ad_data.get('file_id'), caption=f"--- متن آگهی 👇 ---\n{ad_data.get('content', '')}")

    await context.bot.send_message(chat_id=ADMIN_ID, text="--- رسید پرداخت 👇 ---")
    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text="لطفا آگهی را بررسی و در صورت تایید، آن را منتشر کنید.",
        reply_markup=reply_markup
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def approve_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        ad_id = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        await query.edit_message_text("خطا: ID آگهی نامعتبر است.")
        return

    ad_data = context.bot_data.get(ad_id)

    if not ad_data:
        await query.edit_message_text("❌ آگهی منقضی شده یا یافت نشد.")
        return

    user_id = ad_data.get('user_id')
    user_username = ad_data.get('user_username')
    
    if user_username:
        user_identifier = f"@{user_username}"
    else:
        user_identifier = f"{user_id}"

    signature = f"\n\n🆔 {user_identifier}\n———————————————————\n{CHANNEL_ID}"
    
    try:
        if ad_data.get('type') == 'text':
            new_text = ad_data.get('content', '') + signature
            await context.bot.send_message(chat_id=CHANNEL_ID, text=new_text)
        
        elif ad_data.get('type') == 'photo':
            original_caption = ad_data.get('content', '') or ''
            new_caption = original_caption + signature
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=ad_data.get('file_id'), caption=new_caption)
        
        if user_id:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="آگهی شما با موفقیت در چنل منتشر شد. ✅"
                )
            except Exception as e:
                print(f"Could not notify user {user_id}. They may have blocked the bot. Error: {e}")
        
        await query.edit_message_text("✅ آگهی با موفقیت در چنل منتشر شد و به کاربر اطلاع داده شد.")
        
        del context.bot_data[ad_id]

    except Exception as e:
        print(f"Error posting to channel: {e}")
        await query.edit_message_text(f"❌ خطا در انتشار آگهی: {e}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "عملیات ثبت آگهی لغو شد. برای شروع مجدد /start را بزنید."
    )
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log the error."""
    print(f"Update {update} caused error {context.error}")

if __name__ == '__main__':
    print("Starting the bot ...")
    if not all([TOKEN, ADMIN_ID, PAYMENT_CARD_NUMBER, os.environ.get('CHANNEL_USERNAME')]):
        print("Please set up all required Environment Variables.")
        exit()

    app = Application.builder().token(TOKEN).build()

    ad_submission_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            ConversationState.AWAITING_RULES_AGREEMENT: [
                CallbackQueryHandler(check_membership_in_convo, pattern='^check_membership_in_convo$'),
                CallbackQueryHandler(show_ad_menu, pattern='^agree_rules$'),
            ],
            ConversationState.AWAITING_AD_TYPE: [
                CallbackQueryHandler(ad_type_selected, pattern='^ad_type_')
            ],
            ConversationState.AWAITING_AD_CONTENT: [
                MessageHandler(filters.TEXT | filters.PHOTO, receive_ad_content)
            ],
            ConversationState.AWAITING_PAYMENT_RECEIPT: [
                MessageHandler(filters.PHOTO, receive_payment_receipt)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(ad_submission_handler)
    
    app.add_handler(CallbackQueryHandler(approve_ad, pattern=r'^accept_'))
    
    app.add_error_handler(error_handler)
    
    print("Polling ...")
    app.run_polling()