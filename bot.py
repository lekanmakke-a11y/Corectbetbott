import os
import logging
import sys
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError, BadRequest, NetworkError, TimedOut

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHANNEL_LINK = os.getenv('CHANNEL_LINK', 'https://t.me/+QvCFEopP3r9hY2Q0')

# Validate required environment variables
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found in environment variables")
    sys.exit(1)

if not CHANNEL_ID:
    logger.error("CHANNEL_ID not found in environment variables")
    sys.exit(1)

# Convert CHANNEL_ID to integer
try:
    CHANNEL_ID_INT = int(CHANNEL_ID)
except ValueError:
    logger.error(f"Invalid CHANNEL_ID format: {CHANNEL_ID}")
    sys.exit(1)

# Constants
WELCOME_MESSAGE = """👋 **Bine ai venit în CorectBet!**

De peste **7 ani construim și dezvoltăm această comunitate**, iar unul dintre lucrurile la care am ținut întotdeauna este **calitatea membrilor**, nu doar numărul lor.

🛡️ Din acest motiv, accesul se realizează prin intermediul botului oficial CorectBet.

Nu acceptăm **boți, conturi fake sau membri generați artificial**. Ne dorim o comunitate formată din **persoane reale și active**, interesate de conținutul pe care îl oferim.

Această verificare ne ajută să păstrăm grupul curat și standardele pe care le-am construit în toți acești ani.

✅ **Ești o persoană reală? Continuă mai jos pentru acces.**"""

ACCESS_CONFIRMED = """🎉 **Acces confirmat!**

Bine ai venit în comunitatea CorectBet. Ai fost verificat cu succes."""

NOT_JOINED_MESSAGE = """❌ **Nu ești încă membru al canalului.**

Te rugăm să intri în canal folosind butonul de mai jos, apoi revino și apasă „AM INTRAT ÎN CANAL”."""

# Keyboard functions
def get_verify_keyboard():
    keyboard = [[InlineKeyboardButton("🔐 VERIFICĂ ȘI INTRĂ ÎN CORECTBET", url=CHANNEL_LINK)]]
    return InlineKeyboardMarkup(keyboard)

def get_check_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔐 INTRĂ ÎN CORECTBET", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ AM INTRAT ÎN CANAL", callback_data='check')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_access_confirmed_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Vizitează Canalul", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🔄 Verifică din nou", callback_data='check')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        user = update.effective_user
        logger.info(f"User {user.id} started the bot")
        
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=get_verify_keyboard(),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text("❌ Error. Please try again.")

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user has joined the channel"""
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        await query.answer()
        logger.info(f"Checking membership for user {user_id}")
        
        # Get chat member
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_ID_INT, 
            user_id=user_id
        )
        
        status = member.status
        logger.info(f"User {user_id} status: {status}")
        
        if status in ['member', 'administrator', 'creator']:
            await query.edit_message_text(
                ACCESS_CONFIRMED,
                reply_markup=get_access_confirmed_keyboard(),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                NOT_JOINED_MESSAGE,
                reply_markup=get_check_keyboard(),
                parse_mode='Markdown'
            )
            
    except BadRequest as e:
        logger.error(f"BadRequest: {e}")
        error_msg = "❌ **Eroare de verificare.**\n\nTe rugăm să încerci din nou."
        
        if "chat not found" in str(e).lower():
            error_msg = "❌ **Canalul nu a fost găsit.**\n\nContactează suportul."
        elif "bot is not a member" in str(e).lower():
            error_msg = "❌ **Botul nu este administrator.**\n\nContactează suportul."
        
        await query.edit_message_text(
            error_msg,
            reply_markup=get_check_keyboard(),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        await query.edit_message_text(
            "❌ **A apărut o eroare.**\n\nTe rugăm să încerci din nou.",
            reply_markup=get_check_keyboard(),
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Error: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ A apărut o eroare. Te rugăm să încerci din nou."
            )
    except:
        pass

def main():
    """Start the bot"""
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(check_membership, pattern='^check$'))
        application.add_error_handler(error_handler)
        
        # Log startup
        logger.info("Bot starting...")
        logger.info(f"Channel ID: {CHANNEL_ID_INT}")
        logger.info(f"Channel Link: {CHANNEL_LINK}")
        
        # Start polling
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
