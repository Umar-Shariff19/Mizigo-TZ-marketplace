from collections import defaultdict
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.core.enums import OrderStatus, UserRole
from app.models.product import Product
from app.models.vendor import Vendor
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem


def create_order_service(db: Session, current_user, order) -> Order:
    """Create an order, verifying product eligibility, stock availability, and locking inventory."""
    if not order.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    # Consolidate duplicate products within the same order request
    consolidated: dict[int, int] = defaultdict(int)
    for item in order.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Item quantity must be greater than zero")
        consolidated[item.product_id] += item.quantity

    # Sort product IDs to acquire row locks in deterministic order and prevent deadlocks
    sorted_product_ids = sorted(consolidated.keys())

    total_amount = Decimal("0.00")
    order_items = []

    for product_id in sorted_product_ids:
        quantity_needed = consolidated[product_id]

        # Fetch product and verify eligibility
        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        if not product.is_active:
            raise HTTPException(status_code=400, detail=f"Product '{product.name}' is no longer active")

        # Verify vendor is active
        vendor = db.query(Vendor).filter(Vendor.id == product.vendor_id).first()
        if not vendor or not vendor.is_active:
            raise HTTPException(status_code=400, detail=f"Vendor for product '{product.name}' is suspended")

        # Lock inventory row with FOR UPDATE to prevent race conditions & overselling
        inventory = (
            db.query(Inventory)
            .filter(Inventory.product_id == product_id)
            .with_for_update()
            .first()
        )
        if not inventory or inventory.quantity_available < quantity_needed:
            available = inventory.quantity_available if inventory else 0
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product '{product.name}'. Available: {available}, requested: {quantity_needed}"
            )

        # Decrement available inventory and record reservation
        inventory.quantity_available -= quantity_needed
        if inventory.reserved_quantity is not None:
            inventory.reserved_quantity += quantity_needed

        # Calculate authoritative server-side price
        item_total = Decimal(str(product.price)) * quantity_needed
        total_amount += item_total

        order_items.append(
            OrderItem(
                product_id=product.id,
                vendor_id=product.vendor_id,
                quantity=quantity_needed,
                price_at_purchase=product.price
            )
        )

    db_order = Order(
        user_id=current_user.id,
        status=OrderStatus.PENDING.value,
        total_amount=total_amount,
        items=order_items
    )

    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    return db_order


def cancel_order_service(db: Session, current_user, order_id: int) -> Order:
    """Cancel an unpaid pending order and restore its reserved inventory."""
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role != UserRole.ADMIN.value and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this order")

    if order.status != OrderStatus.PENDING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Only PENDING orders can be cancelled. Current status: {order.status}"
        )

    # Restore inventory
    for item in order.items:
        inventory = (
            db.query(Inventory)
            .filter(Inventory.product_id == item.product_id)
            .with_for_update()
            .first()
        )
        if inventory:
            inventory.quantity_available += item.quantity
            if inventory.reserved_quantity is not None:
                inventory.reserved_quantity = max(0, inventory.reserved_quantity - item.quantity)

    order.status = OrderStatus.CANCELLED.value
    db.commit()
    db.refresh(order)

    return order
