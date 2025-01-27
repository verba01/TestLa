# core/schemas/product.py
from pydantic import BaseModel

class ProductCreate(BaseModel):
    artikul: int
    name: str
    price: float
    rating: float
    stock_quantity: int

class ProductRead(BaseModel):
    artikul: int
    name: str
    price: float
    rating: float
    stock_quantity: int

    class Config:
        orm_mode = True
