import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.db.database import Base
from app.main import app
from app.models.user import User
from app.models.vendor import Vendor
from tests.conftest import TestingSessionLocal

client = TestClient(app)


def test_public_registration_cannot_escalate_to_admin() -> None:
    """Ensure public registration cannot assign the ADMIN role."""
    response = client.post(
        "/users",
        json={
            "email": "malicious_admin@mizigo.com",
            "password": "strongpassword123",
            "role": "ADMIN",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == UserRole.CUSTOMER.value, "Public user was able to assign ADMIN role!"


def test_public_registration_cannot_escalate_to_vendor() -> None:
    """Ensure public registration cannot assign the VENDOR role directly."""
    response = client.post(
        "/users",
        json={
            "email": "attempted_vendor@mizigo.com",
            "password": "strongpassword123",
            "role": "VENDOR",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == UserRole.CUSTOMER.value, "Public user was able to assign VENDOR role!"


def test_duplicate_registration_rejected() -> None:
    """Ensure duplicate email registration returns a 400 error."""
    client.post(
        "/users",
        json={"email": "duplicate_user@mizigo.com", "password": "password123"},
    )
    dup_res = client.post(
        "/users",
        json={"email": "duplicate_user@mizigo.com", "password": "password456"},
    )
    assert dup_res.status_code == 400
    assert "Email already registered" in dup_res.json()["detail"]


def test_invalid_login_credentials() -> None:
    """Ensure wrong password or unknown user is rejected with 401."""
    # Unknown user
    res1 = client.post("/login", data={"username": "nobody@mizigo.com", "password": "wrong"})
    assert res1.status_code == 401

    # Existing user, wrong password
    client.post("/users", json={"email": "legit_user@mizigo.com", "password": "correctpassword"})
    res2 = client.post("/login", data={"username": "legit_user@mizigo.com", "password": "wrongpassword"})
    assert res2.status_code == 401


def test_inactive_user_cannot_access_protected_endpoints() -> None:
    """Ensure deactivated accounts are rejected with 403."""
    db = TestingSessionLocal()
    try:
        inactive_user = User(
            email="inactive_user@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.CUSTOMER.value,
            is_active=False,
        )
        db.add(inactive_user)
        db.commit()
    finally:
        db.close()

    token = create_access_token(data={"sub": "inactive_user@mizigo.com", "role": "CUSTOMER"})
    response = client.get("/orders/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert "Inactive user account" in response.json()["detail"]


def test_malformed_and_expired_jwt_tokens() -> None:
    """Ensure malformed and expired tokens are rejected."""
    # Malformed token
    res1 = client.get("/orders/me", headers={"Authorization": "Bearer not.a.valid.jwt"})
    assert res1.status_code == 401

    # Expired token
    expired_payload = {
        "sub": "someuser@mizigo.com",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    res2 = client.get("/orders/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res2.status_code == 401


def test_admin_cli_bootstrap() -> None:
    """Test administrative provisioning CLI script."""
    from app.scripts.create_admin import bootstrap_admin

    bootstrap_admin("system_admin@mizigo.com", "AdminSuperPassword2026!")

    db = TestingSessionLocal()
    try:
        admin_user = db.query(User).filter(User.email == "system_admin@mizigo.com").first()
        assert admin_user is not None
        assert admin_user.role == UserRole.ADMIN.value
        assert admin_user.is_active is True
    finally:
        db.close()

    # Verify admin can log in and access /admin/status
    login_res = client.post(
        "/login",
        data={"username": "system_admin@mizigo.com", "password": "AdminSuperPassword2026!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    status_res = client.get("/admin/status", headers={"Authorization": f"Bearer {token}"})
    assert status_res.status_code == 200
    assert status_res.json() == {"status": "ok"}


def test_unauthorized_access_to_vendor_endpoints() -> None:
    """Ensure unauthenticated users and customers without vendor onboarding are rejected."""
    # 1. Unauthenticated requests to vendor endpoints must return 401
    assert client.get("/vendor/dashboard").status_code == 401
    assert client.post("/vendors", json={"store_name": "Ghost Store"}).status_code == 401
    assert client.post("/vendors/upgrade").status_code == 401
    assert client.get("/vendor/products").status_code == 401

    # 2. Create and authenticate as a normal CUSTOMER in the database
    db = TestingSessionLocal()
    try:
        user = User(
            email="regular_customer@mizigo.com",
            hashed_password=hash_password("customerpass123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        db.add(user)
        db.commit()
    finally:
        db.close()

    customer_token = create_access_token(
        data={"sub": "regular_customer@mizigo.com", "role": UserRole.CUSTOMER.value}
    )
    headers = {"Authorization": f"Bearer {customer_token}"}

    # 3. Customer must be rejected from vendor-only endpoints with 403 "Only vendors allowed"
    dash_res = client.get("/vendor/dashboard", headers=headers)
    assert dash_res.status_code == 403
    assert dash_res.json()["detail"] == "Only vendors allowed"

    upgrade_res = client.post("/vendors/upgrade", headers=headers)
    assert upgrade_res.status_code == 403
    assert upgrade_res.json()["detail"] == "Only vendors allowed"

    products_res = client.get("/vendor/products", headers=headers)
    assert products_res.status_code == 403
    assert products_res.json()["detail"] == "Only vendors allowed"


def test_customer_to_vendor_onboarding_flow() -> None:
    """Verify that a customer successfully transitions to a vendor, creating a vendor profile
    and gaining access to vendor endpoints without requiring re-login."""
    # 1. Register new customer
    reg_res = client.post(
        "/users",
        json={"email": "candidate_seller@mizigo.com", "password": "sellerpass123"},
    )
    assert reg_res.status_code == 200
    assert reg_res.json()["role"] == UserRole.CUSTOMER.value

    # 2. Authenticate as customer via JWT
    token = create_access_token(
        data={"sub": "candidate_seller@mizigo.com", "role": UserRole.CUSTOMER.value}
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Verify customer cannot access vendor dashboard before onboarding
    pre_dash = client.get("/vendor/dashboard", headers=headers)
    assert pre_dash.status_code == 403
    assert pre_dash.json()["detail"] == "Only vendors allowed"

    # 4. Perform vendor onboarding via POST /vendors
    onboard_res = client.post(
        "/vendors",
        json={"store_name": "Sunrise Electronics"},
        headers=headers,
    )
    assert onboard_res.status_code == 200
    onboard_data = onboard_res.json()
    assert onboard_data["store_name"] == "Sunrise Electronics"
    assert onboard_data["is_active"] is True
    vendor_id = onboard_data["id"]
    user_id = onboard_data["user_id"]

    # 5. Verify database state: role updated to VENDOR and Vendor record created
    db = TestingSessionLocal()
    try:
        db_user = db.query(User).filter(User.email == "candidate_seller@mizigo.com").first()
        assert db_user is not None
        assert db_user.role == UserRole.VENDOR.value
        assert db_user.id == user_id

        db_vendor = db.query(Vendor).filter(Vendor.user_id == db_user.id).first()
        assert db_vendor is not None
        assert db_vendor.id == vendor_id
        assert db_vendor.store_name == "Sunrise Electronics"
        assert db_vendor.is_active is True
    finally:
        db.close()

    # 6. Verify existing token now authorizes access to vendor endpoints immediately
    dash_res = client.get("/vendor/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_products"] == 0
    assert dash_data["total_orders"] == 0
    assert Decimal(str(dash_data["total_revenue"])) == Decimal("0.00")

    products_res = client.get("/vendor/products", headers=headers)
    assert products_res.status_code == 200
    assert products_res.json() == []

    upgrade_res = client.post("/vendors/upgrade", headers=headers)
    assert upgrade_res.status_code == 200
    assert upgrade_res.json()["message"] == "Upgraded to PRO"

    # 7. Duplicate onboarding attempt should be rejected with 400
    dup_res = client.post(
        "/vendors",
        json={"store_name": "Duplicate Sunrise Store"},
        headers=headers,
    )
    assert dup_res.status_code == 400
    assert dup_res.json()["detail"] == "Vendor already exists"
