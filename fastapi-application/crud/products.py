import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.models.pair import Product
from sqlalchemy.exc import SQLAlchemyError


async def get_product_by_artikul_from_api(artikul: int):
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("products", [])
            if not products:
                return None
            # Возвращаем данные первого товара
            product_data = products[0]
            return {
                "artikul": product_data["id"],
                "name": product_data["name"],
                "price": product_data["salePriceU"] / 100,  # цена в рублях
                "rating": product_data["rating"],
                "stock_quantity": product_data["totalQuantity"],
            }
        else:
            return None


# async def create_product(session: AsyncSession, product_data):
#     new_product = Product(
#         artikul=product_data['artikul'],
#         name=product_data['name'],
#         price=product_data['price'],
#         rating=product_data['rating'],
#         stock_quantity=product_data['stock_quantity'],
#     )
#     session.add(new_product)
#     try:
#         await session.commit()
#         return new_product
#     except SQLAlchemyError as e:
#         await session.rollback()
#         raise Exception(f"Error saving product to DB: {str(e)}")

async def create_or_update_product(session: AsyncSession, product_data: dict):
    # Проверяем, существует ли товар с таким артикулом
    result = await session.execute(
        select(Product).filter(Product.artikul == product_data["artikul"])
    )
    product = result.scalar_one_or_none()

    if product:
        # Если товар найден, обновляем его данные
        product.name = product_data["name"]
        product.price = product_data["price"]
        product.rating = product_data["rating"]
        product.stock_quantity = product_data["stock_quantity"]
    else:
        # Если товара нет в базе, создаём новый
        product = Product(
            artikul=product_data["artikul"],
            name=product_data["name"],
            price=product_data["price"],
            rating=product_data["rating"],
            stock_quantity=product_data["stock_quantity"]
        )
        session.add(product)

    # Сохраняем изменения в базе данных
    await session.commit()


async def get_product_by_artikul(session: AsyncSession, artikul: int):
    result = await session.execute(select(Product).filter(Product.artikul == artikul))
    return result.scalar_one_or_none()


async def get_all_products(session: AsyncSession):
    result = await session.execute(select(Product))
    return result.scalars().all()
