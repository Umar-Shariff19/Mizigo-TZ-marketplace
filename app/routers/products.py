from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Header, UploadFile
from jose import jwt, JWTError
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.enums import UserRole
from app.core.deps import get_current_user, require_active_vendor
from app.core.logger import logger
from app.db.session import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.order import VendorDashboardResponse
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.image_service import delete_image_file, save_product_image
from app.services.product_service import create_product_service

router = APIRouter(tags=["Products"])


def _product_response(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "is_active": product.is_active,
        "vendor_id": product.vendor_id,
        "quantity_available": product.inventory.quantity_available if product.inventory else 0,
        "image_url": product.image_url,
    }


@router.post(
    "/products/upload-image",
    summary="Upload product image",
    description="Uploads a product image file for the authenticated vendor and returns the relative image URL.",
)
async def upload_product_image_endpoint(
    file: UploadFile = File(...),
    vendor: Vendor = Depends(require_active_vendor),
) -> dict:
    image_url = await save_product_image(file)
    return {"image_url": image_url}


@router.post(
    "/products",
    response_model=ProductResponse,
    summary="Create product",
    description="Creates a product and inventory record for the authenticated vendor.",
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    logger.info("Creating product")
    return create_product_service(db, current_user, product)


@router.get(
    "/products",
    response_model=List[ProductResponse],
    summary="List products",
    description="Returns active marketplace products with pagination and price filtering.",
)
def list_products(
    skip: int = 0,
    limit: int = 10,
    min_price: float = 0,
    max_price: float = 1_000_000,
    search: str | None = Query(default=None, description="Search product names and descriptions."),
    sort_by: str | None = Query(default=None, description="Sort by id, name, or price."),
    sort_order: str = Query(default="asc", description="Sort direction: asc or desc."),
    db: Session = Depends(get_db)
) -> list[dict]:
    # Only return active products belonging to active vendors in public catalogue
    query = (
        db.query(Product)
        .join(Vendor, Product.vendor_id == Vendor.id)
        .options(joinedload(Product.inventory))
        .filter(Product.is_active == True, Vendor.is_active == True)
    )

    query = query.filter(Product.price >= min_price, Product.price <= max_price)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern),
            )
        )

    if sort_by:
        sort_columns = {
            "id": Product.id,
            "name": Product.name,
            "price": Product.price,
        }

        if sort_by not in sort_columns:
            raise HTTPException(status_code=400, detail="Invalid sort_by field")

        if sort_order not in {"asc", "desc"}:
            raise HTTPException(status_code=400, detail="Invalid sort_order")

        sort_column = sort_columns[sort_by]
        query = query.order_by(desc(sort_column) if sort_order == "desc" else asc(sort_column))

    products = query.offset(skip).limit(limit).all()

    return [_product_response(p) for p in products]


@router.get(
    "/products/{id}",
    response_model=ProductResponse,
    summary="Get single product",
    description="Returns details for a single product by ID.",
)
def get_product(
    id: int,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
) -> dict:
    product = (
        db.query(Product)
        .options(joinedload(Product.inventory))
        .filter(Product.id == id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # If the product is active and its vendor is active, anyone can view it
    vendor = db.query(Vendor).filter(Vendor.id == product.vendor_id).first()
    if product.is_active and (vendor and vendor.is_active):
        return _product_response(product)

    # If inactive, verify if authenticated user is the owner vendor or an admin
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user = db.query(User).filter(User.email == payload.get("sub")).first()
            if user and (user.role == UserRole.ADMIN.value or (vendor and vendor.user_id == user.id)):
                return _product_response(product)
        except JWTError:
            pass

    raise HTTPException(status_code=404, detail="Product not found")


@router.get(
    "/vendor/products",
    response_model=List[ProductResponse],
    tags=["Vendor"],
    summary="List vendor products",
    description="Returns products owned by the authenticated vendor.",
)
def list_vendor_products(
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(require_active_vendor)
) -> list[dict]:
    products = (
        db.query(Product)
        .options(joinedload(Product.inventory))
        .filter(Product.vendor_id == vendor.id)
        .all()
    )

    return [_product_response(product) for product in products]


@router.patch(
    "/vendor/products/{id}",
    response_model=ProductResponse,
    tags=["Vendor"],
    summary="Update vendor product",
    description="Updates a product owned by the authenticated vendor.",
)
def update_vendor_product(
    id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(require_active_vendor)
) -> dict:
    product = (
        db.query(Product)
        .options(joinedload(Product.inventory))
        .filter(Product.id == id, Product.vendor_id == vendor.id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product_update.price is not None and product_update.price <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")

    update_data = product_update.model_dump(exclude_unset=True)
    old_image_url = product.image_url
    for field, value in update_data.items():
        if field == "name" and value is not None:
            value = value.strip()
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    if "image_url" in update_data and old_image_url and old_image_url != product.image_url:
        delete_image_file(old_image_url, db)

    return _product_response(product)


@router.post(
    "/vendor/products/{id}/image",
    response_model=ProductResponse,
    tags=["Vendor"],
    summary="Upload or replace product image",
    description="Uploads and replaces the product image for a product owned by the authenticated vendor.",
)
async def upload_vendor_product_image(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(require_active_vendor),
) -> dict:
    product = (
        db.query(Product)
        .options(joinedload(Product.inventory))
        .filter(Product.id == id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.vendor_id != vendor.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this product")

    old_image_url = product.image_url
    image_url = await save_product_image(file)
    product.image_url = image_url

    db.commit()
    db.refresh(product)

    if old_image_url and old_image_url != image_url:
        delete_image_file(old_image_url, db)

    return _product_response(product)


@router.delete(
    "/vendor/products/{id}/image",
    response_model=ProductResponse,
    tags=["Vendor"],
    summary="Remove product image",
    description="Removes the image from a product owned by the authenticated vendor.",
)
def remove_vendor_product_image(
    id: int,
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(require_active_vendor),
) -> dict:
    product = (
        db.query(Product)
        .options(joinedload(Product.inventory))
        .filter(Product.id == id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.vendor_id != vendor.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this product")

    old_image_url = product.image_url
    product.image_url = None

    db.commit()
    db.refresh(product)

    if old_image_url:
        delete_image_file(old_image_url, db)

    return _product_response(product)


@router.delete(
    "/vendor/products/{id}",
    tags=["Vendor"],
    summary="Delete vendor product",
    description="Deletes a product owned by the authenticated vendor.",
)
def delete_vendor_product(
    id: int,
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(require_active_vendor)
) -> dict:
    product = db.query(Product).filter(Product.id == id, Product.vendor_id == vendor.id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    image_to_delete = product.image_url
    db.delete(product)
    db.commit()

    if image_to_delete:
        delete_image_file(image_to_delete, db)

    return {"message": "Product deleted"}


@router.get(
    "/vendor/dashboard",
    response_model=VendorDashboardResponse,
    tags=["Vendor"],
    summary="Vendor dashboard",
    description="Returns aggregate product, order, and revenue metrics for the authenticated vendor.",
)
def get_vendor_dashboard(
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(require_active_vendor)
) -> dict:
    total_products = db.query(Product).filter(Product.vendor_id == vendor.id).count()
    total_orders = (
        db.query(Order.id)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(OrderItem.vendor_id == vendor.id)
        .distinct()
        .count()
    )
    total_revenue = (
        db.query(func.coalesce(func.sum(OrderItem.price_at_purchase * OrderItem.quantity), 0))
        .filter(OrderItem.vendor_id == vendor.id)
        .scalar()
    )

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
    }
