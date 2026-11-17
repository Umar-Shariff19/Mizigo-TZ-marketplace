import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.core.enums import UserRole
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory
from tests.conftest import TestingSessionLocal

client = TestClient(app)


@pytest.fixture
def admin_setup():
    db = TestingSessionLocal()
    uid = uuid.uuid4().hex[:8]
    try:
        admin_user = User(
            email=f"admin_{uid}@mizigo.com",
            hashed_password=hash_password("adminpass123"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        customer_user = User(
            email=f"cust_{uid}@mizigo.com",
            hashed_password=hash_password("custpass123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        vendor_user = User(
            email=f"vendor_{uid}@mizigo.com",
            hashed_password=hash_password("vendorpass123"),
            role=UserRole.VENDOR.value,
            is_active=True,
        )
        db.add_all([admin_user, customer_user, vendor_user])
        db.commit()

        vendor = Vendor(
            user_id=vendor_user.id,
            store_name=f"Store_{uid}",
            is_active=True,
        )
        db.add(vendor)
        db.commit()

        product = Product(
            vendor_id=vendor.id,
            name=f"Target Product {uid}",
            price=Decimal("45.00"),
            is_active=True,
        )
        product.inventory = Inventory(quantity_available=10, reserved_quantity=0)
        db.add(product)
        db.commit()

        admin_token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
        customer_token = create_access_token(data={"sub": customer_user.email, "role": customer_user.role})
        vendor_token = create_access_token(data={"sub": vendor_user.email, "role": vendor_user.role})

        return {
            "admin_token": admin_token,
            "customer_token": customer_token,
            "vendor_token": vendor_token,
            "vendor_id": vendor.id,
            "product_id": product.id,
        }
    finally:
        db.close()


def test_customer_cannot_access_admin_routes(admin_setup) -> None:
    cust_token = admin_setup["customer_token"]

    endpoints = [
        "/admin/status",
        "/admin/users",
        "/admin/vendors",
        "/admin/orders",
    ]
    for ep in endpoints:
        res = client.get(ep, headers={"Authorization": f"Bearer {cust_token}"})
        assert res.status_code == 403
        assert "Admin access required" in res.json()["detail"]


def test_admin_can_list_users_vendors_and_orders(admin_setup) -> None:
    admin_token = admin_setup["admin_token"]

    res_users = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_users.status_code == 200
    assert isinstance(res_users.json(), list)

    res_vendors = client.get("/admin/vendors", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_vendors.status_code == 200
    assert isinstance(res_vendors.json(), list)

    res_orders = client.get("/admin/orders", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_orders.status_code == 200
    assert isinstance(res_orders.json(), list)


def test_admin_can_suspend_vendor_and_block_actions(admin_setup) -> None:
    admin_token = admin_setup["admin_token"]
    vendor_token = admin_setup["vendor_token"]
    vendor_id = admin_setup["vendor_id"]

    # Suspend vendor
    suspend_res = client.patch(
        f"/admin/vendors/{vendor_id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert suspend_res.status_code == 200
    assert suspend_res.json()["is_active"] is False

    # Verify suspended vendor cannot create products
    prod_res = client.post(
        "/products",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={"name": "Post-Suspension Item", "price": "20.00", "quantity": 5},
    )
    assert prod_res.status_code == 403
    assert "suspended" in prod_res.json()["message"].lower()


def test_admin_can_deactivate_product(admin_setup) -> None:
    admin_token = admin_setup["admin_token"]
    product_id = admin_setup["product_id"]

    deact_res = client.patch(
        f"/admin/products/{product_id}/deactivate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] is False

    # Product should now return 404 in public lookup
    pub_res = client.get(f"/products/{product_id}")
    assert pub_res.status_code == 404
