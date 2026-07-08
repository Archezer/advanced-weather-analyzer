from datetime import datetime
from src.weather_service import place_coord

def get_city_coordinates(api_key: str) -> tuple[str, float, float]:
    while True:
        place = input('Введите название города: ').strip()
        if not place:
            print('Ошибка: Название города не может быть пустым. Попробуйте снова.\n')
            continue
        
        coords = place_coord(place, api_key)
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


def print_report(place: str, match_start: datetime, weather_info: dict, ai_response: str):
    print(f'Совет от AI:\n{'='*50}\n{ai_response}')
    print(f"{'='*50}\n")
    

