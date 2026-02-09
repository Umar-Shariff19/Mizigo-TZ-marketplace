from pydantic import BaseModel
from decimal import Decimal

class ProductCreate(BaseModel):
    vendor_id: int
    name: str
    description: str | None = None
    price: Decimal
    quantity: int

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: Decimal
    is_active: bool
    vendor_id: int
    quantity_available: int

    class Config:
        from_attributes = True
