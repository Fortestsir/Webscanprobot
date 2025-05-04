
import telebot
import subprocess
import os
import sqlite3

# === CONFIG ===
API_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(API_TOKEN)
ADMIN_ID = 123456789  # Replace with your Telegram user ID

# === DB SETUP ===
conn = sqlite3.connect("scans.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    url TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS banned_users (
    user_id INTEGER PRIMARY KEY
)
""")

conn.commit()

# === COMMANDS ===

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "Welcome to WebScan SQLi Bot.\nUse /scan <url> to scan.\nUse /history to view your scans.")

@bot.message_handler(commands=["scan"])
def scan(msg):
    args = msg.text.split()
    if len(args) != 2:
        return bot.send_message(msg.chat.id, "Usage: /scan https://site.com/page.php?id=1")

    # Check if banned
    cur.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (msg.from_user.id,))
    if cur.fetchone():
        return bot.send_message(msg.chat.id, "Access denied. You are banned from using this bot.")

    url = args[1]
    if "?" not in url or "=" not in url:
        return bot.send_message(msg.chat.id, "URL must include GET parameters like ?id=1")

    bot.send_message(msg.chat.id, "Scanning... please wait.")

    # Log the scan
    user = msg.from_user
    cur.execute("INSERT INTO scans (user_id, username, url) VALUES (?, ?, ?)", (user.id, user.username or "unknown", url))
    conn.commit()

    try:
        result = subprocess.check_output(
            ["sqlmap", "-u", url, "--batch", "--level=1", "--risk=1", "--smart"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=90
        )
        scan_result = f"Scan result:\n\n{result[:4000]}"
        bot.send_message(msg.chat.id, scan_result)
    except subprocess.TimeoutExpired:
        bot.send_message(msg.chat.id, "Scan timed out.")
    except Exception as e:
        bot.send_message(msg.chat.id, f"Error:\n{str(e)}")

@bot.message_handler(commands=["history"])
def history(msg):
    user = msg.from_user
    cur.execute("SELECT url, timestamp FROM scans WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user.id,))
    rows = cur.fetchall()

    if not rows:
        return bot.send_message(msg.chat.id, "No scan history found.")

    history_text = "\n\n".join([f"{r[1]}:\n{r[0]}" for r in rows])
    bot.send_message(msg.chat.id, f"Your last 5 scans:\n\n{history_text}")

# === ADMIN COMMANDS ===

@bot.message_handler(commands=["users"])
def list_users(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    cur.execute("SELECT DISTINCT user_id, username FROM scans")
    users = cur.fetchall()
    text = "\n".join([f"{u[0]} ({u[1]})" for u in users])
    bot.send_message(msg.chat.id, f"Unique users:\n\n{text or 'None'}")

@bot.message_handler(commands=["logs"])
def all_logs(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    cur.execute("SELECT username, url, timestamp FROM scans ORDER BY timestamp DESC LIMIT 10")
    logs = cur.fetchall()
    if not logs:
        return bot.send_message(msg.chat.id, "No logs yet.")
    text = "\n\n".join([f"{r[2]} - @{r[0]}\n{r[1]}" for r in logs])
    bot.send_message(msg.chat.id, f"Recent scans:\n\n{text}")

@bot.message_handler(commands=["ban"])
def ban_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    args = msg.text.split()
    if len(args) != 2:
        return bot.send_message(msg.chat.id, "Usage: /ban <user_id>")
    try:
        user_id = int(args[1])
        cur.execute("INSERT OR IGNORE INTO banned_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        bot.send_message(msg.chat.id, f"User {user_id} has been banned.")
    except:
        bot.send_message(msg.chat.id, "Invalid user ID.")

@bot.message_handler(commands=["unban"])
def unban_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    args = msg.text.split()
    if len(args) != 2:
        return bot.send_message(msg.chat.id, "Usage: /unban <user_id>")
    try:
        user_id = int(args[1])
        cur.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        conn.commit()
        bot.send_message(msg.chat.id, f"User {user_id} has been unbanned.")
    except:
        bot.send_message(msg.chat.id, "Invalid user ID.")

@bot.message_handler(commands=["banned"])
def banned_list(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    cur.execute("SELECT user_id FROM banned_users")
    users = cur.fetchall()
    if not users:
        return bot.send_message(msg.chat.id, "No users are banned.")
    text = "\n".join(str(u[0]) for u in users)
    bot.send_message(msg.chat.id, f"Banned users:\n\n{text}")

# === RUN ===
bot.polling()
