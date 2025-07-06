import threading
import asyncio
import requests
from telegram import Bot, constants
from flask import Flask
import os

# === Налаштування ===
BOT_TOKEN = "7954440053:AAEQZqUMLlCM3XuIlGUpMkEmOM_od1uEBko"
CHAT_ID = 724220659
CHECK_INTERVAL = 120          # Перевірка кожні 2 хв
STATUS_INTERVAL = 600         # Повідомлення про роботу кожні 10 хв

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
            sold_out_messages.append(f"❌ Помилка перевірки *{product['name']}*: {e}")

    if available_messages:
        full_spam_text = "\n\n".join(available_messages)
        # Спам 20 разів з затримкою 3 сек (20 разів за 1 хв)
        for i in range(20):
            try:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=full_spam_text,
                    parse_mode=constants.ParseMode.MARKDOWN
                )
                await asyncio.sleep(3)
            except Exception as e:
                print(f"❌ Помилка при спамі: {e}")
                break
    else:
        # Якщо все sold out — одне звичайне повідомлення
        try:
            full_message = "\n\n".join(sold_out_messages)
            await bot.send_message(
                chat_id=CHAT_ID,
                text=full_message,
                parse_mode=constants.ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"❌ Помилка надсилання повідомлення в Telegram: {e}")

async def main_loop():
    last_status_time = 0  # час останнього повідомлення про роботу

    while True:
        await check_availability()

        current_time = asyncio.get_event_loop().time()

        if current_time - last_status_time >= STATUS_INTERVAL:
            try:
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text="🔍 Перевірка виконана, товари актуальні."
                )
                last_status_time = current_time
            except Exception as e:
                print("❌ Помилка при надсиланні статусу:", e)

        await asyncio.sleep(CHECK_INTERVAL)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# === Запуск ===
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    asyncio.run(main_loop())
