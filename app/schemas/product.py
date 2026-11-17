from pydantic import BaseModel, ConfigDict, Field, field_validator
from decimal import Decimal


def _validate_image_url(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    if ".." in v or "\\" in v:
        raise ValueError("Path traversal sequences are not allowed in image_url")
    if v.startswith("/uploads/") and not v.startswith("/uploads/products/"):
        raise ValueError("Local image_url must point to /uploads/products/")
    return v


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(gt=0, decimal_places=2)
    quantity: int = Field(ge=0)
    image_url: str | None = None

    @field_validator("image_url")
    @classmethod
    def validate_img(cls, v: str | None) -> str | None:
        return _validate_image_url(v)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    is_active: bool | None = None
    image_url: str | None = None

    @field_validator("image_url")
    @classmethod
    def validate_img(cls, v: str | None) -> str | None:
        return _validate_image_url(v)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: Decimal
    is_active: bool
    vendor_id: int
    quantity_available: int
    image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
