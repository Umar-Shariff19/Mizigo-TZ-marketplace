from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.deps import require_admin_user
from app.db.session import get_db
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.order import OrderResponse
from app.schemas.product import ProductResponse
from app.schemas.user import UserResponse
from app.schemas.vendor import VendorResponse

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin_user)],
)


@router.get(
    "/status",
    summary="Admin status",
    description="Confirms that the authenticated user has access to the admin module.",
)
def admin_status() -> dict:
    return {"status": "ok"}


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="Admin list users",
    description="Returns all users. Requires ADMIN role.",
)
def list_admin_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).all()


@router.get(
    "/vendors",
    response_model=list[VendorResponse],
    summary="Admin list vendors",
    description="Returns all vendors. Requires ADMIN role.",
)
def list_admin_vendors(db: Session = Depends(get_db)) -> list[Vendor]:
    return db.query(Vendor).all()


@router.get(
    "/orders",
    response_model=list[OrderResponse],
    summary="Admin list orders",
    description="Returns all orders. Requires ADMIN role.",
)
def list_admin_orders(db: Session = Depends(get_db)) -> list[Order]:
    return db.query(Order).all()


@router.patch(
    "/vendors/{id}/suspend",
    response_model=VendorResponse,
    summary="Suspend vendor",
    description="Suspends a vendor account by marking it inactive. Requires ADMIN role.",
)
def suspend_vendor(id: int, db: Session = Depends(get_db)) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.id == id).first()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor.is_active = False
    db.commit()
    db.refresh(vendor)

    return vendor


@router.patch(
    "/products/{id}/deactivate",
    response_model=ProductResponse,
    summary="Deactivate product",
    description="Deactivates a product. Requires ADMIN role.",
)
def deactivate_product(id: int, db: Session = Depends(get_db)) -> dict:
    product = (
        db.query(Product)
        .options(joinedload(Product.inventory))
        .filter(Product.id == id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False
    db.commit()
    db.refresh(product)

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "is_active": product.is_active,
        "vendor_id": product.vendor_id,
        "quantity_available": product.inventory.quantity_available if product.inventory else 0,
    }
