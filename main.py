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

    user = update.effective_user
    chat = update.effective_chat
    username = user.username if user else None
    display_name = username or (user.first_name if user else "Unknown")

    text = msg.text or msg.caption or ""
    chat_info = f"[{chat.type} {chat.id}]" if chat else "[Unknown Chat]"

    logger.info(
        f"Message in {chat_info} from @{username} ({display_name}): {text[:100]}{'...' if len(text) > 100 else ''}"
    )

    is_from_target = username in TARGET_BOTS
    is_forward = bool(msg.forward_origin)

    if not is_from_target and not is_forward:
        return

    has_cyrillic = bool(CYRILLIC_PATTERN.search(text))
    is_long = len(text) > LENGTH_THRESHOLD
    has_buttons = bool(msg.reply_markup and msg.reply_markup.inline_keyboard)

    if has_cyrillic and (is_long or has_buttons):
        try:
            if chat.type in ["group", "supergroup"] and user:
                member = await chat.get_member(user.id)
                if member.status in ["administrator", "creator"]:
                    logger.info(f"Skipping deletion: @{username} is an admin.")
                    return

            delete_result = await msg.delete()
            reason = "Long" if is_long else "Buttons"
            source = "forward" if is_forward else f"bot @{username}"
            if delete_result:
                logger.info(
                    f"Successfully deleted spam {source}. Reason: {reason} with Cyrillic."
                )
            else:
                logger.error(
                    f"Delete returned False for {source}. Reason: {reason} with Cyrillic. Message may still exist."
                )
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            logger.error(
                "Ensure the bot is an ADMIN with 'Delete Messages' permission."
            )


async def handle_bot_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles bot mentions in replies to delete Cyrillic messages from target bots."""
    msg = update.effective_message
    logger.info(
        f"[MENTION] Handler called for message: {msg.message_id if msg else 'None'}"
    )

    if not msg:
        logger.warning("[MENTION] No message found")
        return

    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        logger.warning(f"[MENTION] Missing chat={chat}, user={user}")
        return

    text = msg.text or msg.caption or ""
    logger.info(f"[MENTION] From @{user.username}: {text[:50]}")
    logger.info(f"[MENTION] Is reply: {msg.reply_to_message is not None}")

    if not msg.reply_to_message:
        logger.info("[MENTION] Not a reply, skipping")
        return

    bot_username = context.bot.username
    logger.info(f"[MENTION] Bot username: @{bot_username}")
    logger.info(f"[MENTION] Looking for: @{bot_username} in: {text.lower()}")

    has_bot_mention = bot_username and f"@{bot_username}" in text.lower()
    logger.info(f"[MENTION] Bot mentioned: {has_bot_mention}")

    if not has_bot_mention:
        logger.info("[MENTION] Bot not mentioned")
        return

    target_msg = msg.reply_to_message
    target_user = target_msg.from_user
    logger.info(
        f"[MENTION] Target message from: @{target_user.username if target_user else 'None'}"
    )

    if not target_user:
        logger.warning("[MENTION] No target user")
        return

    target_username = target_user.username
    if target_username is None:
        logger.warning("[MENTION] Target has no username")
        return

    logger.info(f"[MENTION] Target: @{target_username}, TARGET_BOTS: {TARGET_BOTS}")
    logger.info(f"[MENTION] Is forward: {target_msg.forward_origin is not None}")

    # Check if directly from target bot OR if it's a forward from target bot
    is_from_target = target_username in TARGET_BOTS
    is_forward_from_target = False

    if target_msg.forward_origin:
        forward_origin = target_msg.forward_origin
        logger.info(f"[MENTION] Forward origin type: {type(forward_origin).__name__}")

        # Get sender from forward origin
        forward_user = getattr(forward_origin, "sender_user", None)
        forward_chat = getattr(forward_origin, "sender_chat", None)

        if forward_user and getattr(forward_user, "username", None):
            forward_username = forward_user.username
            logger.info(f"[MENTION] Forward from user: @{forward_username}")
            is_forward_from_target = forward_username in TARGET_BOTS
        elif forward_chat and getattr(forward_chat, "username", None):
            forward_username = forward_chat.username
            logger.info(f"[MENTION] Forward from chat: @{forward_username}")
            is_forward_from_target = forward_username in TARGET_BOTS

    logger.info(
        f"[MENTION] Is from target: {is_from_target}, Is forward from target: {is_forward_from_target}"
    )

    if not is_from_target and not is_forward_from_target:
        logger.info(f"[MENTION] Neither direct nor forwarded from TARGET_BOTS")
        return

    target_text = target_msg.text or target_msg.caption or ""
    has_cyrillic = bool(CYRILLIC_PATTERN.search(target_text))
    logger.info(f"[MENTION] Target text: {target_text[:50]}")
    logger.info(f"[MENTION] Has Cyrillic: {has_cyrillic}")

    if not has_cyrillic:
        logger.info("[MENTION] No Cyrillic in target")
        return

    try:
        if chat and chat.type in ["group", "supergroup"] and target_user:
            target_member = await chat.get_member(target_user.id)
            logger.info(f"[MENTION] Target status: {target_member.status}")
            if target_member.status in ["administrator", "creator"]:
                logger.info(f"[MENTION] Skipping: @{target_username} is admin")
                return

        logger.info(f"[MENTION] Deleting message from @{target_username}")
        await target_msg.delete()
        logger.info(f"[MENTION] Deleting request from @{user.username}")
        await msg.delete()
        logger.info(
            f"[MENTION] SUCCESS: Deleted @{target_username}'s message by request of @{user.username}"
        )
    except Exception as e:
        logger.error(f"[MENTION] FAILED: {e}")
        logger.error(f"[MENTION] Exception type: {type(e).__name__}")


def main():
    if not TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN not found in environment. Please set it in .env"
        )
        return

    application = ApplicationBuilder().token(TOKEN).build()

    mention_handler = MessageHandler(filters.ALL & ~filters.COMMAND, handle_bot_mention)
    application.add_handler(mention_handler, group=0)

    spam_handler = MessageHandler(filters.ALL & ~filters.COMMAND, filter_bot_spam)
    application.add_handler(spam_handler, group=1)

    logger.info("Anti-Russian Spam Bot is starting...")
    logger.info(
        "NOTE: To receive all messages in groups, ensure 'Group Privacy' is DISABLED in @BotFather or the bot is an ADMIN."
    )
    application.run_polling()


if __name__ == "__main__":
    main()
