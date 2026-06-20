from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.enums import SubscriptionPlan, UserRole
from app.db.session import get_db
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorResponse

router = APIRouter(tags=["Vendors"])


@router.post(
    "/vendors",
    response_model=VendorResponse,
    summary="Create vendor profile",
    description="Creates a vendor store for the authenticated vendor user.",
)
def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Vendor:
    if current_user.role != UserRole.VENDOR.value:
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


@router.get(
    "/vendors",
    response_model=list[VendorResponse],
    summary="List vendors",
    description="Returns all vendor store profiles.",
)
def list_vendors(db: Session = Depends(get_db)) -> list[Vendor]:
    return db.query(Vendor).all()


@router.post(
    "/vendors/upgrade",
    summary="Upgrade vendor subscription",
    description="Upgrades the authenticated vendor to the PRO subscription plan for 30 days.",
)
def upgrade_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    if current_user.role != UserRole.VENDOR.value:
        raise HTTPException(status_code=403, detail="Only vendors can upgrade")

    vendor = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()

    if not vendor:
        raise HTTPException(status_code=400, detail="Vendor not found")

    vendor.subscription_plan = SubscriptionPlan.PRO.value
    vendor.subscription_expiry = datetime.utcnow() + timedelta(days=30)

    db.commit()

    return {
        "message": "Upgraded to PRO",
        "expiry": vendor.subscription_expiry
    }
