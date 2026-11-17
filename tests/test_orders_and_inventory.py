import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.core.enums import OrderStatus, UserRole
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from tests.conftest import TestingSessionLocal

client = TestClient(app)


@pytest.fixture
def marketplace_setup():
    """Setup a vendor, a customer, and products with known stock."""
    db = TestingSessionLocal()
    uid = uuid.uuid4().hex[:8]
    try:
        # Customer
        customer = User(
            email=f"shopper_{uid}@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        db.add(customer)

        # Other customer
        other_customer = User(
            email=f"other_shopper_{uid}@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        db.add(other_customer)

        # Vendor user & store
        vendor_user = User(
            email=f"gadget_owner_{uid}@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.VENDOR.value,
            is_active=True,
        )
        db.add(vendor_user)
        db.commit()

        vendor = Vendor(
            user_id=vendor_user.id,
            store_name=f"Gadget Store {uid}",
            is_active=True,
        )
        db.add(vendor)
        db.commit()

        # Product 1: Smartphone with 5 units @ $499.00
        phone = Product(
            vendor_id=vendor.id,
            name=f"Mizigo Phone {uid}",
            price=Decimal("499.00"),
            is_active=True,
        )
        phone.inventory = Inventory(quantity_available=5, reserved_quantity=0)
        db.add(phone)

        # Product 2: Inactive Product
        inactive_prod = Product(
            vendor_id=vendor.id,
            name=f"Discontinued Earbuds {uid}",
            price=Decimal("29.00"),
            is_active=False,
        )
        inactive_prod.inventory = Inventory(quantity_available=10, reserved_quantity=0)
        db.add(inactive_prod)

        db.commit()

        cust_token = create_access_token(data={"sub": customer.email, "role": customer.role})
        other_token = create_access_token(data={"sub": other_customer.email, "role": other_customer.role})

        return {
            "customer_id": customer.id,
            "other_customer_id": other_customer.id,
            "cust_token": cust_token,
            "other_token": other_token,
            "phone_id": phone.id,
            "inactive_id": inactive_prod.id,
        }
    finally:
        db.close()


def test_create_valid_order_decrements_inventory(marketplace_setup) -> None:
    token = marketplace_setup["cust_token"]
    phone_id = marketplace_setup["phone_id"]

    res = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"product_id": phone_id, "quantity": 2}]},
    )
    assert res.status_code == 200
    order = res.json()
    assert order["status"] == OrderStatus.PENDING.value
    assert float(order["total_amount"]) == 499.00 * 2
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 2

    # Verify inventory was decremented in database
    db = TestingSessionLocal()
    try:
        inv = db.query(Inventory).filter(Inventory.product_id == phone_id).first()
        assert inv.quantity_available == 3  # 5 - 2
        assert inv.reserved_quantity == 2
    finally:
        db.close()


def test_reject_empty_and_zero_quantity_orders(marketplace_setup) -> None:
    token = marketplace_setup["cust_token"]
    phone_id = marketplace_setup["phone_id"]

    # Empty items list
    res_empty = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": []},
    )
    assert res_empty.status_code in {400, 422}

    # Zero quantity
    res_zero = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"product_id": phone_id, "quantity": 0}]},
    )
    assert res_zero.status_code in {400, 422}

    # Negative quantity
    res_neg = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"product_id": phone_id, "quantity": -3}]},
    )
    assert res_neg.status_code in {400, 422}


def test_reject_order_for_inactive_product(marketplace_setup) -> None:
    token = marketplace_setup["cust_token"]
    inactive_id = marketplace_setup["inactive_id"]

    res = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"product_id": inactive_id, "quantity": 1}]},
    )
    assert res.status_code == 400
    assert "no longer active" in res.json()["detail"].lower()


def test_reject_order_exceeding_inventory(marketplace_setup) -> None:
    token = marketplace_setup["cust_token"]
    phone_id = marketplace_setup["phone_id"]

    # Request 100 units when only 5 exist
    res = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"product_id": phone_id, "quantity": 100}]},
    )
    assert res.status_code == 400
    assert "insufficient stock" in res.json()["detail"].lower()


def test_order_cancellation_restores_inventory(marketplace_setup) -> None:
    token = marketplace_setup["cust_token"]
    phone_id = marketplace_setup["phone_id"]

    # Create order for 1 unit
    create_res = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {token}"},
        json={"items": [{"product_id": phone_id, "quantity": 1}]},
    )
    assert create_res.status_code == 200
    order_id = create_res.json()["id"]

    # Check inventory is decremented
    db = TestingSessionLocal()
    try:
        inv_before = db.query(Inventory).filter(Inventory.product_id == phone_id).first()
        qty_before = inv_before.quantity_available
    finally:
        db.close()

    # Cancel the order
    cancel_res = client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == OrderStatus.CANCELLED.value

    # Verify inventory was restored
    db = TestingSessionLocal()
    try:
        inv_after = db.query(Inventory).filter(Inventory.product_id == phone_id).first()
        assert inv_after.quantity_available == qty_before + 1
    finally:
        db.close()


def test_cross_customer_order_isolation(marketplace_setup) -> None:
    cust_token = marketplace_setup["cust_token"]
    other_token = marketplace_setup["other_token"]
    phone_id = marketplace_setup["phone_id"]

    # Customer 1 creates an order
    res = client.post(
        "/orders",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"items": [{"product_id": phone_id, "quantity": 1}]},
    )
    order_id = res.json()["id"]

    # Customer 2 attempts to fetch Customer 1's order
    view_res = client.get(
        f"/orders/{order_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert view_res.status_code == 403

    # Customer 2 attempts to cancel Customer 1's order
    cancel_res = client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert cancel_res.status_code == 403
