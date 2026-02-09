from pydantic import BaseModel

class VendorCreate(BaseModel):
    store_name: str
    user_id: int

class VendorResponse(BaseModel):
    id: int
    store_name: str
    is_active: bool
    user_id: int

    class Config:
        from_attributes = True
