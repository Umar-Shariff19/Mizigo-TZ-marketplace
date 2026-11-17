import os
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import socket
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.enums import OrderStatus, PaymentStatus, UserRole
from app.core.security import hash_password
from app.models.user import User
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.payment import PaymentCreate
from app.services.order_service import create_order_service, cancel_order_service
from app.services.payment_service import process_payment_service
from fastapi import HTTPException

PG_TEST_URL = "postgresql://mizigo_test:mizigo_test_secret@localhost:5433/mizigo_disposable_db"

def is_pg_available() -> bool:
    try:
        with socket.create_connection(("localhost", 5433), timeout=1.0):
            return True
    except OSError:
        return False

# In CI or environments requiring PostgreSQL, prevent tests from silently skipping
if os.getenv("REQUIRE_PG_TESTS") == "1" and not is_pg_available():
    raise RuntimeError("REQUIRE_PG_TESTS is enabled, but PostgreSQL service is not reachable on localhost:5433")

pytestmark = pytest.mark.skipif(
    not is_pg_available(),
    reason="Disposable PostgreSQL container on port 5433 is not running"
)

# Strict safety assertion: Guarantee we never connect to default 5432 or non-disposable DB
assert ":5433/" in PG_TEST_URL and "mizigo_disposable_db" in PG_TEST_URL

pg_engine = create_engine(PG_TEST_URL, pool_size=10, max_overflow=5) if is_pg_available() else None
PgSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine) if pg_engine else None


@pytest.fixture
def pg_session():
    """Provides a fresh database session for setup/teardown."""
    db = PgSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_concurrent_orders_prevent_overselling(pg_session):
    """
    Test two concurrent threads competing for a single item in stock.
    Row-level locking (with_for_update) must serialize execution so exactly
    one order succeeds and the other fails with Insufficient stock.
    Stock must never become negative.
    """
    uid = uuid.uuid4().hex[:8]

    # Create Vendor & Single-Stock Product
    user_vendor = User(
        email=f"v_{uid}@mizigo.com",
        hashed_password=hash_password("pass"),
        role=UserRole.VENDOR.value,
        is_active=True,
    )
    pg_session.add(user_vendor)
    pg_session.commit()

    vendor = Vendor(user_id=user_vendor.id, store_name=f"Store_{uid}", is_active=True)
    pg_session.add(vendor)
    pg_session.commit()

    product = Product(vendor_id=vendor.id, name=f"Limited Item {uid}", price=Decimal("100.00"), is_active=True)
    product.inventory = Inventory(quantity_available=1, reserved_quantity=0)
    pg_session.add(product)
    pg_session.commit()
    product_id = product.id

    # Create two distinct customers
    c1 = User(email=f"buyer1_{uid}@mizigo.com", hashed_password=hash_password("pass"), role=UserRole.CUSTOMER.value, is_active=True)
    c2 = User(email=f"buyer2_{uid}@mizigo.com", hashed_password=hash_password("pass"), role=UserRole.CUSTOMER.value, is_active=True)
    pg_session.add_all([c1, c2])
    pg_session.commit()

    order_payload = OrderCreate(items=[OrderItemCreate(product_id=product_id, quantity=1)])

    barrier = threading.Barrier(2)
    results = []

    def place_order(customer_obj):
        db = PgSessionLocal()
        # Synchronize thread start so both transactions hit the database at the same moment
        barrier.wait(timeout=5)
        try:
            order = create_order_service(db, customer_obj, order_payload)
            results.append(("SUCCESS", order.id))
        except HTTPException as he:
            db.rollback()
            results.append(("FAILED", he.detail))
        except Exception as e:
            db.rollback()
            results.append(("ERROR", str(e)))
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(place_order, c1)
        f2 = executor.submit(place_order, c2)
        f1.result(timeout=10)
        f2.result(timeout=10)

    successes = [r for r in results if r[0] == "SUCCESS"]
    failures = [r for r in results if r[0] == "FAILED"]

    # Assert exactly 1 order won the stock and 1 was rejected
    assert len(successes) == 1, f"Expected exactly 1 success, got: {results}"
    assert len(failures) == 1, f"Expected exactly 1 failure, got: {results}"
    assert "insufficient stock" in failures[0][1].lower()

    # Verify inventory was decremented to 0 and NEVER became negative
    check_session = PgSessionLocal()
    try:
        inv = check_session.query(Inventory).filter(Inventory.product_id == product_id).first()
        assert inv.quantity_available == 0, f"Expected 0 stock, got {inv.quantity_available}"
        assert inv.reserved_quantity == 1
    finally:
        check_session.close()


def test_multi_item_order_rollback_on_partial_failure(pg_session):
    """
    Test that an order with multiple items where one item fails partway through
    rolls back all previously deducted items atomically.
    """
    uid = uuid.uuid4().hex[:8]

    # Vendor
    v_user = User(email=f"v_multi_{uid}@mizigo.com", hashed_password=hash_password("pass"), role=UserRole.VENDOR.value, is_active=True)
    pg_session.add(v_user)
    pg_session.commit()

    vendor = Vendor(user_id=v_user.id, store_name=f"Store_multi_{uid}", is_active=True)
    pg_session.add(vendor)
    pg_session.commit()

    # Product A has 10 units
    prod_a = Product(vendor_id=vendor.id, name=f"Product A {uid}", price=Decimal("20.00"), is_active=True)
    prod_a.inventory = Inventory(quantity_available=10, reserved_quantity=0)

    # Product B has 0 units (out of stock)
    prod_b = Product(vendor_id=vendor.id, name=f"Product B {uid}", price=Decimal("30.00"), is_active=True)
    prod_b.inventory = Inventory(quantity_available=0, reserved_quantity=0)

    pg_session.add_all([prod_a, prod_b])
    pg_session.commit()

    buyer = User(email=f"buyer_multi_{uid}@mizigo.com", hashed_password=hash_password("pass"), role=UserRole.CUSTOMER.value, is_active=True)
    pg_session.add(buyer)
    pg_session.commit()

    # Order requests 2 of A and 1 of B (B will fail)
    order_payload = OrderCreate(
        items=[
            OrderItemCreate(product_id=prod_a.id, quantity=2),
            OrderItemCreate(product_id=prod_b.id, quantity=1),
        ]
    )

    db = PgSessionLocal()
    with pytest.raises(HTTPException) as exc_info:
        try:
            create_order_service(db, buyer, order_payload)
        except Exception:
            db.rollback()
            raise
    db.close()

    assert exc_info.value.status_code == 400
    assert "insufficient stock" in exc_info.value.detail.lower()

    # Verify Product A inventory remained completely untouched (10 units)
    check_session = PgSessionLocal()
    try:
        inv_a = check_session.query(Inventory).filter(Inventory.product_id == prod_a.id).first()
        assert inv_a.quantity_available == 10, f"Expected 10 units for Product A, got {inv_a.quantity_available}"
    finally:
        check_session.close()


def test_order_cancellation_idempotency(pg_session):
    """
    Test that cancelling an order restores inventory exactly once,
    and a second cancellation attempt is rejected without restoring stock again.
    """
    uid = uuid.uuid4().hex[:8]

    v_user = User(email=f"v_cancel_{uid}@mizigo.com", hashed_password=hash_password("pass"), role=UserRole.VENDOR.value, is_active=True)
    pg_session.add(v_user)
    pg_session.commit()

    vendor = Vendor(user_id=v_user.id, store_name=f"Store_cancel_{uid}", is_active=True)
    pg_session.add(vendor)
    pg_session.commit()

    prod = Product(vendor_id=vendor.id, name=f"Product Cancel {uid}", price=Decimal("15.00"), is_active=True)
    prod.inventory = Inventory(quantity_available=5, reserved_quantity=0)
    pg_session.add(prod)
    pg_session.commit()

    buyer = User(email=f"buyer_cancel_{uid}@mizigo.com", hashed_password=hash_password("pass"), role=UserRole.CUSTOMER.value, is_active=True)
    pg_session.add(buyer)
    pg_session.commit()

    # Order 2 units
    order_payload = OrderCreate(items=[OrderItemCreate(product_id=prod.id, quantity=2)])
    order = create_order_service(pg_session, buyer, order_payload)
    order_id = order.id

    # Stock should be 3
    inv1 = pg_session.query(Inventory).filter(Inventory.product_id == prod.id).first()
    assert inv1.quantity_available == 3

    # Cancel once -> Stock should be restored to 5
    cancelled_order = cancel_order_service(pg_session, buyer, order_id)
    assert cancelled_order.status == OrderStatus.CANCELLED.value

    inv2 = pg_session.query(Inventory).filter(Inventory.product_id == prod.id).first()
    assert inv2.quantity_available == 5

    # Cancel a second time -> Must be rejected with HTTP 400
    with pytest.raises(HTTPException) as exc_info:
        cancel_order_service(pg_session, buyer, order_id)

    assert exc_info.value.status_code == 400
    assert "only pending orders" in exc_info.value.detail.lower()

    # Stock must STILL be 5 (never incremented to 7)
    inv3 = pg_session.query(Inventory).filter(Inventory.product_id == prod.id).first()
    assert inv3.quantity_available == 5


def test_payment_idempotency_prevents_duplicate_payments(pg_session):
    """
    Test that once an order is paid, repeated payment requests are rejected,
    preventing duplicate Payment records in PostgreSQL.
    """
    uid = uuid.uuid4().hex[:8]

    v_user = User(email=f"v_pay_{uid}@mizigo.com", hashed_password=hash_password("pass"), role=UserRole.VENDOR.value, is_active=True)
    pg_session.add(v_user)
    pg_session.commit()

    vendor = Vendor(user_id=v_user.id, store_name=f"Store_pay_{uid}", is_active=True)
    pg_session.add(vendor)
    pg_session.commit()

    prod = Product(vendor_id=vendor.id, name=f"Product Pay {uid}", price=Decimal("50.00"), is_active=True)
    prod.inventory = Inventory(quantity_available=10, reserved_quantity=0)
    pg_session.add(prod)
    pg_session.commit()

    buyer = User(email=f"buyer_pay_{uid}@mizigo.com", hashed_password=hash_password("pass"), role=UserRole.CUSTOMER.value, is_active=True)
    pg_session.add(buyer)
    pg_session.commit()

    order_payload = OrderCreate(items=[OrderItemCreate(product_id=prod.id, quantity=1)])
    order = create_order_service(pg_session, buyer, order_payload)

    pay_payload = PaymentCreate(order_id=order.id, provider="simulated")

    # Payment 1 succeeds
    res1 = process_payment_service(pg_session, pay_payload)
    assert res1["message"] == "Payment successful"
    assert res1["order_status"] == OrderStatus.CONFIRMED.value

    # Payment 2 must fail
    with pytest.raises(HTTPException) as exc_info:
        process_payment_service(pg_session, pay_payload)

    assert exc_info.value.status_code == 400
    assert "already paid" in exc_info.value.detail.lower()

    # Confirm exactly 1 Payment row exists in PostgreSQL
    payments = pg_session.query(Payment).filter(Payment.order_id == order.id).all()
    assert len(payments) == 1
