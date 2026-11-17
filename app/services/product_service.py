from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory
from app.core.enums import SubscriptionPlan, UserRole
from app.services.image_service import delete_image_file


def create_product_service(db: Session, current_user, product) -> dict:
    """Create a product and its inventory record for an authenticated vendor."""
    image_to_clean = getattr(product, "image_url", None)

    try:
        if current_user.role != UserRole.VENDOR.value:
            raise HTTPException(status_code=403, detail="Only vendors allowed")

        vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()

        if not vendor:
            raise HTTPException(status_code=400, detail="Vendor not found")

        if not vendor.is_active:
            raise HTTPException(status_code=403, detail="Vendor account is suspended")

        if product.price <= 0:
            raise HTTPException(status_code=400, detail="Price must be positive")

        if product.quantity < 0:
            raise HTTPException(status_code=400, detail="Quantity cannot be negative")

        if vendor.subscription_plan == SubscriptionPlan.PRO.value:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if vendor.subscription_expiry and vendor.subscription_expiry < now:
                raise HTTPException(status_code=403, detail="Subscription expired")

        if vendor.subscription_plan == SubscriptionPlan.FREE.value:
            count = db.query(Product).filter(Product.vendor_id == vendor.id).count()
            if count >= 2:
                raise HTTPException(status_code=403, detail="Free plan limit reached")

        db_product = Product(
            vendor_id=vendor.id,
            name=product.name.strip(),
            description=product.description.strip() if product.description else None,
            price=product.price,
            is_active=True,
            image_url=product.image_url if hasattr(product, "image_url") else None,
        )

        db_inventory = Inventory(quantity_available=product.quantity, reserved_quantity=0)
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
            "quantity_available": db_product.inventory.quantity_available,
            "image_url": db_product.image_url,
        }
    except Exception:
        if image_to_clean:
            delete_image_file(image_to_clean, db)
        raise
