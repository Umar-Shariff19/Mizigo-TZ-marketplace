from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory

def create_product_service(db: Session, current_user, product):

    if current_user.role != "VENDOR":
        raise HTTPException(status_code=403, detail="Only vendors allowed")

    vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()

    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor not found")

    if vendor.subscription_plan == "PRO":
        if vendor.subscription_expiry and vendor.subscription_expiry < datetime.utcnow():
            raise HTTPException(status_code=403, detail="Subscription expired")

    if vendor.subscription_plan == "FREE":
        count = db.query(Product).filter(Product.vendor_id == vendor.id).count()
        if count >= 2:
            raise HTTPException(status_code=403, detail="Free plan limit reached")

    db_product = Product(
        vendor_id=vendor.id,
        name=product.name,
        description=product.description,
        price=product.price,
    )

    db_inventory = Inventory(quantity_available=product.quantity)

    db_product.inventory = db_inventory

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return {
    "id": db_product.id,
    "name": db_product.name,
    "description": db_product.description,
    "price": db_product.price,
    "is_active": db_product.is_active,
    "vendor_id": db_product.vendor_id,
    "quantity_available": db_product.inventory.quantity_available
}