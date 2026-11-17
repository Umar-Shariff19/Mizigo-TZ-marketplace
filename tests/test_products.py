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
def vendor_setup():
    """Create test vendor with user, vendor profile, and auth token."""
    db = TestingSessionLocal()
    uid = uuid.uuid4().hex[:8]
    try:
        user = User(
            email=f"vendor_{uid}@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.VENDOR.value,
            is_active=True,
        )
        db.add(user)
        db.commit()

        vendor = Vendor(
            user_id=user.id,
            store_name=f"Vendor Store {uid}",
            is_active=True,
        )
        db.add(vendor)
        db.commit()

        token = create_access_token(data={"sub": user.email, "role": user.role})
        return {"token": token, "vendor_id": vendor.id, "user_id": user.id}
    finally:
        db.close()


def test_vendor_create_product_success(vendor_setup) -> None:
    token = vendor_setup["token"]
    res = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Super Coffee Maker",
            "description": "Brews fresh coffee fast",
            "price": "99.99",
            "quantity": 15,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Super Coffee Maker"
    assert float(data["price"]) == 99.99
    assert data["quantity_available"] == 15
    assert data["is_active"] is True


def test_product_price_and_quantity_validation(vendor_setup) -> None:
    token = vendor_setup["token"]

    # Reject non-positive price
    res_zero_price = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Freebie Item", "price": "0.00", "quantity": 10},
    )
    assert res_zero_price.status_code in {400, 422}

    res_negative_price = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Bad Price", "price": "-10.00", "quantity": 10},
    )
    assert res_negative_price.status_code in {400, 422}

    # Reject negative quantity
    res_neg_qty = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Negative Inventory", "price": "19.99", "quantity": -5},
    )
    assert res_neg_qty.status_code in {400, 422}


def test_suspended_vendor_cannot_create_or_update_products() -> None:
    db = TestingSessionLocal()
    uid = uuid.uuid4().hex[:8]
    try:
        user = User(
            email=f"suspended_{uid}@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.VENDOR.value,
            is_active=True,
        )
        db.add(user)
        db.commit()

        vendor = Vendor(
            user_id=user.id,
            store_name=f"Suspended Store {uid}",
            is_active=False,  # Suspended!
        )
        db.add(vendor)
        db.commit()
    finally:
        db.close()

    token = create_access_token(data={"sub": user.email, "role": user.role})

    # Attempt create product
    res = client.post(
        "/products",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Sneaky Product", "price": "50.00", "quantity": 5},
    )
    assert res.status_code == 403
    assert "suspended" in res.json()["message"].lower()

    # Attempt subscription upgrade
    res_upg = client.post(
        "/vendors/upgrade",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_upg.status_code == 403
    assert "suspended" in res_upg.json()["message"].lower()


def test_public_catalogue_excludes_inactive_and_suspended_products() -> None:
    db = TestingSessionLocal()
    uid = uuid.uuid4().hex[:8]
    try:
        user = User(
            email=f"active_seller_{uid}@mizigo.com",
            hashed_password=hash_password("password123"),
            role=UserRole.VENDOR.value,
            is_active=True,
        )
        db.add(user)
        db.commit()

        vendor = Vendor(user_id=user.id, store_name=f"Active Store {uid}", is_active=True)
        db.add(vendor)
        db.commit()

        # 1 active product
        prod_active = Product(vendor_id=vendor.id, name="Visible Product", price=Decimal("25.00"), is_active=True)
        prod_active.inventory = Inventory(quantity_available=10)
        db.add(prod_active)

        # 1 inactive product
        prod_inactive = Product(vendor_id=vendor.id, name="Hidden Product", price=Decimal("25.00"), is_active=False)
        prod_inactive.inventory = Inventory(quantity_available=10)
        db.add(prod_inactive)
        db.commit()

        active_id = prod_active.id
        inactive_id = prod_inactive.id
    finally:
        db.close()

    # Query public catalogue with adequate limit to avoid pagination clipping
    res = client.get("/products?limit=100")
    assert res.status_code == 200
    items = res.json()
    names = [i["name"] for i in items]
    assert "Visible Product" in names
    assert "Hidden Product" not in names

    # Single lookup for inactive product by public visitor should return 404
    res_single_inactive = client.get(f"/products/{inactive_id}")
    assert res_single_inactive.status_code == 404

    # Single lookup by the owner vendor should succeed
    vendor_token = create_access_token(data={"sub": user.email, "role": "VENDOR"})
    res_owner_lookup = client.get(
        f"/products/{inactive_id}",
        headers={"Authorization": f"Bearer {vendor_token}"},
    )
    assert res_owner_lookup.status_code == 200
    assert res_owner_lookup.json()["id"] == inactive_id


def test_product_search_and_filtering() -> None:
    # Test price filtering and sort parameters
    res = client.get("/products?min_price=10&max_price=100&sort_by=price&sort_order=desc")
    assert res.status_code == 200
    products = res.json()
    assert isinstance(products, list)
    for p in products:
        assert float(p["price"]) >= 10
        assert float(p["price"]) <= 100
