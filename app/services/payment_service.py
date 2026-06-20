from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.order import Order
from app.models.payment import Payment
from app.core.enums import OrderStatus, PaymentStatus


def process_payment_service(db: Session, payment) -> dict:
    """Simulate payment success and confirm the pending order."""

    order = db.query(Order).filter(Order.id == payment.order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Order already processed")

    db_payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        provider=payment.provider,
        status=PaymentStatus.SUCCESS.value,
        transaction_id="SIMULATED_TXN_123"
    )

    order.status = OrderStatus.CONFIRMED.value

    db.add(db_payment)
    db.commit()

    return {
        "message": "Payment successful",
        "order_status": order.status
    }
