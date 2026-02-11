from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.database import engine, Base
import app.models
from app.models.user import User
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.delivery import Delivery
from app.schemas.user import UserCreate, UserResponse
from app.schemas.vendor import VendorCreate, VendorResponse
from app.schemas.product import ProductCreate, ProductResponse
from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.payment import PaymentCreate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mizigo TZ API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/vendors", response_model=VendorResponse)
def create_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
    db_vendor = Vendor(
        store_name=vendor.store_name,
        user_id=vendor.user_id
    )
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor


@app.get("/vendors", response_model=list[VendorResponse])
def list_vendors(db: Session = Depends(get_db)):
    return db.query(Vendor).all()

@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(
        vendor_id=product.vendor_id,
        name=product.name,
        description=product.description,
        price=product.price,
    )

    db_inventory = Inventory(
        quantity_available=product.quantity
    )

    db_product.inventory = db_inventory

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return ProductResponse(
        id=db_product.id,
        name=db_product.name,
        description=db_product.description,
        price=db_product.price,
        is_active=db_product.is_active,
        vendor_id=db_product.vendor_id,
        quantity_available=db_product.inventory.quantity_available
    )

@app.get("/products", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()

    return [
        ProductResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            price=p.price,
            is_active=p.is_active,
            vendor_id=p.vendor_id,
            quantity_available=p.inventory.quantity_available
        )
        for p in products
    ]

@app.post("/orders", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
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
        user_id=order.user_id,
        total_amount=total_amount
    )

    db_order.items = order_items
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    return db_order

@app.post("/payments")
def process_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
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

    return {"message": "Payment successful", "order_status": order.status}