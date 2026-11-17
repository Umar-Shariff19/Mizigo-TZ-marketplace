from pydantic import BaseModel, ConfigDict

class VendorCreate(BaseModel):
    store_name: str

class VendorResponse(BaseModel):
    id: int
    store_name: str
    is_active: bool
    user_id: int

    model_config = ConfigDict(from_attributes=True)

