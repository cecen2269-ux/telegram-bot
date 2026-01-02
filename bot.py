from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import json
import os

# ================== AYARLAR ==================
TOKEN = "8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s" 
ADMIN_ID = 123456789  # kendi telegram ID'n

PREMIUM_FILE = "premium.json"

waiting_user = None
waiting_premium = None
active_chats = {}

# ================== PREMIUM JSON ==================
def load_premium():
    if not os.path.exists(PREMIUM_FILE):
        return set()
    with open(PREMIUM_FILE, "r") as f:
        return set(json.load(f))

def save_premium(data):
    with open(PREMIUM_FILE, "w") as f:
        json.dump(list(data), f)

premium_users = load_premium()

# ================== /start ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Sohbet Bul", callback_data="find")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium")],
        [InlineKeyboardButton("📜 Kurallar", callback_data="rules")]
    ]

    await update.message.reply_text(
        "👋 Hoş geldin!\nAnonim sohbet botu",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== BUTONLAR ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user, waiting_premium
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # -------- PROFİL --------
    if query.data == "profile":
        status = "💎 Premium" if user_id in premium_users else "👤 Normal"
        await query.message.reply_text(
            f"👤 PROFİL\n\nID: `{user_id}`\nDurum: {status}",
            parse_mode="Markdown"
        )

    # -------- KURALLAR --------
    elif query.data == "rules":
        await query.message.reply_text(
            "📜 KURALLAR\n\n"
            "1️⃣ Küfür yasak\n"
            "2️⃣ Reklam yasak\n"
            "3️⃣ +18 yasak\n"
            "4️⃣ Uymayan banlanır"
        )

    # -------- PREMIUM --------
    elif query.data == "premium":
        if user_id in premium_users:
            await query.message.reply_text("💎 Zaten premiumsun!")
        else:
            premium_users.add(user_id)
            save_premium(premium_users)
            await query.message.reply_text("🎉 Premium aktif edildi!")

    # -------- SOHBET BUL --------
    elif query.data == "find":
        if user_id in active_chats:
            await query.message.reply_text("⚠️ Zaten sohbetteyiz.")
            return

        # PREMIUM KULLANICI
        if user_id in premium_users:
            if waiting_premium is None:
                waiting_premium = user_id
                await query.message.reply_text("💎 Premium partner aranıyor...")
            else:
                partner = waiting_premium
                waiting_premium = None
                active_chats[user_id] = partner
                active_chats[partner] = user_id
                await context.bot.send_message(user_id, "💎 Premium eş bulundu!")
                await context.bot.send_message(partner, "💎 Premium eş bulundu!")

        # NORMAL KULLANICI
        else:
            if waiting_user is None:
                waiting_user = user_id
                await query.message.reply_text("⏳ Partner aranıyor...")
            else:
                partner = waiting_user
                waiting_user = None
                active_chats[user_id] = partner
                active_chats[partner] = user_id
                await context.bot.send_message(user_id, "✅ Eş bulundu!")
                await context.bot.send_message(partner, "✅ Eş bulundu!")

# ================== MESAJ AKTAR ==================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in active_chats:
        partner = active_chats[user_id]
        await context.bot.send_message(partner, update.message.text)

# ================== ADMIN ==================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    try:
        target = int(context.args[0])
        premium_users.add(target)
        save_premium(premium_users)
        await update.message.reply_text("✅ Premium verildi.")
    except:
        await update.message.reply_text("❌ Kullanım: /admin ID")

# ================== MAIN ==================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

print("🤖 Bot çalışıyor...")
app.run_polling()
