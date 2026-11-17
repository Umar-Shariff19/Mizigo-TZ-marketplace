"""
End-to-end integration verification script for Mizigo Marketplace.
Verifies complete customer, vendor, and administrator workflows
against the containerized backend connected to disposable PostgreSQL.
"""
import sys
import uuid
import httpx
from decimal import Decimal

BASE_URL = "http://localhost:8001"


def run_e2e_verification():
    print("=" * 60)
    print("Starting Mizigo End-to-End Workflow Verification")
    print(f"Target: {BASE_URL}")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # Step 1: Health check
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    print("[PASS] Step 1: Backend service health check OK")

    # Step 2: Register Customer 1
    suffix = uuid.uuid4().hex[:6]
    cust_email = f"customer_{suffix}@example.com"
    cust_password = "CustomerPass123!"
    resp = client.post(
        "/users",
        json={
            "email": cust_email,
            "password": cust_password,
        },
    )
    assert resp.status_code == 200, f"Customer registration failed: {resp.text}"
    cust_data = resp.json()
    assert cust_data["role"] == "CUSTOMER", f"Role escalation bug: {cust_data}"
    print(f"[PASS] Step 2: Customer registered ({cust_email}) with enforced role='CUSTOMER'")

    # Step 3: Login Customer 1
    resp = client.post(
        "/login",
        data={"username": cust_email, "password": cust_password},
    )
    assert resp.status_code == 200, f"Customer login failed: {resp.text}"
    cust_token = resp.json()["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    print("[PASS] Step 3: Customer login succeeded, JWT obtained")

    # Step 4: Register User 2 for Vendor Onboarding
    vend_email = f"vendor_{suffix}@example.com"
    vend_password = "VendorPass123!"
    resp = client.post(
        "/users",
        json={
            "email": vend_email,
            "password": vend_password,
        },
    )
    assert resp.status_code == 200, f"Vendor user registration failed: {resp.text}"
    print(f"[PASS] Step 4: Vendor base user registered ({vend_email})")

    # Step 5: Login User 2
    resp = client.post(
        "/login",
        data={"username": vend_email, "password": vend_password},
    )
    assert resp.status_code == 200, f"Vendor login failed: {resp.text}"
    vend_token = resp.json()["access_token"]
    vend_headers = {"Authorization": f"Bearer {vend_token}"}
    print("[PASS] Step 5: Vendor user login succeeded")

    # Step 6: Onboard as Vendor
    store_name = f"Bob's Organic Market {suffix}"
    resp = client.post(
        "/vendors",
        headers=vend_headers,
        json={"store_name": store_name},
    )
    assert resp.status_code == 200, f"Vendor onboarding failed: {resp.text}"
    vendor_profile = resp.json()
    vendor_id = vendor_profile["id"]
    print(f"[PASS] Step 6: Vendor onboarded successfully (ID: {vendor_id}, Store: {store_name})")

    # Step 7: Vendor creates a Product
    prod_name = f"Organic Avocados {suffix}"
    resp = client.post(
        "/products",
        headers=vend_headers,
        json={
            "name": prod_name,
            "description": "Fresh ripe Hass avocados",
            "price": 25.50,
            "quantity": 10,
        },
    )
    assert resp.status_code == 200, f"Product creation failed: {resp.text}"
    prod_data = resp.json()
    product_id = prod_data["id"]
    assert prod_data["quantity_available"] == 10
    print(f"[PASS] Step 7: Vendor created product (ID: {product_id}, Stock: 10, Price: 25.50)")

    # Step 8: Verify product appears in public catalogue
    resp = client.get(f"/products?search={prod_name}")
    assert resp.status_code == 200
    catalogue = resp.json()
    assert any(p["id"] == product_id for p in catalogue), f"Product missing from search catalogue: {catalogue}"
    print(f"[PASS] Step 8: Product visible in public catalogue (found {len(catalogue)} matching items)")

    # Step 9: Customer places Order 1 for 4 units
    resp = client.post(
        "/orders",
        headers=cust_headers,
        json={"items": [{"product_id": product_id, "quantity": 4}]},
    )
    assert resp.status_code == 200, f"Order placement failed: {resp.text}"
    order_1 = resp.json()
    order_1_id = order_1["id"]
    assert Decimal(str(order_1["total_amount"])) == Decimal("102.00")  # 4 * 25.50
    print(f"[PASS] Step 9: Customer placed Order 1 (ID: {order_1_id}, Qty: 4, Total: 102.00)")

    # Check inventory decremented to 6
    resp = client.get(f"/products/{product_id}")
    assert resp.status_code == 200
    assert resp.json()["quantity_available"] == 6, f"Stock not decremented: {resp.json()}"
    print("[PASS] Step 10: Inventory decremented from 10 to 6 after order")

    # Step 11: Customer cancels Order 1 -> Inventory must restore to 10
    resp = client.post(f"/orders/{order_1_id}/cancel", headers=cust_headers)
    assert resp.status_code == 200, f"Order cancellation failed: {resp.text}"
    cancelled_order = resp.json()
    assert cancelled_order["status"] == "CANCELLED"

    resp = client.get(f"/products/{product_id}")
    assert resp.json()["quantity_available"] == 10, f"Stock not restored: {resp.json()}"
    print("[PASS] Step 11: Order 1 cancelled, inventory restored back to 10")

    # Step 12: Customer places Order 2 for 3 units
    resp = client.post(
        "/orders",
        headers=cust_headers,
        json={"items": [{"product_id": product_id, "quantity": 3}]},
    )
    assert resp.status_code == 200, f"Order 2 placement failed: {resp.text}"
    order_2 = resp.json()
    order_2_id = order_2["id"]
    assert Decimal(str(order_2["total_amount"])) == Decimal("76.50")  # 3 * 25.50
    print(f"[PASS] Step 12: Customer placed Order 2 (ID: {order_2_id}, Qty: 3, Total: 76.50)")

    resp = client.get(f"/products/{product_id}")
    assert resp.json()["quantity_available"] == 7

    # Step 13: Customer pays for Order 2
    resp = client.post(
        "/payments",
        headers=cust_headers,
        json={"order_id": order_2_id, "provider": "simulated"},
    )
    assert resp.status_code == 200, f"Payment failed: {resp.text}"
    payment_data = resp.json()
    assert payment_data["order_status"] == "CONFIRMED"
    assert payment_data["transaction_id"].startswith("SIM_TXN_")
    print(f"[PASS] Step 13: Order 2 paid successfully (Txn: {payment_data['transaction_id']})")

    # Verify order status updated to confirmed
    resp = client.get(f"/orders/{order_2_id}", headers=cust_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CONFIRMED"
    print("[PASS] Step 14: Order 2 status verified as 'CONFIRMED'")

    # Step 15: Payment idempotency - second payment attempt must fail
    resp = client.post(
        "/payments",
        headers=cust_headers,
        json={"order_id": order_2_id, "provider": "simulated"},
    )
    assert resp.status_code == 400, f"Expected 400 on duplicate payment, got {resp.status_code}: {resp.text}"
    print("[PASS] Step 15: Duplicate payment attempt correctly rejected with 400 Bad Request")

    # Step 16: Admin workflow - Login as administrator
    resp = client.post(
        "/login",
        data={"username": "admin_e2e@example.com", "password": "AdminSecretPass123!"},
    )
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    admin_token = resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("[PASS] Step 16: Administrator authenticated successfully")

    # Step 17: Admin lists users, vendors, and orders
    resp_users = client.get("/admin/users", headers=admin_headers)
    resp_vendors = client.get("/admin/vendors", headers=admin_headers)
    resp_orders = client.get("/admin/orders", headers=admin_headers)
    assert resp_users.status_code == 200 and len(resp_users.json()) > 0
    assert resp_vendors.status_code == 200 and len(resp_vendors.json()) > 0
    assert resp_orders.status_code == 200 and len(resp_orders.json()) > 0
    print(f"[PASS] Step 17: Admin successfully queried users ({len(resp_users.json())}), vendors ({len(resp_vendors.json())}), and orders ({len(resp_orders.json())})")

    # Step 18: Admin suspends Vendor
    resp = client.patch(
        f"/admin/vendors/{vendor_id}/suspend",
        headers=admin_headers,
    )
    assert resp.status_code == 200, f"Vendor suspension failed: {resp.text}"
    assert resp.json()["is_active"] is False
    print(f"[PASS] Step 18: Admin suspended Vendor {vendor_id} (is_active=False)")

    # Step 19: Public catalogue check - suspended vendor's products hidden
    resp = client.get(f"/products?search={prod_name}")
    assert resp.status_code == 200
    catalogue_after = resp.json()
    assert not any(p["id"] == product_id for p in catalogue_after), (
        "Suspended vendor's product is still visible in public catalogue!"
    )
    print("[PASS] Step 19: Suspended vendor's product automatically excluded from public catalogue")

    # Step 20: Suspended vendor cannot create products
    resp = client.post(
        "/products",
        headers=vend_headers,
        json={
            "name": "Forbidden Item",
            "price": 10.0,
            "quantity": 5,
        },
    )
    assert resp.status_code == 403, f"Expected 403 for suspended vendor, got {resp.status_code}: {resp.text}"
    print("[PASS] Step 20: Suspended vendor blocked from creating products (HTTP 403 Forbidden)")

    # Step 21: Customer cannot order from suspended vendor
    resp = client.post(
        "/orders",
        headers=cust_headers,
        json={"items": [{"product_id": product_id, "quantity": 1}]},
    )
    assert resp.status_code == 400, f"Expected 400 ordering suspended product, got {resp.status_code}: {resp.text}"
    print("[PASS] Step 21: Ordering product from suspended vendor rejected with HTTP 400 Bad Request")

    print("=" * 60)
    print("ALL 21 END-TO-END WORKFLOW VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_e2e_verification()
    except Exception as e:
        print(f"[FAIL] End-to-end verification encountered error: {e}", file=sys.stderr)
        sys.exit(1)
