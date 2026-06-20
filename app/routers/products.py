from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.core.logger import logger
from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse
from app.services.product_service import create_product_service

router = APIRouter(tags=["Products"])


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
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "is_active": p.is_active,
            "vendor_id": p.vendor_id,
            "quantity_available": p.inventory.quantity_available if p.inventory else 0
        }
        for p in products
    ]
