import asyncio
import aiohttp

# Используем новый HTTP-порт 10809 из ваших настроек
PROXY_URL = "http://127.0.0.1:10809"


async def check_weather_http_proxy():
    timeout = aiohttp.ClientTimeout(total=10, connect=5)

    # URL Open-Meteo для проверки погоды в Москве
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": "55.75",
        "longitude": "37.61",
        "current": "temperature_2m",
    }

    print(f"Проверяю работу через HTTP-прокси {PROXY_URL}...")

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Передаем прокси напрямую в метод .get()
            async with session.get(
                url, params=params, proxy=PROXY_URL
            ) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)

                    temp = data["current"]["temperature_2m"]
                    unit = data.get("current_units", {}).get(
                        "temperature_2m", "°C"
                    )

                    print(
                        "🎉 ПОБЕДА! Через встроенный HTTP-прокси всё заработало идеально!"
                    )
                    print(f"Текущая температура в Москве: {temp}{unit}")
                else:
                    print(
                        f"❌ Ошибка! Сервер вернул код ответа: {response.status}"
                    )
                    text = await response.text()
                    print(text[:200])

    except aiohttp.ClientConnectorError as e:
        print(
            f"❌ Ошибка подключения: {e}. Проверьте, применились ли настройки в клиенте."
        )
    except Exception as e:
        print(f"❌ Ошибка обработки ответа: {e}")


if __name__ == "__main__":
    asyncio.run(check_weather_http_proxy())
