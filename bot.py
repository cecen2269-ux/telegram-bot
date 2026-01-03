import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

# ======================
# AYARLAR
# ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s" 
ADMIN_ID = 123456789  # kendi Telegram ID

users = set()
premium_users = set()

# ======================
# MENÜ
# ======================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium")],
        [InlineKeyboardButton("📞 Destek", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ======================
# /start
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)

    await update.message.reply_text(
        "👑 Hoş geldin kral!\n\nMenüden devam et:",
        reply_markup=main_menu()
    )

# ======================
# BUTONLAR
# ======================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "profile":
        status = "💎 Premium" if user_id in premium_users else "🆓 Normal"
        await query.edit_message_text(
            f"👤 Profilin\n\n"
            f"🆔 ID: {user_id}\n"
            f"⭐ Durum: {status}",
            reply_markup=main_menu()
        )

    elif query.data == "premium":
        await query.edit_message_text(
            "💎 Premium özellikler:\n\n"
            "✔ Özel komutlar\n"
            "✔ Öncelikli destek\n\n"
            "Premium almak için adminle iletişime geç.",
            reply_markup=main_menu()
        )

    elif query.data == "support":
        await query.edit_message_text(
            "📞 Destek\n\n"
            "Sorun için adminle iletişime geç.",
            reply_markup=main_menu()
        )

# ======================
# ADMIN KOMUTLARI
# ======================
async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Kullanıcı ID gir.")
        return

    uid = int(context.args[0])
    premium_users.add(uid)
    await update.message.reply_text(f"✅ {uid} premium yapıldı.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        f"📊 İstatistikler\n\n"
        f"👥 Toplam kullanıcı: {len(users)}\n"
        f"💎 Premium: {len(premium_users)}"
    )

# ======================
# NORMAL MESAJ
# ======================
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Menüyü kullan kral 👑",
        reply_markup=main_menu()
    )

# ======================
# MAIN
# ======================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addpremium", add_premium))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("👑 Bot full şekilde çalışıyor")
    app.run_polling()

if __name__ == "__main__":
    main()
