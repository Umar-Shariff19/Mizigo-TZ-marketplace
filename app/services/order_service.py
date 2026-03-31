from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem

def create_order_service(db: Session, current_user, order):

    total_amount = 0
    order_items = []

    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        inventory = product.inventory

        if inventory.quantity_available < item.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")

        inventory.quantity_available -= item.quantity

        total_amount += product.price * item.quantity

        order_items.append(
            OrderItem(
                product_id=product.id,
                vendor_id=product.vendor_id,
                quantity=item.quantity,
                price_at_purchase=product.price
            )
        )

    db_order = Order(
        user_id=current_user.id,
        total_amount=total_amount
    )

    db_order.items = order_items

    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    return db_order