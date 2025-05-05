import telebot
import os
import sqlite3
import subprocess

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

FORCE_JOIN_CHANNEL = "@upsc_coree" "@uchitra_security"
OWNER_USERNAME = "@Rat_Reaper"

@bot.message_handler(commands=["start"])
def start(msg):
    user_id = msg.from_user.id
    username = msg.from_user.username or ""
    first_name = msg.from_user.first_name or ""
    chat_id = msg.chat.id

    # Force join check
    try:
        user = bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        if user.status in ['left', 'kicked']:
            bot.send_message(chat_id, f"Please join {FORCE_JOIN_CHANNEL} to use this bot.")
            return
    except:
        bot.send_message(chat_id, "Channel unavailable. Contact owner.")
        return

    # Referral tracking
    conn = sqlite3.connect("referrals.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS referrals (user_id INTEGER PRIMARY KEY, referred_by INTEGER)")
    ref_id = msg.text.split()[1] if len(msg.text.split()) > 1 else None
    try:
        cur.execute("INSERT INTO referrals (user_id, referred_by) VALUES (?, ?)", (user_id, ref_id))
    except:
        pass
    conn.commit()
    conn.close()

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Contact Owner", url=f"https://t.me/{OWNER_USERNAME.strip('@')}"))
    bot.send_message(chat_id, f"Welcome {first_name}!", reply_markup=markup)

@bot.message_handler(commands=["scan"])
def scan(msg):
    if len(msg.text.split()) < 2:
        bot.reply_to(msg, "Please provide a URL to scan.")
        return
    url = msg.text.split(" ", 1)[1]
    try:
        result = subprocess.getoutput(f"python3 sqlmap/sqlmap.py -u \"{url}\" --batch --level=1")
        bot.send_message(msg.chat.id, f"Scan result:\n{result[:4000]}")
    except Exception as e:
        bot.send_message(msg.chat.id, f"Error: {str(e)}")

bot.polling()
