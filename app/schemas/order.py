from pydantic import BaseModel
from decimal import Decimal
from typing import List

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_amount: Decimal

    class Config:
        from_attributes = True
