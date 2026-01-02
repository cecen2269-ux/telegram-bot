from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "BURAYA_TOKENİN"

waiting_premium = None
waiting_normal = None
active_chats = {}

profiles = {}
premium_users = set()
premium_only_mode = set()  # Premium odayı açanlar

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Sohbet Bul", callback_data="find")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium")],
        [InlineKeyboardButton("🎯 Premium Oda", callback_data="premium_room")],
        [InlineKeyboardButton("📜 Kurallar", callback_data="rules")]
    ]
    await update.message.reply_text(
        "👋 Hoş geldin!\nAnonim Sohbet Botu",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# BUTONLAR
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_premium, waiting_normal
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
            "4️⃣ Uymayanlar banlanır"
        )
        return

    # PREMIUM SATIN AL (DEMO)
    if query.data == "premium":
        if user_id in premium_users:
            await query.message.reply_text("💎 Zaten Premiumsun!")
        else:
            premium_users.add(user_id)
            await query.message.reply_text(
                "🎉 PREMIUM AKTİF!\n\n"
                "✅ Öncelikli eşleşme\n"
                "✅ Premium oda\n"
                "✅ Premium rozet"
            )
        return

    # PREMIUM ODA (SADECE PREMIUM)
    if query.data == "premium_room":
        if user_id not in premium_users:
            await query.message.reply_text("❌ Premium olmadan giremezsin.")
            return

        if user_id in premium_only_mode:
            premium_only_mode.remove(user_id)
            await query.message.reply_text("❌ Premium oda KAPALI.")
        else:
            premium_only_mode.add(user_id)
            await query.message.reply_text("🎯 Premium oda AÇIK!\nSadece premiumlarla eşleşirsin.")
        return

    # PROFİL
    if query.data == "profile":
        badge = " 💎" if user_id in premium_users else ""
        profile = profiles.get(user_id)

        if not profile:
            profiles[user_id] = {"step": "name"}
            await query.message.reply_text("👤 İsmini yaz:")
        else:
            await query.message.reply_text(
                f"👤 Profil{badge}\n\n"
                f"İsim: {profile['name']}\n"
                f"Yaş: {profile['age']}\n"
                f"Bio: {profile['bio']}"
            )
        return

    # SOHBET BUL
    if query.data == "find":
        if user_id in active_chats:
            await query.message.reply_text("⚠️ Zaten sohbetteyiz.")
            return

        is_premium = user_id in premium_users
        wants_premium_only = user_id in premium_only_mode

        # PREMIUM ODA
        if wants_premium_only:
            if waiting_premium and waiting_premium != user_id:
                partner = waiting_premium
                waiting_premium = None
            else:
                waiting_premium = user_id
                await query.message.reply_text("🎯 Premium partner aranıyor...")
                return

        # NORMAL PREMIUM ÖNCELİK
        elif is_premium:
            if waiting_premium:
                partner = waiting_premium
                waiting_premium = None
            elif waiting_normal:
                partner = waiting_normal
                waiting_normal = None
            else:
                waiting_premium = user_id
                await query.message.reply_text("💎 Öncelikli eşleşme aranıyor...")
                return

        # NORMAL KULLANICI
        else:
            if waiting_premium:
                partner = waiting_premium
                waiting_premium = None
            elif waiting_normal:
                partner = waiting_normal
                waiting_normal = None
            else:
                waiting_normal = user_id
                await query.message.reply_text("⏳ Partner aranıyor...")
                return

        active_chats[user_id] = partner
        active_chats[partner] = user_id

        await context.bot.send_message(partner, "✅ Partner bulundu! Sohbet başladı.")
        await query.message.reply_text("✅ Partner bulundu! Sohbet başladı.")

# MESAJLAR
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # PROFİL KAYIT
    if user_id in profiles and "step" in profiles[user_id]:
        step = profiles[user_id]["step"]

        if step == "name":
            profiles[user_id]["name"] = text
            profiles[user_id]["step"] = "age"
            await update.message.reply_text("🎂 Yaşını yaz:")
            return

        if step == "age":
            if not text.isdigit():
                await update.message.reply_text("❌ Sayı gir.")
                return
            profiles[user_id]["age"] = text
            profiles[user_id]["step"] = "bio"
            await update.message.reply_text("📝 Bio yaz:")
            return

        if step == "bio":
            profiles[user_id]["bio"] = text
            profiles[user_id].pop("step")
            await update.message.reply_text("✅ Profil tamamlandı!")
            return

    # SOHBET AKTAR
    if user_id in active_chats:
        partner = active_chats[user_id]
        badge = "💎 " if user_id in premium_users else ""
        await context.bot.send_message(partner, f"{badge}{text}")

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    print("🤖 Bot çalışıyor")
    app.run_polling()

if __name__ == "__main__":
    main()

    
         


            
    