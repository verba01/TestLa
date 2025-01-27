from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import db_helper
from crud import products as products_crud
from core.schemas.product import ProductCreate, ProductRead
from typing import Annotated
from tenacity import retry, stop_after_attempt, wait_fixed
import httpx

router = APIRouter(tags=["Products"])

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def get_product_by_artikul_from_api(artikul: int):
    """
    Получает данные о товаре с внешнего API (Wildberries).
    """
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            products = data.get("data", {}).get("products", [])
            if not products:
                return None
            product_data = products[0]
            return {
                "artikul": product_data["id"],
                "name": product_data["name"],
                "price": product_data["salePriceU"] / 100,  # цена в рублях
                "rating": product_data["rating"],
                "stock_quantity": product_data["totalQuantity"],
            }
    except (httpx.HTTPError, KeyError, IndexError) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching product data from external API: {str(e)}",
        )

async def update_product_data(artikul: int, session: AsyncSession):
    """
    Обновляет данные о товаре в базе данных.
    """
    product_data = await get_product_by_artikul_from_api(artikul)
    if product_data:
        await products_crud.create_or_update_product(session, product_data)

def schedule_product_update(artikul: int, scheduler, session: AsyncSession):
    """
    Добавляет задачу в шедулер для периодического обновления данных о товаре.
    """
    scheduler.add_job(
        update_product_data,  # Функция, которая будет выполняться
        'interval',           # Интервал выполнения (каждые 30 минут)
        minutes=30,
        args=[artikul, session],  # Аргументы для функции
    )


@router.get("/product/{artikul}", response_model=ProductRead)
async def get_product_by_artikul_view(
        artikul: int,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    """
    Возвращает данные о товаре по артикулу.
    Если товара нет в базе, загружает его с внешнего API.
    """
    try:
        # Пытаемся найти товар в базе данных
        product = await products_crud.get_product_by_artikul(session, artikul)
        if not product:
            # Если товара нет в базе, загружаем его с внешнего API
            product_data = await get_product_by_artikul_from_api(artikul)
            if not product_data:
                raise HTTPException(status_code=404, detail="Товар не найден во внешнем API.")

            # Сохраняем товар в базе данных
            product = await products_crud.create_or_update_product(session, product_data)
            if not product:
                raise HTTPException(status_code=200, detail="Товар сохранен в базу данных.")

            # Возвращаем данные товара с сообщением
            return {
                "artikul": product.artikul,
                "name": product.name,
                "price": product.price,
                "rating": product.rating,
                "stock_quantity": product.stock_quantity,
                "message": "Товар добавлен в базу данных"
            }

        # Если товар уже есть в базе, возвращаем его
        return product
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )

@router.post("/subscribe/{artikul}")
async def subscribe_product(
    artikul: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request: Request,
):
    """
    Подписывает пользователя на обновление данных о товаре.
    """
    # Проверяем, существует ли товар в базе данных
    product = await products_crud.get_product_by_artikul(session, artikul)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Получаем шедулер из состояния приложения
    scheduler = request.app.state.scheduler

    # Добавляем задачу в шедулер
    schedule_product_update(artikul, scheduler, session)

    return {"message": f"Subscribed to product {artikul}"}