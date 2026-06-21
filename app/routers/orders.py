from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.enums import UserRole
from app.core.logger import logger
from app.db.session import get_db
from app.models.order import Order
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import create_order_service

router = APIRouter(tags=["Orders"])


@router.get(
    "/orders/me",
    response_model=list[OrderResponse],
    summary="List my orders",
    description="Returns orders owned by the authenticated user.",
)
def list_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[Order]:
    return db.query(Order).filter(Order.user_id == current_user.id).all()


@router.get(
    "/orders/{id}",
    response_model=OrderResponse,
    summary="Get order",
    description="Returns an order if owned by the authenticated user, or if the user is an ADMIN.",
)
def get_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Order:
    order = db.query(Order).filter(Order.id == id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role != UserRole.ADMIN.value and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")

    return order


@router.post(
    "/orders",
    response_model=OrderResponse,
    summary="Create order",
    description="Creates an order for the authenticated user and reserves stock by decrementing inventory.",
)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Order:
    logger.info("Creating order")
    try:
        return create_order_service(db, current_user, order)
    except Exception as exc:
        db.rollback()
        logger.error(f"Order failed: {str(exc)}")
        raise exc
