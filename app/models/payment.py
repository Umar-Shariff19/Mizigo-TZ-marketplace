from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime
from datetime import datetime
from app.db.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)

    status = Column(String, default="PENDING")
    provider = Column(String)  # razorpay, stripe, etc.
    transaction_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
