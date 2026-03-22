from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.session import get_db
from app.db.database import engine, Base

# Models
import app.models
from app.models.user import User
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.delivery import Delivery

# Schemas
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.vendor import VendorCreate, VendorResponse
from app.schemas.product import ProductCreate, ProductResponse
from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.payment import PaymentCreate

# Security
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mizigo TZ API")


# -------------------- HEALTH --------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------- USERS --------------------

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)

    db_user = User(
        email=user.email,
        hashed_password=hashed,
        role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


# -------------------- AUTH --------------------

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == form_data.username).first()

    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": db_user.email, "role": db_user.role}
    )

    return {"access_token": token, "token_type": "bearer"}

# -------------------- VENDORS --------------------

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

from datetime import timedelta

@app.post("/vendors/upgrade")
def upgrade_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    if current_user.role != "VENDOR":
        raise HTTPException(status_code=403, detail="Only vendors can upgrade")

    vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()

    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor not found")

    vendor.subscription_plan = "PRO"
    vendor.subscription_expiry = datetime.utcnow() + timedelta(days=30)

    db.commit()

    return {
        "message": "Upgraded to PRO",
        "expiry": vendor.subscription_expiry
    }


# -------------------- PRODUCTS --------------------

@app.post("/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 1️⃣ Role check
    if current_user.role != "VENDOR":
        raise HTTPException(status_code=403, detail="Only vendors can create products")

    # 2️⃣ Get vendor linked to user
    vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()

    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor profile not found")

    # 3️⃣ Check subscription expiry (for PRO)
    if vendor.subscription_plan == "PRO":
        if vendor.subscription_expiry and vendor.subscription_expiry < datetime.utcnow():
            raise HTTPException(status_code=403, detail="Subscription expired")

    # 4️⃣ FREE plan limit
    if vendor.subscription_plan == "FREE":
        product_count = db.query(Product).filter(Product.vendor_id == vendor.id).count()
        if product_count >= 2:
            raise HTTPException(status_code=403, detail="Free plan limit reached (max 2 products)")

    # 5️⃣ Create product
    db_product = Product(
        vendor_id=vendor.id,
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


# -------------------- ORDERS --------------------

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


# -------------------- PAYMENTS --------------------

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

    return {
        "message": "Payment successful",
        "order_status": order.status
    }

