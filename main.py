import threading
import asyncio
import requests
from telegram import Bot, constants
from flask import Flask
import os

# === Налаштування через змінні середовища ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))
CHECK_INTERVAL = 120          # Перевірка кожні 2 хв
STATUS_INTERVAL = 600         # Повідомлення про роботу кожні 10 хв (не використовується тут)

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

PRODUCTS = [
    {
        "name": "Inexcusable Evil",
        "product_url": "https://toskovat.com/products/inexcusable-evil",
        "json_url": "https://toskovat.com/products/inexcusable-evil.js"
    },
    {
        "name": "Last Birthday Cake",
        "product_url": "https://toskovat.com/products/last-birthday-cake",
        "json_url": "https://toskovat.com/products/last-birthday-cake.js"
    }
]

@app.route('/')
def home():
    return "✅ Бот живий!"

async def check_availability():
    available_messages = []
    sold_out_messages = []

    for product in PRODUCTS:
        try:
            response = requests.get(product["json_url"], timeout=10)
            response.raise_for_status()
            data = response.json()

            variants = data.get("variants", [])
            available = any(variant.get("available") for variant in variants)

            if available:
                available_messages.append(f"🎉 Парфум *{product['name']}* знову *в наявності!* 💥\n{product['product_url']}")
            else:
                sold_out_messages.append(f"⏳ Парфум *{product['name']}* наразі *sold out*.")

        except Exception as e:
            print(f"❌ Помилка перевірки {product['name']}: {e}")

    if available_messages:
        full_text = "\n\n".join(available_messages)
        for i in range(20):
            try:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=full_text,
                    parse_mode=constants.ParseMode.MARKDOWN
                )
                await asyncio.sleep(3)
            except Exception as e:
                print(f"❌ Помилка при надсиланні повідомлення №{i+1}: {e}")
                break

async def main_loop():
    while True:
        await check_availability()
        await asyncio.sleep(CHECK_INTERVAL)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# === Запуск ===
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    asyncio.run(main_loop())
