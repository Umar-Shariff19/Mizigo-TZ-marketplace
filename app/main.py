from typing import List
from dotenv import load_dotenv
load_dotenv()

# ✅ FIX 1: FastAPI import added
from fastapi import FastAPI, Depends, HTTPException, Query, Request

from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.database import engine, Base

# Models
import app.models
from app.models.user import User
from app.models.vendor import Vendor
from app.models.product import Product

# Schemas
from app.schemas.user import UserCreate, UserResponse
from app.schemas.vendor import VendorCreate, VendorResponse
from app.schemas.product import ProductCreate, ProductResponse
from app.schemas.order import OrderCreate, OrderResponse
from app.schemas.payment import PaymentCreate

# Security
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user

# Services
from app.services.order_service import create_order_service
from app.services.product_service import create_product_service
from app.services.payment_service import process_payment_service

# Logging
from app.core.logger import logger

# Exceptions
from app.core.exceptions import http_exception_handler, generic_exception_handler

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload

# -------------------- INIT --------------------

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mizigo TZ API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# -------------------- RATE LIMITER --------------------

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests"}
    )

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
@limiter.limit("5/minute")
def login(
    request: Request,
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
def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "VENDOR":
        raise HTTPException(status_code=403, detail="Only vendors allowed")

    existing = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vendor already exists")

    db_vendor = Vendor(
        store_name=vendor.store_name,
        user_id=current_user.id
    )

    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)

    return db_vendor


@app.get("/vendors", response_model=list[VendorResponse])
def list_vendors(db: Session = Depends(get_db)):
    return db.query(Vendor).all()


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
    logger.info("Creating product")
    return create_product_service(db, current_user, product)


@app.get("/products", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 10,
    min_price: float = 0,
    max_price: float = 1_000_000,
    db: Session = Depends(get_db)
):
    query = db.query(Product).options(joinedload(Product.inventory))

    query = query.filter(Product.price >= min_price, Product.price <= max_price)

    products = query.offset(skip).limit(limit).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "is_active": p.is_active,
            "vendor_id": p.vendor_id,
            "quantity_available": p.inventory.quantity_available if p.inventory else 0
        }
        for p in products
    ]

# -------------------- ORDERS --------------------

@app.post("/orders", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info("Creating order")
    try:
        return create_order_service(db, current_user, order)
    except Exception as e:
        db.rollback()
        logger.error(f"Order failed: {str(e)}")
        raise e

# -------------------- PAYMENTS --------------------

@app.post("/payments")
def process_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)   # ✅ FIX 4
):
    logger.info("Processing payment")
    try:
        return process_payment_service(db, payment)
    except Exception as e:
        db.rollback()
        logger.error(f"Payment failed: {str(e)}")
        raise e