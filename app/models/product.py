from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)

    vendor = relationship("Vendor", back_populates="products")
    inventory = relationship(
        "Inventory",
        back_populates="product",
        uselist=False,
        cascade="all, delete"
    )
