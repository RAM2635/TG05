import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import os
import requests

# Загрузка переменных окружения из файла .env
load_dotenv()

# API-ключи
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
GEO_API_KEY = os.getenv('GEO_API_KEY')

# Логирование
logging.basicConfig(level=logging.INFO)

# Создание объекта бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Функция для получения информации о городе через GeoDB Cities API
def get_city_info(city_name):
    url = f"https://wft-geo-db.p.rapidapi.com/v1/geo/cities"
    headers = {
        "X-RapidAPI-Key": GEO_API_KEY,
        "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
    }
    params = {"namePrefix": city_name, "limit": 1}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return None, f"Ошибка API GeoDB: {response.status_code}, {response.json().get('message', 'Неизвестная ошибка')}"

    data = response.json()
    cities = data.get("data", [])
    if not cities:
        return None, f"Город {city_name} не найден."

    city = cities[0]
    city_info = {
        "name": city.get("city"),
        "country": city.get("country"),
        "latitude": city.get("latitude"),
        "longitude": city.get("longitude"),
        "population": city.get("population", "Нет данных")
    }
    return city_info, None


# Функция для получения погоды через OpenWeatherMap API
def get_weather(latitude, longitude):
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": WEATHER_API_KEY,
        "units": "metric",  # Используем градусы Цельсия
        "lang": "ru"  # Локализация на русский язык
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, f"Ошибка API OpenWeather: {response.status_code}, {response.json().get('message', 'Неизвестная ошибка')}"

    data = response.json()
    weather_info = {
        "description": data.get("weather", [{}])[0].get("description", "Нет данных"),
        "temperature": data.get("main", {}).get("temp", "Нет данных"),
        "feels_like": data.get("main", {}).get("feels_like", "Нет данных"),
        "humidity": data.get("main", {}).get("humidity", "Нет данных"),
        "wind_speed": data.get("wind", {}).get("speed", "Нет данных")
    }
    return weather_info, None


# Команда для получения информации о городе и погоде
@dp.message(Command("city"))
async def send_city_and_weather_info(message: types.Message):
    city_name = message.text[len("/city "):].strip()
    if not city_name:
        await message.answer("Пожалуйста, укажите название города. Пример: /city Москва")
        return

    # Получаем информацию о городе
    city_info, error = get_city_info(city_name)
    if error:
        await message.answer(error)
        return

    # Получаем погоду
    weather_info, error = get_weather(city_info["latitude"], city_info["longitude"])
    if error:
        await message.answer(error)
        return

    # Формируем ответ
    response = (
        f"Информация о городе {city_info['name']}, {city_info['country']}:\n"
        f"- Широта: {city_info['latitude']}\n"
        f"- Долгота: {city_info['longitude']}\n"
        f"- Население: {city_info['population']}\n\n"
        f"Погода:\n"
        f"- Описание: {weather_info['description'].capitalize()}\n"
        f"- Температура: {weather_info['temperature']}°C (Ощущается как {weather_info['feels_like']}°C)\n"
        f"- Влажность: {weather_info['humidity']}%\n"
        f"- Скорость ветра: {weather_info['wind_speed']} м/с"
    )
    await message.answer(response, parse_mode='Markdown')


# Команда для приветствия
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(
        "Привет! Я бот, который помогает узнать информацию о городах и их погоде.\n\n"
        "Используйте команду /city <название города>, чтобы получить данные о городе и погоде.\n\n"
        "Пример: /city Москва"
    )


# Основная функция для запуска бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
