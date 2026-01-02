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

TOKEN="8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s" 
waiting_user = None
active_chats = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Sohbet partneri bul", callback_data="find")],
        [InlineKeyboardButton("❌ Sohbeti bitir", callback_data="stop")]
    ]

    await update.message.reply_text(
        "👋 Anonim Sohbete Hoş Geldin!\n\nBaşlamak için butona tıkla 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Butonlar
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user, active_chats

    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Sohbet bul
    if query.data == "find":
        if user_id in active_chats:
            await query.message.reply_text("⚠️ Zaten bir sohbetteyiz.")
            return

        if waiting_user is None:
            waiting_user = user_id
            await query.message.reply_text("⏳ Partner aranıyor...")
        else:
            partner = waiting_user
            waiting_user = None

            active_chats[user_id] = partner
            active_chats[partner] = user_id

            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Partner bulundu! Sohbete başlayabilirsiniz."
            )
            await context.bot.send_message(
                chat_id=partner,
                text="✅ Partner bulundu! Sohbete başlayabilirsiniz."
            )

    # Sohbet bitir
    elif query.data == "stop":
        if user_id in active_chats:
            partner = active_chats.pop(user_id)
            active_chats.pop(partner, None)

            await context.bot.send_message(
                chat_id=partner,
                text="❌ Karşı taraf sohbeti bitirdi."
            )
            await query.message.reply_text("❌ Sohbeti bitirdin.")
        else:
            await query.message.reply_text("ℹ️ Aktif sohbet yok.")

# Mesaj iletme
async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in active_chats:
        partner = active_chats[user_id]
        await context.bot.send_message(
            chat_id=partner,
            text=update.message.text
        )

# Main
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, relay))

    print("🤖 Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
