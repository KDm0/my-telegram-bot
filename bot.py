import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from geopy.distance import geodesic

# Токен бота
TOKEN = '7446071433:AAF9DsFTKjQu7wuMj8iwKaDIK-Y5a89mQhk'

# Ваш ID для тестирования
USER_CHAT_ID = '5268373934'

# Координаты пункта назначения (реальные)
destination_coords = (55.034281, 82.917169)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создаем клавиатуру
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Старт")],
        [KeyboardButton(text="🚙 Машинка")],
        [KeyboardButton(text="😫 Много работы")],
        [KeyboardButton(text="Отправить местоположение", request_location=True)]
    ],
    resize_keyboard=True
)

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Чем могу помочь?", reply_markup=keyboard)

# Обработчик кнопки "Старт"
@dp.message(lambda message: message.text == "Старт")
async def send_greeting(message: types.Message):
    await message.answer("Здравствуй! Как я могу помочь?", reply_markup=keyboard)

# Обработчик кнопки "🚙 Машинка"
@dp.message(lambda message: message.text == "🚙 Машинка")
async def send_car_message(message: types.Message):
    await bot.send_message(USER_CHAT_ID, "Я поехал 🚗")
    await message.answer("Я поехал 🚗", reply_markup=keyboard)

# Обработчик кнопки "😫 Много работы"
@dp.message(lambda message: message.text == "😫 Много работы")
async def send_work_message(message: types.Message):
    await bot.send_message(USER_CHAT_ID, "Много работы, выезжаю чуть позже 😫")
    await message.answer("Много работы, выезжаю чуть позже 😫", reply_markup=keyboard)

# Обработчик кнопки "Отправить местоположение"
@dp.message(lambda message: message.text == "Отправить местоположение" and message.location)
async def send_location(message: types.Message):
    # Получаем координаты пользователя
    user_coords = (message.location.latitude, message.location.longitude)
    
    # Вычисляем расстояние и время в пути
    distance_km = geodesic(user_coords, destination_coords).km
    time_minutes = (distance_km / 20) * 60  # Предположим, что средняя скорость 20 км/ч
    
    # Выводим отладочную информацию
    print(f"Координаты пользователя: {user_coords}")
    print(f"Координаты пункта назначения: {destination_coords}")
    print(f"Расстояние: {distance_km:.2f} км")
    print(f"Время в пути: {time_minutes:.2f} минут")
    
    # Отправляем сообщение и карту
    await bot.send_message(USER_CHAT_ID, f"Расстояние между точками: {distance_km:.2f} км\n"
                                         f"Время в пути (при скорости 20 км/ч): {time_minutes:.2f} минут")
    
    # Отправка карты
    await bot.send_location(USER_CHAT_ID, latitude=message.location.latitude, longitude=message.location.longitude)
    
    # Подтверждение для пользователя
    await message.answer(f"Ваши данные отправлены! Расстояние: {distance_km:.2f} км. Время в пути: {time_minutes:.2f} минут.", reply_markup=keyboard)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
