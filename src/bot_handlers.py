import os
import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.weather_service import place_coord, know_weather
from src.ai_service import Llama_service

router = Router()

ai_service = None

class WeatherForm(StatesGroup):
    waiting_for_city = State()
    waiting_for_time = State()
    waiting_for_activity = State()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('👋 Привет! Я твой персональный AI-Стилист.\n'
                         'Введите название города, в котором планируется мероприятие:')
    await state.set_state(WeatherForm.waiting_for_city)

@router.message(WeatherForm.waiting_for_city)
async def process_city(message: types.Message, state: FSMContext):
    city = message.text.strip()
    api_key = os.getenv('YANDEX_API_KEY')

    await message.answer('🔍 Ищу город и проверяю координаты...')

    coords = await place_coord(city, api_key)
    if coords is None:
        await message.answer('Ошибка: не удалось найти такой город(( \nПопробуйте еще разок!')
        return
    
    lon, lat = coords

    await state.update_data(city_name=city, lon=lon, lat=lat)

    await message.answer(f"📍 Город {city} успешно найден!\n\n"
                         "📅 Введите дату и время мероприятия в формате:\n"
                         "`ДД-ММ-ГГГГ ЧЧ:ММ` "
                         "(например: `25-06-2026 15:30`)")
    await state.set_state(WeatherForm.waiting_for_time)

@router.message(WeatherForm.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    time_str = message.text.strip()
    try:
        time = datetime.strptime(time_str, '%d-%m-%Y %H:%M')
    except ValueError:
        await message.answer("Неверный формат даты! Напишите еще раз в формате `ДД-ММ-ГГГГ ЧЧ:ММ`:")
        return
    
    user_data = await state.get_data()
    lon = user_data['lon']
    lat = user_data['lat']

    weather_task = asyncio.create_task(know_weather(lon, lat, time))

    await state.update_data(time=time, weather_task=weather_task)
    await message.answer('Какое мероприятие вы планируете? (Например, прогулка в парке/ночной поход в ближайшую рощу)')
    await state.set_state(WeatherForm.waiting_for_activity)

@router.message(WeatherForm.waiting_for_activity)
async def process_activity(message: types.Message, state: FSMContext):
    activity = message.text.strip()

    user_data = await state.get_data()
    city = user_data['city_name']
    time = user_data['time']
    weather_task = user_data['weather_task']

    await message.answer('⏳ Собираю сводку погоды и отправляю запрос стилисту. Это займет несколько секунд...')

    try:
        weather_info = await weather_task
    except Exception:
        weather_info = None

    if not weather_info:
        await message.answer('❌ К сожалению, не удалось получить данные о погоде с сервера Open-Meteo.')
        await state.clear()
        return
    
    ai_response = await ai_service.generate_answer(
        weather_info['in_moment_temp'], 
        weather_info['in_moment_rain_probability'], 
        weather_info['max_rain_probability'],
        activity,
        city
    )

    report = (
        f"📊 *Сводка погоды | {city} | {time.strftime('%d-%m-%Y %H:%M')}*\n"
        f"{'─'*30}\n"
        f"🌡️ Температура в это время: {weather_info['in_moment_temp']}°C\n"
        f"💧 Вероятность дождя: {weather_info['in_moment_rain_probability']}%\n"
        f"📈 Мин / Макс за сутки: {weather_info['min_temp']}°C ... {weather_info['max_temp']}°C\n"
        f"☔ Пиковый риск осадков за день: {weather_info['max_rain_probability']}%\n"
        f"{'─'*30}\n\n"
        f"💡 *Совет от AI-Стилиста:*\n{ai_response}"
    )

    await message.answer(report, parse_mode='Markdown')
    await message.answer("🔄 Чтобы начать заново, введите команду /start")
    await state.clear()