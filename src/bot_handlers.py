import os
import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from src.weather_service import place_coord, know_weather, coord_to_place

router = Router()
ai_service = None

class WeatherForm(StatesGroup):
    waiting_for_city = State()
    waiting_for_time = State()
    waiting_for_activity = State()

# === КНОПКИ ===

def get_location_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='📍 Поделиться локацией', request_location=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def get_time_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к выбору города", callback_data="back_to_city")],
        [InlineKeyboardButton(text='⚡ Сейчас', callback_data='time_now')]
    ])

def get_activity_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к вводу даты", callback_data="back_to_time")]
    ])

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def safe_delete(message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

async def proceed_to_activity(event: types.Message | types.CallbackQuery, state: FSMContext, time_obj: datetime, time_str: str):
    user_data = await state.get_data()
    lon, lat, city = user_data['lon'], user_data['lat'], user_data['city_name']
    main_msg_id = user_data['main_msg_id']

    await event.bot.edit_message_text(
        chat_id=event.from_user.id, message_id=main_msg_id, 
        text='⏳ Минутку, подготавливаю данные...'
    )

    weather_task = asyncio.create_task(know_weather(lon, lat, time_obj))
    await asyncio.sleep(0.4) 

    text = (f'📍 Город: {city}\n\n📅 Дата: {time_str}\n\n'
            f'🎟 Какое мероприятие вы планируете? (Например, прогулка в парке)')
    
    await event.bot.edit_message_text(
        chat_id=event.from_user.id, message_id=main_msg_id, text=text, reply_markup=get_activity_kb()
    )

    await state.update_data(time=time_obj, time_str=time_str, weather_task=weather_task)
    await state.set_state(WeatherForm.waiting_for_activity)

# === ОСНОВНЫЕ ХЭНДЛЕРЫ ===

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    main_msg = await message.answer(
        '👋 Привет! Я твой персональный AI-Стилист.\n'
        'Введите название города, в котором планируется мероприятие:',
        reply_markup=get_location_kb()
    )

    await state.update_data(main_msg_id=main_msg.message_id)
    await state.set_state(WeatherForm.waiting_for_city)

@router.message(WeatherForm.waiting_for_city, F.text | F.location)
async def process_city(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    start_msg_id = user_data['main_msg_id']
    await safe_delete(message)

    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=start_msg_id)
    except Exception:
        pass

    lon, lat, city = None, None, None

    if message.location:
        lon, lat = message.location.longitude, message.location.latitude

        status_msg = await message.answer('🔍 Определяю локацию по координатам...', reply_markup=ReplyKeyboardRemove())
        city = await coord_to_place(lon, lat, os.getenv('REVERSE_GEOCODE_API_KEY'))
        await safe_delete(status_msg)
    elif message.text:
        city = message.text.strip()

        status_msg = await message.answer('🔍 Ищу город и проверяю координаты...', reply_markup=ReplyKeyboardRemove())
        coords = await place_coord(city, os.getenv('YANDEX_API_KEY'))
        if not coords:
            await safe_delete(status_msg)
            err_msg = await message.answer('❌ Ошибка: город не найден. Попробуйте еще раз:', reply_markup=get_location_kb())
            await state.update_data(main_msg_id=err_msg.message_id)
            return
        await safe_delete(status_msg)
        lon, lat = coords, coords

    await state.update_data(city_name=city, lon=lon, lat=lat)

    main_msg = await message.answer(
        f"📍 Город {city} успешно найден!\n\n📅 Введите дату и время в формате:\n`ДД-ММ-ГГГГ ЧЧ:ММ` (например: `25-06-2026 15:30`)",
        reply_markup=get_time_kb()
    )
    await state.update_data(main_msg_id=main_msg.message_id)
    await state.set_state(WeatherForm.waiting_for_time)

@router.callback_query(F.data == "back_to_city")
async def back_to_city_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(WeatherForm.waiting_for_city)

    await callback.message.delete()
    main_msg = await callback.message.answer('👋 Введите название города:', reply_markup=get_location_kb())
    await state.update_data(main_msg_id=main_msg.message_id)
    await callback.answer()

@router.callback_query(WeatherForm.waiting_for_time, F.data == "time_now")
async def process_time_now_handler(callback: types.CallbackQuery, state: FSMContext):
    now = datetime.now()
    await proceed_to_activity(callback, state, now, f"{now.strftime('%d-%m-%Y %H:%M')} (Прямо сейчас)")
    await callback.answer()

@router.message(WeatherForm.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    time_str = message.text.strip()
    user_data = await state.get_data()
    main_msg_id = user_data['main_msg_id']
    await safe_delete(message)

    try:
        time_obj = datetime.strptime(time_str, '%d-%m-%Y %H:%M')
    except ValueError:
        await message.bot.edit_message_text(
            chat_id=message.chat.id, message_id=main_msg_id,
            text="⚠️ Неверный формат! Напишите в формате: `ДД-ММ-ГГГГ ЧЧ:ММ`:", reply_markup=get_time_kb()
        )
        return
    
    await proceed_to_activity(message, state, time_obj, time_str)

@router.callback_query(F.data == "back_to_time")
async def back_to_time_handler(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    await state.set_state(WeatherForm.waiting_for_time)
    await callback.message.edit_text(
        f"📍 Город *{user_data.get('city_name')}* успешно найден!\n\n📅 Введите дату и время мероприятия в формате:\n`ДД-ММ-ГГГГ ЧЧ:ММ`",
        reply_markup=get_time_kb()
    )
    await callback.answer()

@router.message(WeatherForm.waiting_for_activity)
async def process_activity(message: types.Message, state: FSMContext):
    activity = message.text.strip()
    user_data = await state.get_data()
    main_msg_id = user_data['main_msg_id']
    weather_task = user_data['weather_task']
    await safe_delete(message)

    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=main_msg_id,
        text='📡 Связываюсь с метеостанцией и получаю сводку погоды...'
    )

    try:
        weather_info = await weather_task
    except Exception:
        weather_info = None

    if not weather_info:
        await message.bot.edit_message_text(
            chat_id=message.chat.id, message_id=main_msg_id, text='❌ К сожалению, не удалось получить данные о погоде.'
        )
        await state.clear()
        return

    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=main_msg_id,
        text='🤖 Погода получена! Передаю данные нейросети, это займет несколько секунд...'
    )
    
    ai_response = await ai_service.generate_answer(
        weather_info['in_moment_temp'], 
        weather_info['in_moment_rain_probability'], 
        weather_info['max_rain_probability'],
        activity,
        user_data['city_name']
    )

    report = (
        f"📊 *Сводка погоды | {user_data['city_name']} | {user_data['time'].strftime('%d-%m-%Y %H:%M')}*\n"
        f"{'─'*24}\n"
        f"🌡️ Температура в это время: {weather_info['in_moment_temp']}°C\n"
        f"💧 Вероятность дождя: {weather_info['in_moment_rain_probability']}%\n"
        f"📈 Мин / Макс за сутки: {weather_info['min_temp']}°C ... {weather_info['max_temp']}°C\n"
        f"☔ Пиковый риск осадков за день: {weather_info['max_rain_probability']}%\n"
        f"{'─'*24}\n\n"
        f'💡 *Совет от AI-Стилиста для "{activity}":*\n{ai_response}'
    )

    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=main_msg_id, text=report, parse_mode="Markdown"
    )
    await state.clear()
