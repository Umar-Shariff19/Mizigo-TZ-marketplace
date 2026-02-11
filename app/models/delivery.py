from sqlalchemy import Column, Integer, ForeignKey, String
from app.db.database import Base

class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    partner_name = Column(String)  # e.g., DHL, FedEx
    tracking_id = Column(String, nullable=True)
    status = Column(String, default="PENDING")
