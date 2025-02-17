import logging
import asyncio
import requests
import math
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputMediaGeo
from aiogram.filters import Command

# Токен бота и ID Лены
TOKEN = '7446071433:AAF9DsFTKjQu7wuMj8iwKaDIK-Y5a89mQhk'
LENA_CHAT_ID = '1326402096'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# API ключ TomTom
api_key = 'ZZoqfG4otwIX0Gg1npdoIGSo7JIaEaPC'

# Координаты контрольных точек
checkpoint_names = ["ГПНТБ", "Оперный", "ул. Советскую", "Подъехал"]
checkpoints = [
    (55.016395, 82.945483),  # ГПНТБ
    (55.030087, 82.920644),  # Оперный
    (55.031483, 82.916098),  # Поворот на Советскую
    (55.034479, 82.916807)   # Подъехал
]

# Точка назначения
destination = (55.034281, 82.917169)

# Создаем клавиатуру
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Старт")],
        [KeyboardButton(text="🚙 Машинка", request_location=True)],
        [KeyboardButton(text="😫 Много работы")]
    ],
    resize_keyboard=True
)

# Функция для расчета расстояния между двумя точками
def calculate_distance(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    radius = 6371  # Радиус Земли в км

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c

# Функция для получения маршрута и времени в пути
def get_route_info(start, end):
    coordinates_str = f"{start[0]},{start[1]}:{end[0]},{end[1]}"
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{coordinates_str}/json?key={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        route = data.get('routes', [])[0]
        length = route['summary']['lengthInMeters'] / 1000
        travel_time = math.ceil(route['summary']['travelTimeInSeconds'] / 60)
        return length, travel_time
    else:
        return None, None

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Чем могу помочь?", reply_markup=keyboard)

# Обработчик кнопки "Старт"
@dp.message(lambda message: message.text == "Старт")
async def send_greeting(message: types.Message):
    await message.answer("Здравствуй! Как я могу помочь?", reply_markup=keyboard)

# Обработчик кнопки "😫 Много работы"
@dp.message(lambda message: message.text == "😫 Много работы")
async def send_work_message(message: types.Message):
    await bot.send_message(LENA_CHAT_ID, "Много работы, выезжаю чуть позже 😫")
    await message.answer("Сообщение Лене, что ты задерживаешься, успешно отправлено ✅", reply_markup=keyboard)

# Обработчик кнопки "🚙 Машинка" с геолокацией
@dp.message(lambda message: message.location)
async def track_location(message: types.Message):
    start_location = (message.location.latitude, message.location.longitude)

    # Получаем информацию о маршруте
    length, travel_time = get_route_info(start_location, destination)

    if length and travel_time:
        arrival_time = (types.datetime.datetime.now() + types.timedelta(minutes=travel_time)).strftime("%H:%M")

        # Отправляем карту и информацию Лене
        await bot.send_location(LENA_CHAT_ID, message.location.latitude, message.location.longitude)
        await bot.send_message(
            LENA_CHAT_ID,
            f"За тобой выехал муж, расстояние до тебя {length:.2f} км\n"
            f"Время в пути примерно {travel_time} минут\n"
            f"Будет у тебя примерно в {arrival_time}"
        )

        # Отправляем подтверждение тебе
        await message.answer("Сообщение Лене успешно отправлено ✅", reply_markup=keyboard)

        # Запускаем отслеживание контрольных точек
        await track_checkpoints(start_location)

# Функция для отслеживания контрольных точек
async def track_checkpoints(start_location):
    reached_points = set()

    while len(reached_points) < len(checkpoints):
        for i, checkpoint in enumerate(checkpoints):
            if i not in reached_points:
                current_distance = calculate_distance(start_location, checkpoint)
                if current_distance <= 0.1:  # Если в пределах 100 метров
                    length, travel_time = get_route_info(checkpoint, destination)
                    arrival_time = (types.datetime.datetime.now() + types.timedelta(minutes=travel_time)).strftime("%H:%M")

                    message = f"Дима проехал {checkpoint_names[i]}, будет у тебя примерно через {travel_time} минут в {arrival_time}"
                    if i == len(checkpoints) - 1:
                        message = "Дима подъехал, ждёт тебя внизу."

                    await bot.send_message(LENA_CHAT_ID, message)
                    reached_points.add(i)

        await asyncio.sleep(10)  # Проверяем каждую 10 секунд

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
