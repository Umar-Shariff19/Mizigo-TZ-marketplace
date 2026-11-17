# Mizigo Testing Strategy & Execution Guide

## 1. Overview & Test Architecture

The Mizigo Marketplace test suite is built on **pytest** and **Starlette TestClient**.

### Safety Guarantees:
- **Zero Production/Development Database Access**: Tests run against an isolated in-memory SQLite database (`sqlite:///:memory:`) using `StaticPool`.
- **Global Override**: `tests/conftest.py` forces `DATABASE_URL` to SQLite and overrides both `app.db.session.get_db` and `app.db.database.SessionLocal` before any application code executes.
- **Clean State**: The `clean_db` autouse fixture resets and recreates empty tables between every single test.

---

## 2. Windows Asyncio Loopback IPC Diagnosis & Solution

### The Issue
On Windows, Python's `asyncio` event loop creates loopback TCP socketpairs (`127.0.0.1`) for event loop notifications. In restricted sandbox containers or without local network permissions, loopback socket creation blocks indefinitely waiting for firewall approval, causing `TestClient` requests to hang.

### The Resolution
Tests must be executed with standard local loopback network access permitted (or running in standard unconstrained environments). With loopback access permitted, all 36 tests execute and pass in under 15 seconds.

---

## 3. Running Backend Tests

Activate your virtual environment and run:

```bash
# Run full backend test suite
pytest -v

# Run tests with execution timing
pytest -v --durations=10

# Run specific test modules
pytest tests/test_auth_and_security.py -v
pytest tests/test_products.py -v
pytest tests/test_orders_and_inventory.py -v
pytest tests/test_payments.py -v
pytest tests/test_admin.py -v
```

---

## 4. Test Coverage Summary

| Test Module | Coverage Scope | Tests |
| :--- | :--- | :--- |
| `tests/test_api_smoke.py` | Health check, unauthenticated endpoint guards, basic registration/login | 10 |
| `tests/test_auth_and_security.py` | Role escalation prevention, duplicate registration, inactive users, malformed/expired JWT, admin CLI bootstrap | 7 |
| `tests/test_products.py` | Vendor product creation, price/quantity validation, suspended vendor guards, active catalogue filters, search/sort | 5 |
| `tests/test_orders_and_inventory.py` | Order creation, inventory reservation, empty/invalid payloads, inactive product rejection, stock cancellation release, cross-user isolation | 6 |
| `tests/test_payments.py` | Simulated payment confirmation, intruder rejection, double-payment prevention, cancelled order payment rejection | 4 |
| `tests/test_admin.py` | Admin-only route enforcement, user/vendor/order listing, vendor suspension, product deactivation | 4 |
| **Total** | | **36 Passed** |

---

## 5. Running Frontend Build & Verification

```bash
cd frontend
npm run build
```
Produces an optimized static bundle in `frontend/dist/` in under 1 second.
