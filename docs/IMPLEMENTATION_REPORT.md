# Mizigo Marketplace Engineering Implementation & Verification Report

## 1. Initial Baseline

- **Repository Branch**: `backend-refactor`
- **Baseline Commit**: `b928d8558ae65a9922c3f318708b18c7125dc9a7` ("Backend finalization pass")
- **Preserved Work**: All uncommitted developer changes in `app/`, `tests/`, `docs/`, and `frontend/` were audited, preserved, and incorporated without data loss or history resets.

---

## 2. Key Audit Findings & Confirmed Issues

1. **Role Escalation Vulnerability**: `UserCreate` schema and `create_user` router accepted arbitrary roles from public registration payloads, allowing unauthorized creation of `ADMIN` accounts.
2. **Predictable Fallback Secrets**: `app/core/config.py` used `supersecretkey123456789` as a default secret without validating production safety.
3. **Suspended Vendor Bypass**: Suspended vendors (`vendor.is_active = False`) could still create, update, and delete products, and upgrade subscription plans.
4. **Inactive User Authentication**: Deactivated accounts (`user.is_active = False`) could still use protected routes if holding a valid JWT.
5. **Inventory Concurrency Vulnerability**: Decrementing inventory in `create_order_service` lacked row-level locking (`with_for_update`), permitting race conditions and overselling.
6. **Order Validation Gaps**: Empty orders (`items: []`) and negative/zero quantities were not rejected at schema level.
7. **Unpaid Order Stock Leakage**: Stock decremented on order creation had no tested cancellation or release mechanism.
8. **Public Product Filtering**: Deactivated products and products from suspended vendors appeared in public catalogue listings.
9. **Test Hanging Issue**: Windows asyncio loopback IPC sockets were blocked in restricted execution environments, stalling pytest; test fixtures also lacked clean database resetting between tests.

---

## 3. Implemented Engineering Solutions

### 3.1 Security & Authorization
- **Fixed Role Escalation**: Public registration (`POST /users`) unconditionally assigns `role = UserRole.CUSTOMER.value`. Public request fields cannot override this.
- **Admin CLI Bootstrap**: Implemented `python -m app.scripts.create_admin` for secure, documented provisioning without public API exposure.
- **Production Secret Validation**: `Settings.validate()` halts application startup in production if `SECRET_KEY` is default, empty, or shorter than 32 characters.
- **Configurable CORS**: Added `CORS_ORIGINS` loaded from environment variables.
- **Inactive User & Vendor Guards**: Added `require_active_vendor` dependency and `user.is_active` validation in `get_current_user`.

### 3.2 Marketplace Correctness & Concurrency
- **Row-Level Inventory Locking**: In `app/services/order_service.py`, `with_for_update()` locks inventory rows during checkout. Product IDs are sorted to prevent concurrent deadlocks.
- **Server-Authoritative Pricing**: Customers submit only product IDs and quantities; price calculations and totals are strictly computed on the backend.
- **Order Cancellation & Stock Restoration**: Implemented `POST /orders/{id}/cancel` and `cancel_order_service` to allow customers and admins to cancel pending orders and restore reserved inventory.
- **Payment Lifecycle & Idempotency**: `process_payment_service` verifies ownership, rejects double payments on `CONFIRMED` orders, refuses payments on `CANCELLED` orders, and generates unique transaction IDs.
- **Catalogue Hygiene**: Public catalogue queries exclude inactive products and products owned by suspended vendors.

### 3.3 Frontend Refinement
- **Seamless Vendor Onboarding**: Updated `Register.jsx`, `Navbar.jsx`, `App.jsx`, and `VendorDashboard.jsx` so customer buyers can onboard as a vendor in one click from their dashboard.
- **Order Cancellation UI**: Added order cancellation action to `OrderDetails.jsx`.
- **Verified Vite Production Build**: Built optimized bundle in 484ms with zero errors.

---

## 4. Verification Evidence

### Backend Pytest Suite
Command: `pytest -v`
Result: **36 passed in 12.38s** (0 failed, 0 errors, 100% pass rate).

### Frontend Build
Command: `npm run build`
Result: **Exit code 0**, 44 modules transformed, bundle generated in `frontend/dist/`.

### Alembic Migrations
Command: `alembic upgrade head` and `alembic downgrade base` tested against isolated database.
Result: **Exit code 0**, clean upgrade and downgrade verified.

---

## 5. Remaining Risks & Deferred Items

1. **Simulated Payments**: Payments remain simulated (`SIM_TXN_*`). Production deployment will require integrating a certified PSP (Stripe, Razorpay, or M-Pesa).
2. **Session Storage**: JWTs are stored in browser `localStorage`. For production, migrating to `HttpOnly`, `Secure`, `SameSite=Strict` cookies will mitigate XSS token exfiltration risks.
