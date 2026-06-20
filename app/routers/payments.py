from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.logger import logger
from app.db.session import get_db
from app.models.order import Order
from app.models.user import User
from app.schemas.payment import PaymentCreate
from app.services.payment_service import process_payment_service

router = APIRouter(tags=["Payments"])


@router.post(
    "/payments",
    summary="Process payment",
    description="Processes a simulated payment for an order owned by the authenticated user.",
)
def process_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    logger.info("Processing payment")
    try:
        order = db.query(Order).filter(Order.id == payment.order_id).first()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to process payment for this order")

        return process_payment_service(db, payment)
    except Exception as exc:
        db.rollback()
        logger.error(f"Payment failed: {str(exc)}")
        raise exc
