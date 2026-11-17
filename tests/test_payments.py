import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.core.enums import OrderStatus, PaymentStatus, UserRole
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.payment import Payment
from tests.conftest import TestingSessionLocal

client = TestClient(app)


@pytest.fixture
def payment_setup():
    db = TestingSessionLocal()
    uid = uuid.uuid4().hex[:8]
    try:
        user = User(
            email=f"payer_{uid}@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        db.add(user)

        intruder = User(
            email=f"intruder_{uid}@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        db.add(intruder)
        db.commit()

        # Vendor & Product
        vuser = User(email=f"pay_vendor_{uid}@mizigo.com", hashed_password=hash_password("pass"), role=UserRole.VENDOR.value, is_active=True)
        db.add(vuser)
        db.commit()

        vendor = Vendor(user_id=vuser.id, store_name=f"Pay Store {uid}", is_active=True)
        db.add(vendor)
        db.commit()

        prod = Product(vendor_id=vendor.id, name=f"Book {uid}", price=Decimal("15.50"), is_active=True)
        prod.inventory = Inventory(quantity_available=20, reserved_quantity=0)
        db.add(prod)
        db.commit()

        # Create Order for user
        order = Order(user_id=user.id, status=OrderStatus.PENDING.value, total_amount=Decimal("31.00"))
        db.add(order)
        db.commit()
        db.refresh(order)

        user_token = create_access_token(data={"sub": user.email, "role": user.role})
        intruder_token = create_access_token(data={"sub": intruder.email, "role": intruder.role})

        return {
            "user_token": user_token,
            "intruder_token": intruder_token,
            "order_id": order.id,
            "user_id": user.id,
        }
    finally:
        db.close()


def test_successful_simulated_payment(payment_setup) -> None:
    token = payment_setup["user_token"]
    order_id = payment_setup["order_id"]

    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"order_id": order_id, "provider": "simulated_card"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Payment successful"
    assert data["order_status"] == OrderStatus.CONFIRMED.value
    assert "transaction_id" in data
    assert data["amount"] == 31.00

    # Verify payment record in DB
    db = TestingSessionLocal()
    try:
        pay = db.query(Payment).filter(Payment.order_id == order_id).first()
        assert pay is not None
        assert pay.status == PaymentStatus.SUCCESS.value
        assert pay.transaction_id == data["transaction_id"]
    finally:
        db.close()


def test_intruder_cannot_pay_for_another_users_order(payment_setup) -> None:
    intruder_token = payment_setup["intruder_token"]
    order_id = payment_setup["order_id"]

    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {intruder_token}"},
        json={"order_id": order_id, "provider": "simulated_card"},
    )
    assert res.status_code == 403
    assert "Not authorized" in res.json()["detail"]


def test_cannot_pay_order_twice(payment_setup) -> None:
    token = payment_setup["user_token"]
    order_id = payment_setup["order_id"]

    # First payment succeeds
    res1 = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"order_id": order_id, "provider": "simulated_card"},
    )
    assert res1.status_code == 200

    # Second payment is rejected
    res2 = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"order_id": order_id, "provider": "simulated_card"},
    )
    assert res2.status_code == 400
    assert "already paid" in res2.json()["detail"].lower() or "already processed" in res2.json()["detail"].lower()


def test_cannot_pay_cancelled_order() -> None:
    db = TestingSessionLocal()
    uid = uuid.uuid4().hex[:8]
    try:
        user = User(
            email=f"cancelled_payer_{uid}@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        db.add(user)
        db.commit()

        order = Order(user_id=user.id, status=OrderStatus.CANCELLED.value, total_amount=Decimal("50.00"))
        db.add(order)
        db.commit()
        db.refresh(order)
        order_id = order.id
    finally:
        db.close()

    token = create_access_token(data={"sub": user.email, "role": user.role})
    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}"},
        json={"order_id": order_id, "provider": "simulated_card"},
    )
    assert res.status_code == 400
    assert "cannot pay" in res.json()["detail"].lower()
