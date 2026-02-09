from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)

    quantity_available = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)

    product = relationship("Product", back_populates="inventory")
