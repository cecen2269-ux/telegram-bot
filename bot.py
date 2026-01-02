from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s" 


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba 👋 Bot çalışıyor!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("Bot çalışıyor...")
app.run_polling()

