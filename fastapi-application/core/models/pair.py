from sqlalchemy import UniqueConstraint, String, Numeric, Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime
from .base import Base
from .mixins.int_id_pk import IntIdPkMixin


class Product(IntIdPkMixin, Base):
    __tablename__ = 'products'

    artikul:Mapped[int] = mapped_column(Integer,nullable = False,unique=True)
    name:Mapped[str]=mapped_column(String, nullable=False)
    price:Mapped[float]=mapped_column(Numeric(10,2), nullable=False)
    rating:Mapped[float]=mapped_column(Numeric(3,2), nullable=False)
    stock_quantity:Mapped[float]=mapped_column(Integer, nullable=False)
    created_at:Mapped[datetime]=mapped_column(default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("artikul"),
    )