from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    store_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    subscription_plan = Column(String, default="FREE")
    subscription_expiry = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="vendor")
    products = relationship("Product", back_populates="vendor")