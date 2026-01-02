
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s"

waiting_user = None
active_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user, active_chats

    user_id = update.effective_user.id

    # resetle
    waiting_user = None
    if user_id in active_chats:
        partner = active_chats.pop(user_id)
        active_chats.pop(partner, None)

    keyboard = [
        [InlineKeyboardButton("🚀 Sohbet partneri bul", callback_data="find")],
        [InlineKeyboardButton("❌ Sohbeti bitir", callback_data="stop")]
    ]

    await update.message.reply_text(
        "👋 Hoş geldin!\nAnonim sohbet botuna hazır mısın?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
# Butonlar
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "find":
        if user_id in active_chats:
            await query.message.reply_text("⚠️ Zaten bir sohbettesin.")
            return

        if waiting_user is None:
            waiting_user = user_id
            await query.message.reply_text("⏳ Partner aranıyor...")
        else:
            partner = waiting_user
            waiting_user = None

            active_chats[user_id] = partner
            active_chats[partner] = user_id

            await context.bot.send_message(partner, "✅ Partner bulundu! Sohbet başladı.")
            await context.bot.send_message(user_id, "✅ Partner bulundu! Sohbet başladı.")

    elif query.data == "stop":
        await stop_chat(user_id, context)

# Mesaj iletme
async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in active_chats:
        partner = active_chats[user_id]
        await context.bot.send_message(partner, update.message.text)
    else:
        await update.message.reply_text("❗ Önce partner bulmalısın.")

# /next
async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await stop_chat(user_id, context)
    global waiting_user
    waiting_user = user_id
    await update.message.reply_text("🔄 Yeni partner aranıyor...")

# Sohbet bitir
async def stop_chat(user_id, context):
    if user_id in active_chats:
        partner = active_chats.pop(user_id)
        active_chats.pop(partner, None)
        await context.bot.send_message(partner, "❌ Partner sohbeti bitirdi.")
        await context.bot.send_message(user_id, "❌ Sohbet bitirildi.")
    else:
        await context.bot.send_message(user_id, "⚠️ Aktif sohbet yok.")

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("next", next_chat))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))

    print("🤖 Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()

    

