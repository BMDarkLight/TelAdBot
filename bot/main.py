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

# --- Environment Variable Loading ---
env_path = find_dotenv()
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

TOKEN = os.environ.get("BOT_TOKEN")
BOT_USERNAME = os.environ.get("BOT_USERNAME")
ADMIN_ID = os.environ.get("ADMIN_ID")
PAYMENT_CARD_NUMBER = os.environ.get("PAYMENT_CARD_NUMBER")

CHANNEL_USERNAME = f"@{os.environ.get('CHANNEL_USERNAME')}"
CHANNEL_LINK = f"https://t.me/{os.environ.get('CHANNEL_LINK')}"

# --- Define Conversation States ---
class ConversationState(Enum):
    AWAITING_RULES_AGREEMENT = 1
    AWAITING_AD_TYPE = 2
    AWAITING_AD_CONTENT = 3
    AWAITING_PAYMENT_RECEIPT = 4

# --- Helper Functions ---
async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the rules and an 'I Agree' button."""
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
    """Displays the ad pricing menu."""
    query = update.callback_query
    await query.answer()

    menu_text = """
لطفا نوع آگهی خود را انتخاب کنید:

- **آگهی عادی**: ۲۵۰,۰۰۰ تومان
    """
    keyboard = [
        [InlineKeyboardButton("آگهی عادی (100,000 تومان)", callback_data="ad_type_normal")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    return ConversationState.AWAITING_AD_TYPE

# --- Command and Conversation Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Starts the conversation. Checks for channel membership first.
    This function is the ENTRY POINT for our ConversationHandler.
    """
    user = update.effective_user
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user.id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            raise Exception("User not in channel")
            
        await update.message.reply_text(f"سلام {user.first_name}، خوش آمدید!")
        return await show_rules(update, context)

    except Exception:
        # If user is NOT a member, ask them to join.
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
    """
    Callback function to re-check membership and continue to rules if successful.
    """
    query = update.callback_query
    user_id = query.from_user.id

    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            # Membership confirmed, proceed to showing rules
            return await show_rules(update, context)
        else:
            await query.answer("هنوز عضو چنل نیستید. لطفا عضو شوید و دوباره تلاش کنید.", show_alert=True)
            return ConversationState.AWAITING_RULES_AGREEMENT # Stay in the same state
            
    except Exception as e:
        print(e)
        await query.answer("خطایی در بررسی عضویت رخ داد. لطفا لحظاتی دیگر تلاش کنید.", show_alert=True)
        return ConversationState.AWAITING_RULES_AGREEMENT

async def ad_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user selecting an ad type from the menu."""
    query = update.callback_query
    await query.answer()

    # Store the chosen ad type in user_data for later use.
    context.user_data['ad_type'] = query.data
    
    ad_type_text = "عادی" if query.data == "ad_type_normal" else "ویژه"
    
    await query.edit_message_text(text=f"شما آگهی «{ad_type_text}» را انتخاب کردید.\n\n"
                                       "اکنون لطفا **متن و/یا تصویر آگهی** خود را ارسال کنید.")
                                       
    return ConversationState.AWAITING_AD_CONTENT

async def receive_ad_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives the ad content (text/photo) and asks for payment."""
    # Store the message ID and chat ID so we can forward it later.
    context.user_data['ad_message_id'] = update.message.message_id
    context.user_data['ad_chat_id'] = update.message.chat_id

    price = "100,000 تومان" if context.user_data['ad_type'] == 'ad_type_normal' else "250,000 تومان"
    
    payment_text = f"""
آگهی شما دریافت شد. ✅

مبلغ قابل پرداخت: **{price}**

لطفا هزینه را به شماره کارت زیر واریز کرده و سپس **تصویر رسید پرداخت** را ارسال نمایید.

💳 شماره کارت:
`{PAYMENT_CARD_NUMBER}`
    """
    await update.message.reply_text(text=payment_text, parse_mode='Markdown')
    return ConversationState.AWAITING_PAYMENT_RECEIPT

async def receive_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receives the payment receipt, forwards everything to the admin,
    and ends the conversation.
    """
    user = update.effective_user
    
    await update.message.reply_text(
        " رسید شما دریافت شد. آگهی شما جهت بررسی و انتشار برای ادمین ارسال گردید.\n"
        "از صبر و شکیبایی شما متشکریم. 🙏"
    )

    # --- Forward to Admin ---
    admin_caption = f"""
#آگهی_جدید

کاربر: {user.full_name} (@{user.username or 'N/A'})
ID: `{user.id}`
نوع آگهی: {context.user_data.get('ad_type', 'N/A')}

--- متن آگهی 👇 ---
    """
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_caption, parse_mode='Markdown')
    
    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=context.user_data['ad_chat_id'],
        message_id=context.user_data['ad_message_id']
    )
    
    await context.bot.send_message(chat_id=ADMIN_ID, text="--- رسید پرداخت 👇 ---")
    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id
    )
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "عملیات ثبت آگهی لغو شد. برای شروع مجدد /start را بزنید."
    )
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a message to the user."""
    print(f"Update {update} caused error {context.error}")

if __name__ == '__main__':
    print("Starting the bot ...")
    if not all([TOKEN, ADMIN_ID, PAYMENT_CARD_NUMBER]):
        print("Please set up all required Environment Variables (TOKEN, ADMIN_ID, PAYMENT_CARD_NUMBER).")
        exit()

    app = Application.builder().token(TOKEN).build()

    # --- Conversation Handler Setup ---
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
    
    app.add_error_handler(error_handler)
    
    print("Polling ...")
    app.run_polling()