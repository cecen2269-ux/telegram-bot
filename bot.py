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
profiles = {}      # user_id: {name, age, bio}
premium_users = set()

# START
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

# BUTONLAR
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_user, active_chats
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # KURALLAR
    if query.data == "rules":
        await query.message.reply_text(
            "📜 KURALLAR\n\n"
            "1️⃣ Küfür yasak\n"
            "2️⃣ Reklam yasak\n"
            "3️⃣ +18 yasak\n"
            "4️⃣ Ban sebebi"
        )
        return

    # PROFİL
    if query.data == "profile":
        profile = profiles.get(user_id)
        if not profile:
            profiles[user_id] = {"step": "name"}
            await query.message.reply_text("👤 İsmini yaz:")
        else:
            badge = " 💎" if user_id in premium_users else ""
            await query.message.reply_text(
                f"👤 Profil{badge}\n\n"
                f"İsim: {profile['name']}\n"
                f"Yaş: {profile['age']}\n"
                f"Bio: {profile['bio']}"
            )
        return

    # PREMIUM
    if query.data == "premium":
        if user_id in premium_users:
            await query.message.reply_text("💎 Zaten premiumsun!")
        else:
            premium_users.add(user_id)
            await query.message.reply_text("🎉 Premium aktif edildi!")
        return

    # SOHBET BUL
    if query.data == "find":
        if user_id in active_chats:
            await query.message.reply_text("⚠️ Zaten sohbetteyiz.")
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
                partner, "✅ Partner bulundu! Sohbet başladı."
            )
            await query.message.reply_text(
                "✅ Partner bulundu! Sohbet başladı."
            )

# MESAJLAR
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # PROFİL OLUŞTURMA ADIMLARI
    if user_id in profiles and "step" in profiles[user_id]:
        step = profiles[user_id]["step"]

        if step == "name":
            profiles[user_id]["name"] = text
            profiles[user_id]["step"] = "age"
            await update.message.reply_text("🎂 Yaşını yaz:")
            return

        if step == "age":
            if not text.isdigit():
                await update.message.reply_text("❌ Sayı gir!")
                return
            profiles[user_id]["age"] = text
            profiles[user_id]["step"] = "bio"
            await update.message.reply_text("📝 Kısa bio yaz:")
            return

        if step == "bio":
            profiles[user_id]["bio"] = text
            profiles[user_id].pop("step")
            await update.message.reply_text("✅ Profil oluşturuldu!")
            return

    # SOHBET AKTAR
    if user_id in active_chats:
        partner = active_chats[user_id]
        badge = "💎 " if user_id in premium_users else ""
        await context.bot.send_message(
            partner, f"{badge}{text}"
        )

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("🤖 Bot aktif")
    app.run_polling()

if __name__ == "__main__":
    main()
