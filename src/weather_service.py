import requests
from datetime import datetime, timedelta

def place_coord(place, api_key):
    try:
        url = f'https://geocode-maps.yandex.ru/v1/?apikey={api_key}&geocode={place}&format=json'
        response = requests.get(url).json()

        feature_member_list = response['response']['GeoObjectCollection']['featureMember']
        first_match = feature_member_list[0]
        get_coord = first_match['GeoObject']['Point']['pos']

        coord_list = get_coord.split(' ')
        lon = float(coord_list[0])
        lat = float(coord_list[1])
        
        return lon, lat
    except (KeyError, IndexError) as e:
        return None

def know_weather(lon, lat, match_start):

    start_dt = match_start.strftime('%Y-%m-%d')
    end_dt = (match_start + timedelta(days=1)).strftime('%Y-%m-%d')

    url = 'https://api.open-meteo.com/v1/forecast'
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_dt,
        'end_date': end_dt,
        'hourly': 'temperature_2m,precipitation_probability',
        'timezone': 'auto'
    }

    response = requests.get(url, params=params).json()
    hourly = response['hourly']

    best_index = None
    min_diff = timedelta(days=1)
    match_day_temps = []
    match_day_rain_probs = []

    for i in range (len(hourly['time'])):
        hour_datetime = datetime.fromisoformat(hourly['time'][i])
        diff = abs(hour_datetime - match_start)

        if diff < min_diff:
            min_diff = diff
            best_index = i
        
        if hour_datetime.date() == match_start.date():
            match_day_temps.append(hourly['temperature_2m'][i])
            match_day_rain_probs.append(hourly['precipitation_probability'][i])

    calculated_weather = {
        'in_moment_temp': hourly['temperature_2m'][best_index],
        'in_moment_rain_probability': hourly['precipitation_probability'][best_index],
        'min_temp': min(match_day_temps),
        'max_temp': max(match_day_temps),
        'max_rain_probability': max(match_day_rain_probs)
    }

    return calculated_weather