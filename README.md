
# Telegram WebScan SQLi Bot

A Telegram bot that performs basic SQLi vulnerability scanning using sqlmap and logs scan activity to a SQLite database.

## Features

- `/scan <url>`: Run SQLi scan on a URL with GET parameters.
- `/history`: Shows last 5 scans by the user.
- Admin commands:
  - `/users`: List all users who used the bot.
  - `/logs`: View last 10 scan logs.
  - `/ban <user_id>` & `/unban <user_id>`: Ban/unban users.
  - `/banned`: List of banned users.

## Deployment (Render)

1. Upload the contents of this repo to a GitHub repository.
2. Create a new Web Service on Render:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
3. Add environment variable:
   - `BOT_TOKEN`: Your Telegram bot token.

## Requirements

- Python 3.9+
- `pyTelegramBotAPI`
- `sqlmap` must be installed and available in system path.

## Note

This tool is for legal and educational use only. Always get permission before scanning websites.

