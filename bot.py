from telegram import *
from telegram.ext import *
import time

TOKEN = "8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s" 

# ------------------ VERİLER ------------------
users = {}
waiting = []
chats = {}
daily_limit = {}
premium_users = set()
banned = set()

DAILY_FREE_LIMIT = 5

bad_words = ["küfür", "orospu", "sik"]

# ------------------ START ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid in banned:
        await update.message.reply_text("🚫 Bu bottan yasaklandın.")
        return

    users.setdefault(uid, {
        "gender": None,
        "age": None,
        "looking": None,
        "bio": "",
        "premium": False
    })

    kb = [
        [InlineKeyboardButton("🚀 Sohbet Bul", callback_data="find")],
        [InlineKeyboardButton("👤 Profil", callback_data="profile")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium")],
        [InlineKeyboardButton("📜 Kurallar", callback_data="rules")]
    ]

    await update.message.reply_text(
        "🔥 *Anonim Flört Botu*\n\nSeçimini yap:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

# ------------------ BUTTONS ------------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "rules":
        await q.message.reply_text(
            "📜 *Kurallar*\n\n"
            "• Küfür yasak\n"
            "• Reklam yasak\n"
            "• +18 içerik yasak\n"
            "• Rahatsız eden banlanır",
            parse_mode="Markdown"
        )

    elif q.data == "premium":
        premium_users.add(uid)
        users[uid]["premium"] = True
        await q.message.reply_text("💎 Premium aktif! Limitsiz sohbet.")

    elif q.data == "profile":
        u = users[uid]
        text = (
            "📝 *Profil*\n\n"
            f"👤 Cinsiyet: {u['gender']}\n"
            f"🎂 Yaş: {u['age']}\n"
            f"❤️ Arıyor: {u['looking']}\n"
            f"🧠 Bio: {u['bio'] or 'Yok'}"
        )

        kb = [
            [InlineKeyboardButton("👩 Kadın", callback_data="g_k"),
             InlineKeyboardButton("👨 Erkek", callback_data="g_e")],
            [InlineKeyboardButton("18", callback_data="a_18"),
             InlineKeyboardButton("19+", callback_data="a_19")],
            [InlineKeyboardButton("❤️ Erkek", callback_data="l_e"),
             InlineKeyboardButton("❤️ Kadın", callback_data="l_k")],
            [InlineKeyboardButton("✏️ Bio Yaz", callback_data="bio")],
            [InlineKeyboardButton("✅ Kaydet", callback_data="save")]
        ]

        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif q.data.startswith("g_"):
        users[uid]["gender"] = "Kadın" if "k" in q.data else "Erkek"
        await q.message.reply_text("✅ Cinsiyet kaydedildi")

    elif q.data.startswith("a_"):
        users[uid]["age"] = "18" if "18" in q.data else "19+"
        await q.message.reply_text("✅ Yaş kaydedildi")

    elif q.data.startswith("l_"):
        users[uid]["looking"] = "Erkek" if "e" in q.data else "Kadın"
        await q.message.reply_text("✅ Aradığı kaydedildi")

    elif q.data == "bio":
        await q.message.reply_text("✏️ Bio yaz:")
        context.user_data["bio"] = True

    elif q.data == "save":
        u = users[uid]
        if None in (u["gender"], u["age"], u["looking"]):
            await q.message.reply_text("❌ Profil eksik!")
        else:
            await q.message.reply_text("✅ Profil kaydedildi!")

    elif q.data == "find":
        await find_partner(q, context)

# ------------------ SOHBET ------------------
async def find_partner(q, context):
    uid = q.from_user.id

    if not users[uid]["premium"]:
        count = daily_limit.get(uid, 0)
        if count >= DAILY_FREE_LIMIT:
            await q.message.reply_text("⛔ Günlük limit doldu. Premium al.")
            return
        daily_limit[uid] = count + 1

    if uid in chats:
        await q.message.reply_text("⚠️ Zaten sohbettesin.")
        return

    for other in waiting:
        if users[other]["gender"] == users[uid]["looking"]:
            waiting.remove(other)
            chats[uid] = other
            chats[other] = uid

            await context.bot.send_message(other, "✅ Partner bulundu!")
            await q.message.reply_text("✅ Partner bulundu!")
            return

    waiting.append(uid)
    await q.message.reply_text("⏳ Partner aranıyor...")

# ------------------ MESAJLAR ------------------
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if context.user_data.get("bio"):
        users[uid]["bio"] = text[:50]
        context.user_data["bio"] = False
        await update.message.reply_text("✅ Bio kaydedildi")
        return

    if uid not in chats:
        return

    for w in bad_words:
        if w in text.lower():
            await update.message.reply_text("🚫 Küfür yasak!")
            return

    await context.bot.send_message(chats[uid], text)

# ------------------ KOMUTLAR ------------------
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in chats:
        other = chats.pop(uid)
        chats.pop(other, None)
        await context.bot.send_message(other, "❌ Partner ayrıldı")
        await update.message.reply_text("❌ Sohbet bitti")

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop(update, context)
    fake = type("obj", (), {"from_user": update.effective_user, "message": update.message})
    await find_partner(fake, context)

# ------------------ MAIN ------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("next", next_chat))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

    print("🔥 Bot aktif")
    app.run_polling()

if __name__ == "__main__":
    main()
