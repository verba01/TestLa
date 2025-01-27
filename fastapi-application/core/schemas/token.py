from pydantic import BaseModel
from datetime import datetime

class TokenBase(BaseModel):
    token: str

class TokenCreate(TokenBase):
    pass

class TokenRead(TokenBase):
    created_at: datetime

    class Config:
        from_attributes = True  # Ранее known as `orm_mode`