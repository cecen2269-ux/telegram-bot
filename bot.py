import os
import sqlite3
from telegram import *
from telegram.ext import *
from telegram.constants import ChatAction, ParseMode

BOT_TOKEN = os.getenv("8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s") 
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")

# ================= DB =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
gender TEXT,
age INTEGER,
looking TEXT,
premium INTEGER DEFAULT 0,
banned INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS reports(
id INTEGER PRIMARY KEY AUTOINCREMENT,
reporter INTEGER,
reported INTEGER,
reason TEXT
)
""")

db.commit()

# ============== MATCH STATE ============
WAITING = []
CHATS = {}  # user_id: partner_id

# ================= HELPERS =================
def user(uid):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    return cur.fetchone()

def ensure_user(uid):
    if not user(uid):
        cur.execute("INSERT INTO users(id) VALUES(?)", (uid,))
        db.commit()

# ================= START =================
async def start(update: Update, ctx):
    uid = update.effective_user.id
    ensure_user(uid)

    await update.message.reply_text(
        "👋 *Anonim Sohbete Hoş Geldin!*\n\n👇 Seç:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            [
                ["🚀 Eşleş"],
                ["👤 Profil", "💎 Premium"],
                ["📜 Kurallar"]
            ],
            resize_keyboard=True
        )
    )

# ================= PROFILE =================
PROFILE_STATE = {}

async def profile(update: Update, ctx):
    await update.message.reply_text("Cinsiyetini seç:",
        reply_markup=ReplyKeyboardMarkup([["Erkek","Kadın"]], resize_keyboard=True))
    PROFILE_STATE[update.effective_user.id] = "gender"

async def profile_steps(update: Update, ctx):
    uid = update.effective_user.id
    step = PROFILE_STATE.get(uid)
    txt = update.message.text

    if step == "gender":
        cur.execute("UPDATE users SET gender=? WHERE id=?", (txt, uid))
        db.commit()
        PROFILE_STATE[uid] = "age"
        await update.message.reply_text("Yaşını gir:")
    elif step == "age":
        cur.execute("UPDATE users SET age=? WHERE id=?", (int(txt), uid))
        db.commit()
        PROFILE_STATE[uid] = "looking"
        await update.message.reply_text("Kimi arıyorsun? (Erkek/Kadın)")
    elif step == "looking":
        cur.execute("UPDATE users SET looking=? WHERE id=?", (txt, uid))
        db.commit()
        PROFILE_STATE.pop(uid)
        await update.message.reply_text("✅ Profil kaydedildi!")

# ================= MATCH =================
async def match(update: Update, ctx):
    uid = update.effective_user.id
    if uid in CHATS:
        return

    if WAITING:
        partner = WAITING.pop(0)
        CHATS[uid] = partner
        CHATS[partner] = uid

        await ctx.bot.send_message(uid, "💬 Eşleştin! Yazmaya başlayabilirsin.")
        await ctx.bot.send_message(partner, "💬 Eşleştin! Yazmaya başlayabilirsin.")
    else:
        WAITING.append(uid)
        await update.message.reply_text("⏳ Eşleşme bekleniyor...")

# ================= CHAT =================
async def relay(update: Update, ctx):
    uid = update.effective_user.id
    if uid not in CHATS:
        return

    partner = CHATS[uid]

    # medya filtresi
    if update.message.photo or update.message.video:
        if not user(uid)[4]:
            await update.message.reply_text("🚫 Medya sadece Premium!")
            return

    await ctx.bot.copy_message(
        chat_id=partner,
        from_chat_id=uid,
        message_id=update.message.message_id
    )

# ================= PAYMENT =================
async def premium(update: Update, ctx):
    await ctx.bot.send_invoice(
        chat_id=update.effective_user.id,
        title="Premium Üyelik",
        description="Sınırsız sohbet + medya",
        payload="premium",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="TRY",
        prices=[LabeledPrice("Premium", 10000)]
    )

async def successful_payment(update: Update, ctx):
    uid = update.effective_user.id
    cur.execute("UPDATE users SET premium=1 WHERE id=?", (uid,))
    db.commit()
    await update.message.reply_text("💎 Premium aktif!")

# ================= ADMIN =================
async def admin(update: Update, ctx):
    if update.effective_user.id != ADMIN_ID:
        return
    users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    await update.message.reply_text(f"👑 Admin Panel\nKullanıcı: {users}")

async def ban(update: Update, ctx):
    if update.effective_user.id != ADMIN_ID:
        return
    uid = int(ctx.args[0])
    cur.execute("UPDATE users SET banned=1 WHERE id=?", (uid,))
    db.commit()
    await update.message.reply_text(f"{uid} banlandı.")

# ================= REPORT =================
async def report(update: Update, ctx):
    uid = update.effective_user.id
    if uid not in CHATS:
        return
    partner = CHATS[uid]
    cur.execute("INSERT INTO reports(reporter,reported,reason) VALUES(?,?,?)",
                (uid, partner, "Spam"))
    db.commit()
    await update.message.reply_text("🚨 Kullanıcı raporlandı.")

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(MessageHandler(filters.Regex("👤 Profil"), profile))
app.add_handler(MessageHandler(filters.Regex("🚀 Eşleş"), match))
app.add_handler(MessageHandler(filters.TEXT & filters.User(PROFILE_STATE.keys()), profile_steps))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))
app.add_handler(PreCheckoutQueryHandler(lambda u,c: u.answer(True)))
app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

print("🤖 BOT CANLI")
app.run_polling()
