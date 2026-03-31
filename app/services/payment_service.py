from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.order import Order
from app.models.payment import Payment

def process_payment_service(db: Session, payment):

    order = db.query(Order).filter(Order.id == payment.order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "PENDING":
        raise HTTPException(status_code=400, detail="Order already processed")

    db_payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        provider=payment.provider,
        status="SUCCESS",
        transaction_id="SIMULATED_TXN_123"
    )

    order.status = "CONFIRMED"

    db.add(db_payment)
    db.commit()

    return {
        "message": "Payment successful",
        "order_status": order.status
    }