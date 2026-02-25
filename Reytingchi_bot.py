#!/usr/bin/env python3
"""
Tablo Boti - Guruh ball va reyting tizimi
Ikki xabarga ajratilgan, ko'k link va bir xil o'rinli versiya
"""

import telebot
from telebot.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats
import json
import os

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8610406042:AAHw9P9V7MWGo2sBZNKqE2bwdwdaoEEuMHs"
DATA_FILE = "tablo_data.json"
# ======================================================

bot = telebot.TeleBot(BOT_TOKEN)

# ========== Buyruqlar menyusini o'rnatish ==========
def setup_commands():
    group_commands = [
        BotCommand("on", "Tabloni boshlash"),
        BotCommand("off", "Tabloni o'chirish"),
        BotCommand("ball", "Ball miqdorini belgilash (admin)"),
        BotCommand("reyting", "Joriy natijalarni ko'rish"),
        BotCommand("recount", "Boshlovchilikni topshirish"),
        BotCommand("settings", "Sozlamalar"),
        BotCommand("stats", "Statistika"),
        BotCommand("reset", "Reytingni tozalash (admin)"),
    ]
    private_commands = [
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("settings", "Sozlamalar"),
        BotCommand("stats", "Statistika"),
    ]
    try:
        bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
        bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
        print("Buyruqlar menyusi o'rnatildi!")
    except Exception as e:
        print("Menyu xatosi:", e)

# ========== Ma'lumotlar ==========
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
        data[cid] = {
            "active": False,
            "ball_amount": 5,
            "host_id": None,
            "host_name": "",
            "users": {}
        }
    return data[cid]

def is_admin(chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id, user_id)
        return m.status in ["administrator", "creator"]
    except:
        return False

# ----- REYTING VA LINKLAR UCHUN YANGILANGAN FUNKSIYA -----
def get_rating_text(chat_data):
    users = chat_data["users"]
    if not users:
        return "Hali ball yo'q."
    
    # Ballarni ko'pligiga qarab tartiblaymiz
    sorted_users = sorted(users.items(), key=lambda x: x[1]["balls"], reverse=True)
    
    lines = []
    current_rank = 0
    last_score = -1
    
    for uid, info in sorted_users:
        score = info["balls"]
        # Bir xil ball to'plaganlarni bitta o'ringa qo'yish mantiqi
        if score != last_score:
            current_rank += 1
            last_score = score
            
        if current_rank == 1:
            medal = "🥇"
        elif current_rank == 2:
            medal = "🥈"
        elif current_rank == 3:
            medal = "🥉"
        else:
            medal = str(current_rank) + "."
            
        # Ismlarni ko'k rangli linkka aylantirish
        name_link = '<a href="tg://user?id=' + str(uid) + '">' + info["name"] + '</a>'
        lines.append(medal + " " + name_link + " — " + str(score) + " ball")
        
    return "\n".join(lines)

def get_full_name(user):
    name = user.first_name or ""
    if user.last_name:
        name += " " + user.last_name
    return name.strip()

# ========== /start ==========
@bot.message_handler(commands=["start"])
def cmd_start(message):
    user = message.from_user
    first_name = user.first_name or "Do'stim"
    user_id = user.id
    name_link = '<a href="tg://user?id=' + str(user_id) + '">' + first_name + '</a>'

    bot.reply_to(message,
        name_link + " Assalomu alaykum! 👋\n\n"
        "Men guruhlarda o'tkaziladigan turnirlarda ballarni hisoblab boraman.\n\n"
        "<b>Buning uchun meni guruhingizga qo'shib admin qilishingiz kerak!</b>\n\n"
        "📌 <b>Asosiy buyruqlar:</b>\n"
        "/on — Tabloni boshlash\n"
        "/off — Tabloni o'chirish\n"
        "/ball &lt;son&gt; — Ball miqdori\n"
        "/reyting — Natijalar\n"
        "/recount — Boshlovchilikni topshirish\n"
        "/settings — Sozlamalar\n"
        "/stats — Statistika\n"
        "/reset — Reytingni tozalash",
        parse_mode="HTML"
    )

# ========== /on ==========
@bot.message_handler(commands=["on"])
def cmd_on(message):
    if message.chat.type == "private":
        bot.reply_to(message, "Bu buyruq faqat guruhlarda ishlaydi!")
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "Faqat adminlar foydalana oladi!")
        return

    chat_id = str(message.chat.id)
    data = load_data()
    chat_data = get_chat(data, chat_id)

    if chat_data["active"]:
        bot.reply_to(message, "Tablo allaqachon yoqilgan!")
        return

    host_name = get_full_name(message.from_user)
    chat_data["active"] = True
    chat_data["host_id"] = message.from_user.id
    chat_data["host_name"] = host_name
    chat_data["users"] = {}
    save_data(data)

    ball = chat_data["ball_amount"]
    bot.reply_to(message,
        "Tablo yoqildi, boshlovchi: " + host_name + "\n"
        "To'g'ri javobni ✅ belgisi bilan belgilang!\n"
        " Har bir to'g'ri javobga " + str(ball) + " baldan beriladi"
    )

# ========== /off ==========
@bot.message_handler(commands=["off"])
def cmd_off(message):
    if message.chat.type == "private":
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "Faqat adminlar foydalana oladi!")
        return

    chat_id = str(message.chat.id)
    data = load_data()
    chat_data = get_chat(data, chat_id)

    if not chat_data["active"]:
        bot.reply_to(message, "Tablo hali yoqilmagan!")
        return

    chat_data["active"] = False
    rating = get_rating_text(chat_data)
    save_data(data)

    bot.reply_to(message,
        "Tablo o'chirildi!\n\n"
        "Yakuniy natijalar:\n\n" + rating,
        parse_mode="HTML"
    )

# ========== /ball ==========
@bot.message_handler(commands=["ball"])
def cmd_ball(message):
    if message.chat.type == "private":
        bot.reply_to(message, "Bu buyruq faqat guruhlarda ishlaydi!")
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "Faqat adminlar foydalana oladi!")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "Format: /ball <son>  |  Misol: /ball 5")
        return

    amount = int(parts[1])
    if amount <= 0:
        bot.reply_to(message, "Ball 0 dan katta bo'lishi kerak!")
        return

    chat_id = str(message.chat.id)
    data = load_data()
    chat_data = get_chat(data, chat_id)
    chat_data["ball_amount"] = amount
    save_data(data)
    bot.reply_to(message, "Ball miqdori " + str(amount) + " ga o'rnatildi!")

# ========== /recount ==========
@bot.message_handler(commands=["recount"])
def cmd_recount(message):
    if message.chat.type == "private":
        return

    chat_id = str(message.chat.id)
    data = load_data()
    chat_data = get_chat(data, chat_id)

    if not chat_data["active"]:
        bot.reply_to(message, "Avval /on bilan tabloni yoqing!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "Bu buyruqni boshlovchilikni bermoqchi bo'lgan odamingizga javob tarzida yo'llang")
        return

    sender_id = message.from_user.id
    host_id = chat_data.get("host_id")

    if sender_id != host_id and not is_admin(message.chat.id, sender_id):
        bot.reply_to(message, "Boshlovchilikni faqat joriy boshlovchi yoki admin topshira oladi!")
        return

    new_host = message.reply_to_message.from_user
    new_host_name = get_full_name(new_host)
    old_host_name = chat_data["host_name"]

    chat_data["host_id"] = new_host.id
    chat_data["host_name"] = new_host_name
    save_data(data)

    bot.reply_to(message,
        old_host_name + " boshlovchilikni " + new_host_name + " ga topshirdi!"
    )

# ========== /reyting va /stats ==========
@bot.message_handler(commands=["reyting", "stats"])
def cmd_reyting(message):
    chat_id = str(message.chat.id)
    data = load_data()
    chat_data = get_chat(data, chat_id)

    rating = get_rating_text(chat_data)
    status = "🟢 Tablo: YOQILGAN" if chat_data["active"] else "🔴 Tablo: O'CHIRILGAN"
    
    host_id = chat_data.get("host_id")
    host_name = chat_data.get("host_name")
    
    if host_id and host_name:
        host_link = '<a href="tg://user?id=' + str(host_id) + '">' + host_name + '</a>'
        host = "Boshlovchi: " + host_link
    else:
        host = ""
        
    ball = "Ball miqdori: " + str(chat_data["ball_amount"])

    text = status + "\n"
    if host:
        text += host + "\n"
    text += ball + "\n\nNatijalar:\n\n" + rating

    bot.reply_to(message, text, parse_mode="HTML")

# ========== /settings ==========
@bot.message_handler(commands=["settings"])
def cmd_settings(message):
    chat_id = str(message.chat.id)
    data = load_data()
    chat_data = get_chat(data, chat_id)

    status = "🟢 Yoqilgan" if chat_data["active"] else "🔴 O'chirilgan"
    host = chat_data["host_name"] if chat_data["host_name"] else "Yo'q"

    bot.reply_to(message,
        "Sozlamalar:\n\n"
        "Holat: " + status + "\n"
        "Boshlovchi: " + host + "\n"
        "Ball miqdori: " + str(chat_data["ball_amount"]) + "\n\n"
        "Ball miqdorini o'zgartirish:\n/ball <son>"
    )

# ========== /reset ==========
@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    if message.chat.type == "private":
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "Faqat adminlar foydalana oladi!")
        return

    chat_id = str(message.chat.id)
    data = load_data()
    chat_data = get_chat(data, chat_id)
    chat_data["users"] = {}
    save_data(data)
    bot.reply_to(message, "Reyting tozalandi!")

# ========== + VA ✅ BELGISI UCHUN IKKITA XABAR ==========
@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_plus(message):
    if message.text.strip() not in ["+", "✅"]:
        return
    if message.chat.type == "private":
        return
    if not message.reply_to_message:
        return

    chat_id = str(message.chat.id)
    sender = message.from_user
    data = load_data()
    chat_data = get_chat(data, chat_id)

    if not chat_data["active"]:
        return

    host_id = chat_data.get("host_id")
    sender_is_host = (sender.id == host_id)
    sender_is_admin = is_admin(message.chat.id, sender.id)

    if not sender_is_host and not sender_is_admin:
        bot.reply_to(message, "Ball faqat boshlovchi yoki adminlar tomonidan beriladi!")
        return

    receiver = message.reply_to_message.from_user
    if receiver.id == sender.id:
        bot.reply_to(message, "O'zingizga ball bera olmaysiz!")
        return
    if receiver.is_bot:
        return

    amount = chat_data["ball_amount"]
    receiver_id = str(receiver.id)
    receiver_name = get_full_name(receiver)
    sender_name = get_full_name(sender)

    if receiver_id not in chat_data["users"]:
        chat_data["users"][receiver_id] = {"name": receiver_name, "balls": 0}
    chat_data["users"][receiver_id]["name"] = receiver_name
    chat_data["users"][receiver_id]["balls"] += amount
    save_data(data)

    rating_text = get_rating_text(chat_data)
    
    # Ismlarni ko'k linkka o'tkazish
    sender_link = '<a href="tg://user?id=' + str(sender.id) + '">' + sender_name + '</a>'
    receiver_link = '<a href="tg://user?id=' + receiver_id + '">' + receiver_name + '</a>'
    
    host_name = chat_data["host_name"]
    host_link = '<a href="tg://user?id=' + str(host_id) + '">' + host_name + '</a>'

    # --- 1-XABAR ---
    msg1 = f"{sender_link} {receiver_link} ga {amount} ball qo'shildi"
    bot.reply_to(message.reply_to_message, msg1, parse_mode="HTML")

    # --- 2-XABAR ---
    msg2 = f"Boshlovchi: {host_link}\n\nXozirgi natijalar:\n\n{rating_text}"
    bot.send_message(message.chat.id, msg2, parse_mode="HTML")

# ========== Ishga tushirish ==========
print("Bot ishga tushmoqda...")
setup_commands()
print("Bot ishga tushdi!")
bot.infinity_polling()
    
