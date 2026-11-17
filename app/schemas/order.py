from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, description="Quantity must be greater than zero")

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    vendor_id: int
    quantity: int
    price_at_purchase: Decimal

    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(min_length=1, description="Order must contain at least one item")

class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_amount: Decimal
    created_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class VendorDashboardResponse(BaseModel):
    total_products: int
    total_orders: int
    total_revenue: Decimal

    model_config = ConfigDict(from_attributes=True)
