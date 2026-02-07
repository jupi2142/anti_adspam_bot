import os
import re
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Target bots to monitor
try:
    TARGET_BOTS = set(filter(bool, map(str.strip, os.getenv("TARGET_BOTS", "").split(","))))
except Exception as e:
    logger.error(f"Failed to parse TARGET_BOTS: {e}")
    TARGET_BOTS = {"instagrambot", "SaveMedia_bot"}


# Thresholds
LENGTH_THRESHOLD = 150
CYRILLIC_PATTERN = re.compile(r"[а-яА-ЯёЁ]")

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def filter_bot_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks messages from specific bots for spam patterns and deletes them."""
    if not update.message or not update.message.from_user:
        return

    sender = update.message.from_user
    username = sender.username

    # Check if the sender is one of the target bots
    if username not in TARGET_BOTS:
        return

    text = update.message.text or update.message.caption or ""
    has_cyrillic = bool(CYRILLIC_PATTERN.search(text))
    is_long = len(text) > LENGTH_THRESHOLD
    has_buttons = bool(
        update.message.reply_markup and update.message.reply_markup.inline_keyboard
    )

    # Logic: Delete if it has Cyrillic AND (is long OR has buttons)
    if has_cyrillic and (is_long or has_buttons):
        try:
            await update.message.delete()
            logger.info(
                f"Deleted spam from @{username}. Reason: {'Long' if is_long else 'Buttons'} with Cyrillic."
            )
        except Exception as e:
            logger.error(f"Failed to delete message from @{username}: {e}")


def main():
    if not TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN not found in environment. Please set it in .env"
        )
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Handle all messages (including those with media/captions)
    spam_handler = MessageHandler(filters.ALL & ~filters.COMMAND, filter_bot_spam)
    application.add_handler(spam_handler)

    logger.info("Anti-Russian Spam Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()
