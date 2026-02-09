from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.database import engine, Base
import app.models
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.user import UserCreate, UserResponse
from app.schemas.vendor import VendorCreate, VendorResponse


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
