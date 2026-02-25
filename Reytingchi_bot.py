import telebot
from telebot.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats
import json
import os
import html

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8610406042:AAHw9P9V7MWGo2sBZNKqE2bwdwdaoEEuMHs"
DATA_FILE = "tablo_data.json"
# ======================================================

bot = telebot.TeleBot(BOT_TOKEN)

def setup_commands():
    group_commands = [
        BotCommand("on", "Tabloni boshlash"),
        BotCommand("off", "Tabloni o'chirish"),
        BotCommand("ball", "Ball miqdorini belgilash"),
        BotCommand("reyting", "Natijalar"),
        BotCommand("recount", "Boshlovchilikni topshirish"),
        BotCommand("reset", "Tozalash")
    ]
    try:
        bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
    except: pass

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_chat(data, chat_id):
    cid = str(chat_id)
    if cid not in data:
        data[cid] = {"active": False, "ball_amount": 5, "host_id": None, "host_name": "", "users": {}}
    return data[cid]

def is_admin(chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id, user_id)
        return m.status in ["administrator", "creator"]
    except: return False

def get_rating_text(chat_data):
    users = chat_data["users"]
    if not users: return "Hali ball yo'q."
    sorted_users = sorted(users.items(), key=lambda x: x[1]["balls"], reverse=True)
    lines = []
    rank, last_s = 0, -1
    for uid, info in sorted_users:
        s = info["balls"]
        if s != last_s: rank += 1; last_s = s
        m = {1:"🥇", 2:"🥈", 3:"🥉"}.get(rank, f"{rank}.")
        safe_name = html.escape(info["name"])
        lines.append(f'{m} <a href="tg://user?id={uid}">{safe_name}</a> — {s} ball')
    return "\n".join(lines)

@bot.message_handler(commands=["on"])
def cmd_on(message):
    if not is_admin(message.chat.id, message.from_user.id): return
    data = load_data()
    c = get_chat(data, message.chat.id)
    c["active"], c["host_id"], c["host_name"] = True, message.from_user.id, message.from_user.first_name
    c["users"] = {}
    save_data(data)
    bot.reply_to(message, "✅ Tablo yoqildi!")

@bot.message_handler(commands=["reyting"])
def cmd_r(message):
    data = load_data()
    c = get_chat(data, message.chat.id)
    bot.send_message(message.chat.id, f"<b>Natijalar:</b>\n\n{get_rating_text(c)}", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and m.text.strip() in ["+", "✅"])
def handle_p(message):
    if not message.reply_to_message or message.chat.type == "private": return
    data = load_data()
    c = get_chat(data, message.chat.id)
    if not c["active"] or (message.from_user.id != c["host_id"] and not is_admin(message.chat.id, message.from_user.id)): return
    
    target = message.reply_to_message.from_user
    if target.is_bot or target.id == message.from_user.id: return
    
    uid = str(target.id)
    if uid not in c["users"]: c["users"][uid] = {"name": target.first_name, "balls": 0}
    c["users"][uid]["balls"] += c["ball_amount"]
    save_data(data)
    
    s_name = html.escape(message.from_user.first_name)
    r_name = html.escape(target.first_name)
    
    try:
        bot.send_message(message.chat.id, f'<a href="tg://user?id={message.from_user.id}">{s_name}</a> <a href="tg://user?id={target.id}">{r_name}</a> ga {c["ball_amount"]} ball berdi', parse_mode="HTML")
        bot.send_message(message.chat.id, f"<b>Reyting:</b>\n\n{get_rating_text(c)}", parse_mode="HTML")
    except Exception as e:
        print(f"Xato: {e}")

setup_commands()
bot.infinity_polling()
    
