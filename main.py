import os
import re
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Target bots to monitor
try:
    TARGET_BOTS = set(
        filter(bool, map(str.strip, os.getenv("TARGET_BOTS", "").split(",")))
    )
except Exception as e:
    logger.error(f"Failed to parse TARGET_BOTS: {e}")
    TARGET_BOTS = {"instagrambot", "SaveMedia_bot"}


# Thresholds
LENGTH_THRESHOLD = 150
CYRILLIC_PATTERN = re.compile(r"[а-яА-ЯёЁ]")


async def filter_bot_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks messages from specific bots for spam patterns and deletes them."""
    msg = update.effective_message
    if not msg:
        return

    # Extract sender info
    user = update.effective_user
    chat = update.effective_chat
    username = user.username if user else None
    display_name = username or (user.first_name if user else "Unknown")

    text = msg.text or msg.caption or ""
    chat_info = f"[{chat.type} {chat.id}]" if chat else "[Unknown Chat]"

    # Print all messages seen for debugging
    logger.info(
        f"Message in {chat_info} from @{username} ({display_name}): {text[:100]}{'...' if len(text) > 100 else ''}"
    )

    # Check if sender is a target bot OR if the message is a forward
    is_from_target = username in TARGET_BOTS
    is_forward = bool(msg.forward_origin)

    if not is_from_target and not is_forward:
        return

    has_cyrillic = bool(CYRILLIC_PATTERN.search(text))
    is_long = len(text) > LENGTH_THRESHOLD
    has_buttons = bool(msg.reply_markup and msg.reply_markup.inline_keyboard)

    # Logic: Delete if it has Cyrillic AND (is long OR has buttons)
    if has_cyrillic and (is_long or has_buttons):
        try:
            # Check if sender is an admin (bots can't delete admin messages)
            if chat.type in ["group", "supergroup"] and user:
                member = await chat.get_member(user.id)
                if member.status in ["administrator", "creator"]:
                    logger.info(f"Skipping deletion: @{username} is an admin.")
                    return

            await msg.delete()
            reason = "Long" if is_long else "Buttons"
            source = "forward" if is_forward else f"bot @{username}"
            logger.info(
                f"Successfully deleted spam {source}. Reason: {reason} with Cyrillic."
            )
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            logger.error(
                "Ensure the bot is an ADMIN with 'Delete Messages' permission."
            )


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
    logger.info(
        "NOTE: To receive all messages in groups, ensure 'Group Privacy' is DISABLED in @BotFather or the bot is an ADMIN."
    )
    application.run_polling()


if __name__ == "__main__":
    main()
