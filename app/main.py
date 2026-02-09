from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.database import engine, Base
import app.models
from app.models.user import User
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory
from app.schemas.user import UserCreate, UserResponse
from app.schemas.vendor import VendorCreate, VendorResponse
from app.schemas.product import ProductCreate, ProductResponse



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
