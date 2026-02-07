# Anti-Russian Spam Bot

A Telegram bot designed to automatically remove spam posts from specific bots in your group.

## Purpose

This bot targets `@instagrambot` and `@SaveMedia_bot`, which often post long advertisements with Cyrillic text and link buttons. It monitors these specific bots and deletes their messages when they match spam patterns.

## Features

- **Targeted Filtering**: Only monitors `@instagrambot` and `@SaveMedia_bot`
- **Smart Detection**: Deletes messages containing Cyrillic characters that are either:
  - Longer than 150 characters
  - Contain inline keyboards (link buttons)
- **Minimal Impact**: Ignores all other users and bots
- **Logging**: Provides console logs for deleted messages

## Setup

### 1. Get Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` to create a new bot
3. Follow the prompts and copy the **API token**

### 2. Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and replace the placeholder:
   ```
   TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
   ```

### 3. Install Dependencies

This project uses `uv` for dependency management:

```bash
uv sync
```

### 4. Run the Bot

```bash
uv run anti-spam-bot
```

### 5. Add to Group

1. Add your bot to the target Telegram group
2. Promote the bot to **Admin**
3. Enable **"Delete messages"** permission

## How It Works

The bot monitors all messages in the group and applies the following logic:

1. Checks if the message is from `@instagrambot` or `@SaveMedia_bot`
2. If yes, checks for Cyrillic characters in the message
3. If Cyrillic is found, checks if the message is either:
   - Longer than 150 characters, OR
   - Contains an inline keyboard (link buttons)
4. If all conditions are met, the message is immediately deleted

## Configuration

You can modify these constants in `main.py`:

- `TARGET_BOTS`: List of bot usernames to monitor
- `LENGTH_THRESHOLD`: Character count for "long" messages (default: 150)
- `CYRILLIC_PATTERN`: Regex pattern for Cyrillic detection

## Requirements

- Python 3.13+
- `uv` package manager
- Telegram Bot API token

## Dependencies

- `python-telegram-bot>=22.6`
- `python-dotenv>=1.2.1`

## License

Add your license here.