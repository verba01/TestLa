import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.models import db_helper
from crud import products as products_crud
from dotenv import load_dotenv  # Импортируем библиотеку для работы с .env
import os  # Импортируем модуль os для работы с переменными окружения

# Загружаем переменные из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=settings.bot_token)
dp = Dispatcher()

# Клавиатура с кнопкой
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Получить данные по товару")]
    ],
    resize_keyboard=True,
)


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для получения данных о товарах с Wildberries. "
        "Нажми кнопку ниже, чтобы начать.",
        reply_markup=keyboard,
    )


# Обработка кнопки "Получить данные по товару"
@dp.message(lambda message: message.text == "Получить данные по товару")
async def ask_artikul(message: types.Message):
    await message.answer("Введите артикул товара:")


# Обработка введённого артикула
@dp.message()
async def get_product_data(message: types.Message):
    try:
        artikul = int(message.text)  # Пытаемся преобразовать введённый текст в число
    except ValueError:
        await message.answer("Пожалуйста, введите корректный артикул (число).")
        return

    # Получаем данные из базы данных
    async with db_helper.session_factory() as session:
        product = await products_crud.get_product_by_artikul(session, artikul)

        # Если товар не найден в базе, получаем его с внешнего API
        if not product:
            product_data = await products_crud.get_product_by_artikul_from_api(artikul)
            if not product_data:
                await message.answer("Товар с таким артикулом не найден на Wildberries.")
                return

            # Сохраняем товар в базу данных
            product = await products_crud.create_or_update_product(session, product_data)
            await message.answer("Товар успешно добавлен в базу данных.")

        # Формируем сообщение с данными о товаре
        response = (
            f"Название: {product.name}\n"
            f"Артикул: {product.artikul}\n"
            f"Цена: {product.price} руб.\n"
            f"Рейтинг: {product.rating}\n"
            f"Количество на складах: {product.stock_quantity}"
        )
        await message.answer(response)


# Функция для запуска бота
async def start_bot():
    await dp.start_polling(bot)