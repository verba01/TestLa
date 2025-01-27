import logging
import asyncio
import uvicorn

from core.config import settings
from api import router as api_router
from create_fastapi_app import create_app
from bot import start_bot  # Импортируем функцию для запуска бота

# Настройка логирования
logging.basicConfig(
    format=settings.logging.log_format,
)

# Создание FastAPI приложения
main_app = create_app(
    create_custom_static_urls=True,
)

# Подключение роутеров
main_app.include_router(
    api_router,
)

# Функция для запуска бота и FastAPI
async def run_app():
    # Запуск бота в фоновом режиме
    bot_task = asyncio.create_task(start_bot())

    # Запуск FastAPI
    config = uvicorn.Config(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
    server = uvicorn.Server(config)
    await server.serve()

    # Ожидание завершения задач
    await bot_task

if __name__ == "__main__":
    asyncio.run(run_app())