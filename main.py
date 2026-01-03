import os
from flask import Flask, request
import requests

BOT_TOKEN = "8403759105:AAEs7u9LZqQX7bWhITpFpZjG57-zz1ekG7s"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Bot çalışıyor kral 👑", 200

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "🔥 Anonim Flört Botu aktif!\nSeçimini yap 👇")
        else:
            send_message(chat_id, f"Mesaj alındı: {text}")

    return "ok", 200


def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
