import os
import sqlite3
import logging
from datetime import datetime, timedelta

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    LabeledPrice
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s") 
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN", "")  # Telegram payment
DB_FILE = "bot.db"

DAILY_LIMIT_FREE = 50

# ================= LOG =================
logging.basicConfig(level=logging.INFO)

# ================= DB =================
db = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    gender TEXT,
    interest TEXT,
    premium INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0,
    daily_count INTEGER DEFAULT 0,
    last_reset TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS chats (
    u1 INTEGER,
    u2 INTEGER
)
""")

db.commit()

# ================= HELPERS =================
def is_premium(uid):
    cur.execute("SELECT premium FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return r and r[0] == 1

def reset_daily(uid):
    cur.execute("SELECT last_reset FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    today = datetime.now().date().isoformat()
    if not r or r[0] != today:
        cur.execute("UPDATE users SET daily_count=0, last_reset=? WHERE user_id=?", (today, uid))
        db.commit()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    cur.execute("INSERT OR IGNORE INTO users (user_id,last_reset) VALUES (?,?)",
                (uid, datetime.now().date().isoformat()))
    db.commit()

    kb = [
        [InlineKeyboardButton("💬 Eşleş", callback_data="match")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium")]
    ]

    await update.message.reply_text(
        "👑 Hoş geldin!\nAnonim sohbet botu",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= PROFILE =================
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    cur.execute("SELECT gender,interest,premium FROM users WHERE user_id=?", (q.from_user.id,))
    g, i, p = cur.fetchone()

    txt = f"""
👤 Profil
Cinsiyet: {g or 'Belirtilmedi'}
İlgi: {i or 'Belirtilmedi'}
Premium: {'✅' if p else '❌'}
"""
    await q.message.reply_text(txt)

# ================= MATCH =================
waiting = []

async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if uid in waiting:
        await q.message.reply_text("⏳ Zaten bekliyorsun")
        return

    waiting.append(uid)
    await q.message.reply_text("⏳ Eşleşme bekleniyor...")

    if len(waiting) >= 2:
        u1 = waiting.pop(0)
        u2 = waiting.pop(0)
        cur.execute("INSERT INTO chats VALUES (?,?)", (u1, u2))
        db.commit()

        await context.bot.send_message(u1, "✅ Eşleştin! Yazabilirsin.")
        await context.bot.send_message(u2, "✅ Eşleştin! Yazabilirsin.")

# ================= MESSAGE =================
async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    cur.execute("SELECT banned FROM users WHERE user_id=?", (uid,))
    if cur.fetchone()[0]:
        return

    reset_daily(uid)

    cur.execute("SELECT daily_count FROM users WHERE user_id=?", (uid,))
    count = cur.fetchone()[0]

    if not is_premium(uid) and count >= DAILY_LIMIT_FREE:
        await update.message.reply_text("❌ Günlük limit doldu (Premium al)")
        return

    cur.execute("UPDATE users SET daily_count=daily_count+1 WHERE user_id=?", (uid,))
    db.commit()

    cur.execute("SELECT u1,u2 FROM chats WHERE u1=? OR u2=?", (uid, uid))
    r = cur.fetchone()
    if not r:
        return

    target = r[1] if r[0] == uid else r[0]
    await context.bot.send_message(target, update.message.text)

# ================= PREMIUM =================
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    kb = [[InlineKeyboardButton("💳 Premium Satın Al", callback_data="buy")]]
    await q.message.reply_text(
        "💎 Premium\n• Öncelikli eşleşme\n• Limitsiz sohbet",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    await context.bot.send_invoice(
        chat_id=q.from_user.id,
        title="Premium",
        description="Sınırsız kullanım",
        payload="premium",
        provider_token=PROVIDER_TOKEN,
        currency="TRY",
        prices=[LabeledPrice("Premium", 9900)]
    )

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur.execute("UPDATE users SET premium=1 WHERE user_id=?", (uid,))
    db.commit()
    await update.message.reply_text("💎 Premium aktif!")

# ================= ADMIN =================
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    uid = int(context.args[0])
    cur.execute("UPDATE users SET banned=1 WHERE user_id=?", (uid,))
    db.commit()
    await update.message.reply_text("✅ Banlandı")

# ================= MAIN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(match, pattern="match"))
app.add_handler(CallbackQueryHandler(profile, pattern="profile"))
app.add_handler(CallbackQueryHandler(premium, pattern="premium"))
app.add_handler(CallbackQueryHandler(buy, pattern="buy"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
app.add_handler(CommandHandler("ban", ban))

app.run_polling()
