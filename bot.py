import sqlite3
import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ======================
# AYARLAR
# ======================
BOT_TOKEN = "ENV"  # Render env'den okunacak
ADMIN_ID = 123456789  # kendi telegram ID'n

# ======================
# LOG
# ======================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ======================
# DATABASE
# ======================
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    premium INTEGER DEFAULT 0,
    searching INTEGER DEFAULT 0,
    partner INTEGER
)
""")
db.commit()

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    db.commit()

    keyboard = [
        ["🚀 Sohbet partneri bul"],
        ["👤 Profil", "💎 Premium abonelik"],
        ["📜 Kurallar", "🌐 Language"]
    ]

    await update.message.reply_text(
        "👋 *Anonim Sohbete Hoş Geldiniz!*\n\n"
        "Anketiniz aktif.\n"
        "Sohbet etmeye başlamak için\n"
        "🚀 *Sohbet partneri bul*’a tıklayın.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        ),
        parse_mode="Markdown"
    )

# ======================
# EŞLEŞME
# ======================
async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute(
        "SELECT user_id FROM users WHERE searching=1 AND user_id!=?",
        (user_id,)
    )
    partner = cursor.fetchone()

    if partner:
        partner_id = partner[0]

        cursor.execute(
            "UPDATE users SET searching=0, partner=? WHERE user_id=?",
            (partner_id, user_id)
        )
        cursor.execute(
            "UPDATE users SET searching=0, partner=? WHERE user_id=?",
            (user_id, partner_id)
        )
        db.commit()

        await update.message.reply_text("✅ Eşleşme bulundu! Yazmaya başlayabilirsiniz.")
        await context.bot.send_message(
            chat_id=partner_id,
            text="✅ Eşleşme bulundu! Yazmaya başlayabilirsiniz."
        )
    else:
        cursor.execute(
            "UPDATE users SET searching=1 WHERE user_id=?",
            (user_id,)
        )
        db.commit()
        await update.message.reply_text("⏳ Eşleşme bekleniyor...")

# ======================
# MESAJ AKTARIM
# ======================
async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    cursor.execute(
        "SELECT partner FROM users WHERE user_id=?",
        (user_id,)
    )
    row = cursor.fetchone()

    if row and row[0]:
        await context.bot.send_message(
            chat_id=row[0],
            text=text
        )

# ======================
# MENÜ HANDLER
# ======================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🚀 Sohbet partneri bul":
        await find_partner(update, context)

    elif text == "👤 Profil":
        await update.message.reply_text("👤 Profil yakında")

    elif text == "💎 Premium abonelik":
        await update.message.reply_text(
            "💎 Premium Özellikler:\n"
            "• Öncelikli eşleşme\n"
            "• Limitsiz sohbet\n\n"
            "💳 Ödeme sonrası admin premium verir."
        )

    elif text == "📜 Kurallar":
        await update.message.reply_text(
            "📜 Kurallar:\n"
            "• Küfür yasak\n"
            "• +18 zorunlu\n"
            "• Reklam yasak"
        )

    elif text == "🌐 Language":
        await update.message.reply_text("🌐 Dil desteği yakında")

    else:
        await relay_message(update, context)

# ======================
# ADMIN
# ======================
async def premium_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        return

    target = int(context.args[0])
    cursor.execute(
        "UPDATE users SET premium=1 WHERE user_id=?",
        (target,)
    )
    db.commit()

    await update.message.reply_text("✅ Premium verildi")

# ======================
# MAIN
# ======================
def main():
    import os
    token = os.getenv("BOT_TOKEN")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("premium", premium_give))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("🤖 Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
