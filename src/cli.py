from datetime import datetime
from src.weather_service import place_coord

async def get_city_coordinates(api_key: str) -> tuple[str, float, float]:
    while True:
        print('Введите название города: ')
        place = input().strip()
        if not place:
            print('Ошибка: Название города не может быть пустым. Попробуйте снова.\n')
            continue
        
        coords = await place_coord(place, api_key)
        if coords is None:
            print('Ошибка: Не удалось получить координаты для указанного города. Попробуйте снова.\n')
            continue
        
        lon, lat = coords
        return place, lon, lat


def get_match_time() -> datetime:
    while True:
        match_start_str = input('Введите дату и время матча в формате ГГГГ-ММ-ДД ЧЧ:ММ (например, 2026-07-07 13:00): ').strip()
        try:
            return datetime.strptime(match_start_str, '%Y-%m-%d %H:%M')
        except ValueError:
            print('Ошибка: Неверный формат даты и времени. Попробуйте снова.\n')

def get_activity() -> str:
    activity = input('Введите мероприятие, к которому вам необходимо подобрать одежду: ').strip()
    return activity


def print_report(place, match_start, weather_info, ai_response):
    print(f"{'='*50}\n")
    print(f"Сводка погоды | {place} | {match_start.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")
    print(f"Температура в указанное время: {weather_info['in_moment_temp']}°C")
    print(f"Вероятность осадков в указанное время: {weather_info['in_moment_rain_probability']}%")
    print(f"Минимум / Максимум за день: {weather_info['min_temp']}°C ... {weather_info['max_temp']}°C")
    print(f"Максимальный риск дождя за день: {weather_info['max_rain_probability']}%")
    print(f"{'='*50}\n")

    print(f"\nСовет от AI:\n{'='*50}\n{ai_response}")
    print(f"{'='*50}\n")
    

