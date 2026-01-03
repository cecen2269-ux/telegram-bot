import os
import sqlite3
import time
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
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
ADMIN_ID = 123456789  # kendi Telegram ID
FORCE_CHANNEL = None  # örn: "Partnherhub" ()

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
    last_message INTEGER DEFAULT 0
)
""")
conn.commit()

# =====================
# YARDIMCI FONKSİYONLAR
# =====================
def is_admin(user_id):
    return user_id == ADMIN_ID

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cur.fetchone()

def add_user(user):
    if not get_user(user.id):
        cur.execute(
            "INSERT INTO users VALUES (?,?,?,?,?,?)",
            (
                user.id,
                user.username,
                datetime.now().isoformat(),
                None,
                0,
                0
            )
        )
        conn.commit()

def is_premium(user_id):
    user = get_user(user_id)
    if not user or not user[3]:
        return False
    return datetime.fromisoformat(user[3]) > datetime.now()

def is_banned(user_id):
    user = get_user(user_id)
    return user and user[4] == 1

def flood_ok(user_id):
    now = int(time.time())
    user = get_user(user_id)
    if not user:
        return True
    last = user[5]
    if now - last < FLOOD_SECONDS:
        return False
    cur.execute("UPDATE users SET last_message=? WHERE user_id=?", (now, user_id))
    conn.commit()
    return True

# =====================
# MENÜLER
# =====================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium")],
        [InlineKeyboardButton("📞 Destek", callback_data="support")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 İstatistik", callback_data="stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]
    ])

# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user)

    if is_banned(user.id):
        return

    await update.message.reply_text(
        "👑 Hoş geldin kral!\nMenüden devam et:",
        reply_markup=main_menu()
    )

# =====================
# BUTONLAR
# =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    if is_banned(user_id):
        return

    if q.data == "profile":
        user = get_user(user_id)
        premium = "💎 Premium" if is_premium(user_id) else "🆓 Normal"
        joined = user[2]
        await q.edit_message_text(
            f"👤 Profil\n\n"
            f"🆔 ID: {user_id}\n"
            f"⭐ Durum: {premium}\n"
            f"📅 Kayıt: {joined}",
            reply_markup=main_menu()
        )

    elif q.data == "premium":
        await q.edit_message_text(
            "💎 Premium\n\n"
            "• Özel özellikler\n"
            "• Öncelikli destek\n\n"
            "Admin ile iletişime geç.",
            reply_markup=main_menu()
        )

    elif q.data == "support":
        await q.edit_message_text(
            "📞 Destek\n\nAdmin ile iletişime geç.",
            reply_markup=main_menu()
        )

    elif q.data == "stats" and is_admin(user_id):
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE premium_until IS NOT NULL")
        premium = cur.fetchone()[0]

        await q.edit_message_text(
            f"📊 İstatistik\n\n"
            f"👥 Toplam: {total}\n"
            f"💎 Premium: {premium}",
            reply_markup=admin_menu()
        )

# =====================
# ADMIN KOMUTLARI
# =====================
async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    uid = int(context.args[0])
    days = int(context.args[1])
    until = datetime.now() + timedelta(days=days)

    cur.execute(
        "UPDATE users SET premium_until=? WHERE user_id=?",
        (until.isoformat(), uid)
    )
    conn.commit()

    await update.message.reply_text(f"✅ {uid} {days} gün premium.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = int(context.args[0])
    cur.execute("UPDATE users SET banned=1 WHERE user_id=?", (uid,))
    conn.commit()
    await update.message.reply_text("🚫 Banlandı.")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    uid = int(context.args[0])
    cur.execute("UPDATE users SET banned=0 WHERE user_id=?", (uid,))
    conn.commit()
    await update.message.reply_text("✅ Ban kaldırıldı.")

# =====================
# MESAJ
# =====================
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_banned(user_id):
        return

    if not flood_ok(user_id):
        return

    await update.message.reply_text(
        "Menüyü kullan kral 👑",
        reply_markup=main_menu()
    )

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addpremium", add_premium))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("👑 MASTER BOT ÇALIŞIYOR")
    app.run_polling()

if __name__ == "__main__":
    main()
