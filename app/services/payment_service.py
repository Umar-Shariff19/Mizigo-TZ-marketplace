import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.order import Order
from app.models.payment import Payment
from app.core.enums import OrderStatus, PaymentStatus


def process_payment_service(db: Session, payment) -> dict:
    """Process simulated payment atomically and confirm the pending order."""

    order = (
        db.query(Order)
        .filter(Order.id == payment.order_id)
        .with_for_update()
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == OrderStatus.CONFIRMED.value:
        raise HTTPException(status_code=400, detail="Order is already paid")

    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(status_code=400, detail=f"Cannot pay for order with status: {order.status}")

    existing_payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id, Payment.status == PaymentStatus.SUCCESS.value)
        .first()
    )
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already completed for this order")

    txn_id = f"SIM_TXN_{order.id}_{uuid.uuid4().hex[:12].upper()}"

    db_payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        provider=payment.provider if hasattr(payment, "provider") and payment.provider else "simulated",
        status=PaymentStatus.SUCCESS.value,
        transaction_id=txn_id,
    )

    order.status = OrderStatus.CONFIRMED.value

    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    db.refresh(order)

    return {
        "message": "Payment successful",
        "order_status": order.status,
        "transaction_id": db_payment.transaction_id,
        "amount": float(db_payment.amount)
    }
