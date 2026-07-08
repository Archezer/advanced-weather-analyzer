import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Импортируем наши асинхронные сервисы
from src.weather_service import place_coord, know_weather
from src.ai_service import Llama_service

load_dotenv()

YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

if not YANDEX_API_KEY or not TELEGRAM_TOKEN:
    raise ValueError("Пожалуйста, убедитесь, что YANDEX_API_KEY и TELEGRAM_TOKEN указаны в файле .env")

# Инициализация бота и диспетчера aiogram 3
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
ai_service = Llama_service()

# Описываем шаги диалога (Машина состояний)
class WeatherForm(StatesGroup):
    waiting_for_city = State()
    waiting_for_time = State()
    waiting_for_activity = State()

# Команда /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() # Сбрасываем старые состояния, если они были
    await message.answer("Привет! Я помогу тебе подобрать идеальную одежду по погоде.\n\nВведите название города:")
    await state.set_state(WeatherForm.waiting_for_city)

# Шаг 1: Получаем город
@dp.message(WeatherForm.waiting_for_city)
async def process_city(message: types.Message, state: FSMContext):
    city = message.text.strip()
    if not city:
        await message.answer("Название города не может быть пустым. Попробуйте еще раз:")
        return

    await message.answer("🔎 Ищу координаты города, подождите...")
    coords = await place_coord(city, YANDEX_API_KEY)
    
    if coords is None:
        await message.answer("Не удалось найти такой город. Проверьте название и введите снова:")
        return

    lon, lat = coords
    # Сохраняем промежуточные данные в контекст пользователя
    await state.update_data(city=city, lon=lon, lat=lat)
    
    await message.answer("Отлично! Теперь введите дату и время мероприятия в формате:\n`ГГГГ-ММ-ДД ЧЧ:ММ` (например: `2026-07-07 13:00`)", parse_mode="Markdown")
    await state.set_state(WeatherForm.waiting_for_time)

# Шаг 2: Получаем время
@dp.message(WeatherForm.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    time_str = message.text.strip()
    try:
        match_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
    except ValueError:
        await message.answer("Неверный формат даты. Напишите в виде: `ГГГГ-ММ-ДД ЧЧ:ММ`", parse_mode="Markdown")
        return

    await state.update_data(match_time=match_time)
    await message.answer("Какое мероприятие планируется? (например: прогулка в парке, футбольный матч, свидание, пробежка):")
    await state.set_state(WeatherForm.waiting_for_activity)

# Шаг 3: Получаем активность и выводим результат
@dp.message(WeatherForm.waiting_for_activity)
async def process_activity(message: types.Message, state: FSMContext):
    activity = message.text.strip()
    
    # Достаем все сохраненные данные пользователя из памяти бота
    user_data = await state.get_data()
    city = user_data['city']
    lon = user_data['lon']
    lat = user_data['lat']
    match_time = user_data['match_time']

    await message.answer("🌤️ Запрашиваю прогноз погоды...")
    weather_info = await know_weather(lon, lat, match_time)
    
    if not weather_info:
        await message.answer("Произошла ошибка при получении погоды. Попробуйте начать заново с команды /start")
        await state.clear()
        return

    await message.answer("🤖 ИИ-стилист обдумывает ваш образ (это может занять около 20 секунд)...")
    
    # Вызываем асинхронную генерацию
    ai_response = await ai_service.generate_answer_async(
        temp=weather_info['in_moment_temp'],
        rain=weather_info['in_moment_rain_probability'],
        max_rain=weather_info['max_rain_probability'],
        activity=activity,
        place=city
    )

    # Формируем итоговый отчет
    report = (
        f"<b>Сводка погоды | {city} | {match_time.strftime('%Y-%m-%d %H:%M')}</b>\n"
        f"{'='*30}\n"
        f"🌡️ Температура в это время: {weather_info['in_moment_temp']}°C\n"
        f"💧 Вероятность осадков: {weather_info['in_moment_rain_probability']}%\n"
        f"📊 Диапазон за день: {weather_info['min_temp']}°C ... {weather_info['max_temp']}°C\n"
        f"☔ Макс. риск дождя за день: {weather_info['max_rain_probability']}%\n"
        f"{'='*30}\n\n"
        f"<b>👔 Совет от AI-Стилиста:</b>\n{ai_response}"
    )

    await message.answer(report, parse_mode="HTML")
    
    # Очищаем состояние, чтобы пользователь мог начать новый запрос
    await state.clear()
    await message.answer("\nЧтобы составить новый образ, просто напишите /start")

# Точка входа для запуска бота
async def main():
    print("[Система] Бот успешно запущен и слушает сервера Telegram...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[Система] Бот остановлен.")
