import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from src.weather_service import know_weather
from src.ai_service import Llama_service
from src.cli import get_city_coordinates, get_match_time, print_report, get_activity

async def main():
    api_key = os.getenv('YANDEX_API_KEY')
    if not api_key:
        print('Ошибка: Не найден ключ API Яндекс. Пожалуйста, установите переменную окружения YANDEX_API_KEY.')
        return

    ai_service = Llama_service()

    place, lon, lat = await get_city_coordinates(api_key)
    match_start = get_match_time()

    weather_info = await know_weather(lon, lat, match_start)
    if not weather_info:
        print('Ошибка: Не удалось получить информацию о погоде.')
        return

    activity = get_activity()

    ai_response = ai_service.generate_answer(
        weather_info['in_moment_temp'], 
        weather_info['in_moment_rain_probability'], 
        weather_info['max_rain_probability'],
        activity,
        place
    )

    print_report(place, match_start, weather_info, ai_response)

if __name__ == "__main__":
    asyncio.run(main())
