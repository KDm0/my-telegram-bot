import logging
import asyncio
import requests
import math
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

# Токен бота
TOKEN = '7446071433:AAF9DsFTKjQu7wuMj8iwKaDIK-Y5a89mQhk'

# ID Лены
LENA_CHAT_ID = '1326402096'

# API-ключ для маршрутов TomTom
api_key = 'ZZoqfG4otwIX0Gg1npdoIGSo7JIaEaPC'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Координаты конечной точки (Романова 28)
DESTINATION = (55.034281, 82.917169)

# Контрольные точки
CHECKPOINTS = {
    "ГПНТБ": (55.016395, 82.945483),
    "Оперный театр": (55.030087, 82.920644),
    "ул. Советская": (55.031483, 82.916098),
    "Подъехал": (55.034479, 82.916807)
}

# Радиус для определения контрольных точек (в метрах)
RADIUS = 100

# Создаем клавиатуру
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Старт")],
        [KeyboardButton(text="🚙 Машинка", request_location=True)],
        [KeyboardButton(text="😫 Много работы")]
    ],
    resize_keyboard=True
)

# Функция для вычисления расстояния между координатами (в метрах)
def haversine(coord1, coord2):
    from math import radians, cos, sin, asin, sqrt

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371000  # радиус Земли в метрах
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return R * c

# Функция для запроса маршрута к API TomTom и расчета времени и расстояния
def get_route_duration(origin, destination):
    coordinates_str = f"{origin[0]},{origin[1]}:{destination[0]},{destination[1]}"
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{coordinates_str}/json?key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        route = data.get('routes', [])[0]
        length = route['summary']['lengthInMeters'] / 1000
        travel_time = math.ceil(route['summary']['travelTimeInSeconds'] / 60)
        return length, travel_time
    return None, None

# Функция для отправки уведомлений о контрольных точках
async def check_and_notify(current_location):
    for name, checkpoint in CHECKPOINTS.items():
        distance = haversine(current_location, checkpoint)
        if distance <= RADIUS:
            _, travel_time = get_route_duration(current_location, DESTINATION)
            arrival_time = (datetime.now() + timedelta(minutes=travel_time)).strftime('%H:%M')
            await bot.send_message(LENA_CHAT_ID, f"Дима проехал {name}, будет у тебя примерно через {travel_time} минут в {arrival_time}")

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Чем могу помочь?", reply_markup=keyboard)

# Обработчик кнопки "🚙 Машинка"
@dp.message(lambda message: message.location)
async def handle_location(message: types.Message):
    user_location = (message.location.latitude, message.location.longitude)

    # Рассчитываем маршрут и время
    length, travel_time = get_route_duration(user_location, DESTINATION)

    if length and travel_time:
        arrival_time = (datetime.now() + timedelta(minutes=travel_time)).strftime('%H:%M')

        await message.answer(f"Расстояние до Романова 28: {length:.2f} км\nВремя в пути: {travel_time} минут")

        await bot.send_location(LENA_CHAT_ID, latitude=user_location[0], longitude=user_location[1])
        await bot.send_message(
            LENA_CHAT_ID,
            f"За тобой выехал муж, расстояние от него до тебя {length:.2f} км\n"
            f"Время в пути примерно {travel_time} минут\n"
            f"Будет у тебя примерно в {arrival_time}"
        )

        # Запускаем слежение за контрольными точками (обновление каждые 5 минут)
        while True:
            await asyncio.sleep(300)  # Проверяем раз в 5 минут
            await check_and_notify(user_location)

    else:
        await message.answer("Не удалось получить маршрут. Попробуй ещё раз.")

# Обработчик кнопки "😫 Много работы"
@dp.message(lambda message: message.text == "😫 Много работы")
async def send_work_message(message: types.Message):
    await bot.send_message(LENA_CHAT_ID, "Много работы, выезжаю чуть позже 😫")
    await message.answer("Сообщение Лене, что ты задерживаешься, успешно отправлено ✅", reply_markup=keyboard)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
