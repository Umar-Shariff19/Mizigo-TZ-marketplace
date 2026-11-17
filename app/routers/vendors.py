from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_active_vendor
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
    description="Onboards the authenticated user as a vendor and creates their store.",
)
def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Vendor:
    existing = db.query(Vendor).filter(Vendor.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vendor already exists")

    # Onboard user as vendor if they are currently a customer
    if current_user.role == UserRole.CUSTOMER.value:
        current_user.role = UserRole.VENDOR.value

    db_vendor = Vendor(
        store_name=vendor.store_name,
        user_id=current_user.id,
        is_active=True
    )

    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)

    return db_vendor


@router.get(
    "/vendors",
    response_model=list[VendorResponse],
    summary="List vendors",
    description="Returns all active vendor store profiles.",
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
    vendor: Vendor = Depends(require_active_vendor)
) -> dict:
    vendor.subscription_plan = SubscriptionPlan.PRO.value
    vendor.subscription_expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)

    db.commit()

    return {
        "message": "Upgraded to PRO",
        "expiry": vendor.subscription_expiry
    }
