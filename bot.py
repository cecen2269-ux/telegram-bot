
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# 🔑 BOT TOKEN
TOKEN = "8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s" 
# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🚀 Sohbet partneri bul"],
        ["👤 Profil"],
        ["💎 Premium abonelik"],
        ["📜 Kurallar"],
        ["🌐 Language"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "👋 Anonim Sohbete Hoş Geldiniz!\n\n"
        "Anketiniz aktif. Sohbet etmeye başlamak için\n"
        "🚀 Sohbet partneri bul'a tıklayın.",
        reply_markup=reply_markup
    )

# Butonlara basılınca (şimdilik cevap versin diye)
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🚀 Sohbet partneri bul":
        await update.message.reply_text("🔍 Sohbet partneri aranıyor...")
    elif text == "👤 Profil":
        await update.message.reply_text("👤 Profil yakında eklenecek.")
    elif text == "💎 Premium abonelik":
        await update.message.reply_text("💎 Premium yakında.")
    elif text == "📜 Kurallar":
        await update.message.reply_text("📜 Kurallar yakında.")
    elif text == "🌐 Language":
        await update.message.reply_text("🌐 Dil seçimi yakında.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("🤖 Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()

    

