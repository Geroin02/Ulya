import os
from telegram.ext import Updater, MessageHandler, Filters

# Токен твоего бота
TOKEN = "8483427590:AAEHHFlai3Dr4SqisJm6IpVRvVWvFBI8Ees"

# Обработчик сообщений
def reply(update, context):
    text = update.message.text
    update.message.reply_text(f"Привет! Ты написал: {text}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))

    # Render выделяет PORT автоматически
    PORT = int(os.environ.get("PORT", 5000))

    # ⚠️ ВАЖНО: замени ulya-bot на имя своего сервиса в Render
    APP_NAME = "ulya-bot"

    # Запускаем webhook
    updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN
    )
    updater.bot.set_webhook(f"https://{APP_NAME}.onrender.com/{TOKEN}")

    updater.idle()

if __name__ == "__main__":
    main()
