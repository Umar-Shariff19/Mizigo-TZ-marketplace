from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.enums import UserRole
from app.core.deps import get_current_user
from app.core.logger import logger
from app.db.session import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.order import VendorDashboardResponse
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import create_product_service

router = APIRouter(tags=["Products"])


def _get_current_vendor(db: Session, current_user: User) -> Vendor:
    if current_user.role != UserRole.VENDOR.value:
        raise HTTPException(status_code=403, detail="Only vendors allowed")

    vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()

    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor not found")

    return vendor


def _product_response(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "is_active": product.is_active,
        "vendor_id": product.vendor_id,
        "quantity_available": product.inventory.quantity_available if product.inventory else 0,
    }


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
    description="Returns marketplace products with pagination and price filtering.",
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
    query = db.query(Product).options(joinedload(Product.inventory))

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

    return [
        _product_response(p)
        for p in products
    ]


@router.get(
    "/vendor/products",
    response_model=List[ProductResponse],
    tags=["Vendor"],
    summary="List vendor products",
    description="Returns products owned by the authenticated vendor.",
)
def list_vendor_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[dict]:
    vendor = _get_current_vendor(db, current_user)
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
    current_user: User = Depends(get_current_user)
) -> dict:
    vendor = _get_current_vendor(db, current_user)
    product = (
        db.query(Product)
        .options(joinedload(Product.inventory))
        .filter(Product.id == id, Product.vendor_id == vendor.id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

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
    current_user: User = Depends(get_current_user)
) -> dict:
    vendor = _get_current_vendor(db, current_user)
    product = db.query(Product).filter(Product.id == id, Product.vendor_id == vendor.id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

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
    current_user: User = Depends(get_current_user)
) -> dict:
    vendor = _get_current_vendor(db, current_user)

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
