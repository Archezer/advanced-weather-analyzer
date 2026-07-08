from src.weather_service import place_coord, know_weather
from datetime import datetime
from src.ai_service import Llama_service
from dotenv import load_dotenv
import os

def main():
    load_dotenv()
    api_key = os.getenv('YANDEX_API_KEY')
    if not api_key:
        print('Ошибка: Не найден ключ API Яндекс. Пожалуйста, установите переменную окружения YANDEX_API_KEY.')
        return

    while True:
        place = input('Введите название города:').strip()
        if not place:
            print('Ошибка: Название города не может быть пустым. Попробуйте снова.')
            continue
        break
    
    coords = place_coord(place, api_key)
    if coords is None:
        print('Ошибка: Не удалось получить координаты для указанного города.')
        return
    lon, lat = coords

    while True:
        match_start_str = input('Введите дату и время матча в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2026-07-07 13:00):').strip()
        try:
            match_start = datetime.strptime(match_start_str, '%Y-%m-%d %H:%M')
        except ValueError:
            print('Ошибка: Неверный формат даты и времени. Попробуйте снова.')
            continue
        break
    
    weather_info = know_weather(lon, lat, match_start)
    if not weather_info:
        print('Ошибка: Не удалось получить информацию о погоде.')
        return
    
    ai_response = Llama_service()
    response = ai_response.generate_answer(
        weather_info['in_moment_temp'], 
        weather_info['in_moment_rain_probability'], 
        weather_info['max_rain_probability'],
        place
        )

    print(f"\n{'='*50}")
    print(f'\nСовет от AI:\n{response}\n')
    print(response)
    print(f"\n{'='*50}")
    
    print(f'ПОГОДА В ГОРОДЕ {place.upper()} НА МОМЕНТ НАЧАЛА МАТЧА ({match_start.strftime("%Y-%m-%d %H:%M")}):')
    print(f'Температура: {weather_info["in_moment_temp"]}°C')
    print(f'Вероятность осадков: {weather_info["in_moment_rain_probability"]}%')
    print(f'Минимальная температура за день: {weather_info["min_temp"]}°C')
    print(f'Максимальная температура за день: {weather_info["max_temp"]}°C')
    print(f'Максимальная вероятность осадков за день: {weather_info["max_rain_probability"]}%')

if __name__ == "__main__":
    main()


