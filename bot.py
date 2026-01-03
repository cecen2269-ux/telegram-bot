import os
import sqlite3
import time
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =====================
# AYARLAR
# =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s" 
ADMIN_ID = 123456789

DB_NAME = "bot.db"
FLOOD_SECONDS = 2

# =====================
# DATABASE
# =====================
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    joined_at TEXT,
    premium_until TEXT,
    banned INTEGER DEFAULT 0,
    last_message INTEGER DEFAULT 0,
    partner INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS match_queue (
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()

# =====================
# YARDIMCI
# =====================
def is_admin(uid): return uid == ADMIN_ID

def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

def add_user(user):
    if not get_user(user.id):
        cur.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,?,?)",
            (user.id, user.username, datetime.now().isoformat(), None, 0, 0, None)
        )
        conn.commit()

def is_premium(uid):
    u = get_user(uid)
    if not u or not u[3]: return False
    return datetime.fromisoformat(u[3]) > datetime.now()

def flood_ok(uid):
    now = int(time.time())
    u = get_user(uid)
    if not u: return True
    if now - u[5] < FLOOD_SECONDS: return False
    cur.execute("UPDATE users SET last_message=? WHERE user_id=?", (now, uid))
    conn.commit()
    return True

def get_partner(uid):
    cur.execute("SELECT partner FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return r[0] if r else None

def set_partner(a, b):
    cur.execute("UPDATE users SET partner=? WHERE user_id=?", (b, a))
    cur.execute("UPDATE users SET partner=? WHERE user_id=?", (a, b))
    conn.commit()

def clear_partner(uid):
    cur.execute("UPDATE users SET partner=NULL WHERE user_id=?", (uid,))
    conn.commit()

# =====================
# MENÜ
# =====================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Eşleş", callback_data="match")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium")]
    ])

# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user)
    await update.message.reply_text(
        "👑 Hoş geldin!\nAnonim sohbet botu",
        reply_markup=main_menu()
    )

# =====================
# BUTONLAR
# =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "profile":
        p = "💎 Premium" if is_premium(uid) else "🆓 Normal"
        await q.edit_message_text(
            f"👤 Profil\n\n🆔 {uid}\n⭐ {p}",
            reply_markup=main_menu()
        )

    elif q.data == "premium":
        await q.edit_message_text(
            "💎 Premium\n\n"
            "• Sınırsız eşleşme\n"
            "• Öncelikli eşleşme\n\n"
            "💳 Ödeme sonrası admin premium verir.",
            reply_markup=main_menu()
        )

    elif q.data == "match":
        if get_partner(uid):
            await q.edit_message_text("❗ Zaten eşleşmişsin.")
            return

        cur.execute("SELECT user_id FROM match_queue WHERE user_id!=? LIMIT 1", (uid,))
        other = cur.fetchone()

        if other:
            other_id = other[0]
            cur.execute("DELETE FROM match_queue WHERE user_id IN (?,?)", (uid, other_id))
            set_partner(uid, other_id)

            await context.bot.send_message(
                other_id, "✅ Eşleştin! Yazabilirsin.\n/leave"
            )
            await q.edit_message_text("✅ Eşleştin! Yazabilirsin.\n/leave")
        else:
            cur.execute("INSERT OR IGNORE INTO match_queue VALUES (?)", (uid,))
            conn.commit()
            await q.edit_message_text("⏳ Eşleşme bekleniyor...")

# =====================
# CHAT
# =====================
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not flood_ok(uid): return

    partner = get_partner(uid)
    if partner:
        await context.bot.send_message(partner, update.message.text)
    else:
        await update.message.reply_text(
            "Menüyü kullan kral 👑",
            reply_markup=main_menu()
        )

# =====================
# LEAVE
# =====================
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    partner = get_partner(uid)
    if partner:
        clear_partner(uid)
        clear_partner(partner)
        await context.bot.send_message(partner, "❌ Karşı taraf sohbeti bitirdi.")
        await update.message.reply_text("❌ Sohbet bitti.", reply_markup=main_menu())

# =====================
# ADMIN
# =====================
async def addpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    uid = int(context.args[0])
    days = int(context.args[1])
    until = datetime.now() + timedelta(days=days)
    cur.execute(
        "UPDATE users SET premium_until=? WHERE user_id=?",
        (until.isoformat(), uid)
    )
    conn.commit()
    await update.message.reply_text("✅ Premium verildi")

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("addpremium", addpremium))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🔥 BOT ÇALIŞIYOR")
    app.run_polling()

if __name__ == "__main__":
    main()
