from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.logger import logger
from app.db.session import get_db
from app.models.order import Order
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import create_order_service

router = APIRouter(tags=["Orders"])


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
