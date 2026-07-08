import os
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.telegram import TelegramAPIServer 
import src.bot_handlers as bot_handlers # Импортируем сам модуль
from src.ai_service import Llama_service # Импортируем сервис Лламы

async def main():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    ws_proxy_base = "http://127.0.0.1:1443"

    if not bot_token:
        print("Ошибка: Переменная TELEGRAM_BOT_TOKEN не задана в .env файле.")
        return

    print(f"🚀 Запуск Telegram-бота через туннель TG-WS-PROXY: {ws_proxy_base}")

    # Создаем конфигурацию сервера
    local_server = TelegramAPIServer(
        base=f"{ws_proxy_base}/bot{{token}}/{{method}}",
        file=f"{ws_proxy_base}/file/bot{{token}}/{{path}}"
    )

    # Инициализируем бота
    bot = Bot(
        token=bot_token, 
        server=local_server,
        default=DefaultBotProperties(parse_mode="Markdown")
    )
    
    # КРИТИЧЕСКИЙ ШАГ: Связываем пустую переменную в bot_handlers с реальной моделью!
    # Модель начнет загружаться в GPU фоном прямо сейчас
    print("[LOG] Инициализация фоновой загрузки нейросети в видеокарту...")
    bot_handlers.ai_service = Llama_service()
    
    dispatcher = Dispatcher()
    dispatcher.include_router(bot_handlers.router)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
