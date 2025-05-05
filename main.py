import telebot
import subprocess
import sqlite3
import os

BOT_TOKEN = "7655006894:AAFynoptxT_nT4gmtLwI7dnmJ-s6cU-tFjY"
bot = telebot.TeleBot(BOT_TOKEN)
CHANNEL_USERNAME = '@Uchitra_sec'  # Force join channel
OWNER_ID = 7655006894  # Replace with your Telegram user ID

bot = telebot.TeleBot(TOKEN)

# Force join checker
def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# SQLite setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, referral TEXT, plan TEXT, expiry TEXT, banned INTEGER DEFAULT 0)")
    conn.commit()
    conn.close()

init_db()

def add_user(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, plan, expiry, banned) VALUES (?, ?, ?, 0)", (user_id, 'free', 'never'))
    conn.commit()
    conn.close()

def get_user_plan(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT plan FROM users WHERE id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "free"

def get_plan_expiry(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT expiry FROM users WHERE id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "never"

def is_banned(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT banned FROM users WHERE id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def ban_user_in_db(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET banned=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def unban_user_in_db(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET banned=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def get_total_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    result = c.fetchone()
    conn.close()
    return result[0]

@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id

    if is_banned(user_id):
        bot.send_message(msg.chat.id, "You are banned from using this bot.")
        return

    if not is_user_in_channel(user_id):
        bot.send_message(msg.chat.id, f"Please join {CHANNEL_USERNAME} to use this bot.")
        return

    add_user(user_id)
    bot.send_message(msg.chat.id, "Welcome to WebScan Bot!\nUse /help to view commands.")

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    bot.send_message(msg.chat.id, """
Available Commands:
/start - Start the bot
/scan <url> - Scan a website
/myplan - View your current plan
/referral - Your referral code
/buy - Buy premium
/users - (Admin) total users
/ban <user_id> - (Admin)
/unban <user_id> - (Admin)
/owner - Contact bot owner
    """)

@bot.message_handler(commands=['owner'])
def owner_cmd(msg):
    bot.send_message(msg.chat.id, "Contact Owner: @yourownerusername")

@bot.message_handler(commands=['myplan'])
def myplan(msg):
    user_id = msg.from_user.id
    plan = get_user_plan(user_id)
    expiry = get_plan_expiry(user_id)
    bot.send_message(msg.chat.id, f"Your current plan: {plan}\nExpires: {expiry}")

@bot.message_handler(commands=['referral'])
def referral_cmd(msg):
    user_id = msg.from_user.id
    bot.send_message(msg.chat.id, f"Your referral code: REF{user_id}")

@bot.message_handler(commands=['buy'])
def buy_cmd(msg):
    bot.send_message(msg.chat.id, "To buy premium, contact @RatReaper")

@bot.message_handler(commands=['users'])
def total_users(msg):
    if msg.from_user.id != OWNER_ID:
        return
    count = get_total_users()
    bot.send_message(msg.chat.id, f"Total users: {count}")

@bot.message_handler(commands=['ban'])
def ban_user(msg):
    if msg.from_user.id != OWNER_ID:
        return
    try:
        uid = int(msg.text.split()[1])
        ban_user_in_db(uid)
        bot.send_message(msg.chat.id, f"User {uid} banned.")
    except:
        bot.send_message(msg.chat.id, "Usage: /ban <user_id>")

@bot.message_handler(commands=['unban'])
def unban_user(msg):
    if msg.from_user.id != OWNER_ID:
        return
    try:
        uid = int(msg.text.split()[1])
        unban_user_in_db(uid)
        bot.send_message(msg.chat.id, f"User {uid} unbanned.")
    except:
        bot.send_message(msg.chat.id, "Usage: /unban <user_id>")

@bot.message_handler(commands=['scan'])
def scan_cmd(msg):
    user_id = msg.from_user.id

    if is_banned(user_id):
        bot.send_message(msg.chat.id, "You are banned.")
        return

    if not is_user_in_channel(user_id):
        bot.send_message(msg.chat.id, f"Join {CHANNEL_USERNAME} to use this bot.")
        return

    try:
        url = msg.text.split()[1]
        output = subprocess.check_output(["python3", "sqlmap/sqlmap.py", "-u", url, "--batch", "--level=1"], stderr=subprocess.STDOUT, timeout=60)
        result = output.decode("utf-8")
        bot.send_message(msg.chat.id, f"Scan result:\n{result[:4000]}")
    except Exception as e:
        bot.send_message(msg.chat.id, f"Error: {e}")

bot.polling()
