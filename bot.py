from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s" 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔞 Videolar", callback_data="videos")],
        [InlineKeyboardButton("📸 Fotoğraflar", callback_data="photos")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Menüden seç 👇", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "videos":
        await query.edit_message_text("🔞 Video bölümü yakında")
    elif query.data == "photos":
        await query.edit_message_text("📸 Fotoğraf bölümü yakında")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("Bot çalışıyor...")
app.run_polling()
