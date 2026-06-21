from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_users_list_requires_authentication() -> None:
    response = client.get("/users")

    assert response.status_code == 401


def test_admin_module_requires_authentication() -> None:
    response = client.get("/admin/status")

    assert response.status_code == 401


def test_admin_users_requires_authentication() -> None:
    response = client.get("/admin/users")

    assert response.status_code == 401


def test_vendor_products_requires_authentication() -> None:
    response = client.get("/vendor/products")

    assert response.status_code == 401


def test_vendor_dashboard_requires_authentication() -> None:
    response = client.get("/vendor/dashboard")

    assert response.status_code == 401


def test_my_orders_requires_authentication() -> None:
    response = client.get("/orders/me")

    assert response.status_code == 401


def test_products_reject_invalid_sort_field() -> None:
    response = client.get("/products?sort_by=unknown")

    assert response.status_code == 400
    assert response.json()["message"] == "Invalid sort_by field"
