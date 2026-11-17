# Mizigo Marketplace Security Architecture & Guidelines

## 1. Authentication & Token Lifecycle

- **Password Storage**: Passwords are never stored in plaintext. They are hashed using bcrypt via `passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")`.
- **JWT Authorization**: Authenticated sessions utilize signed JSON Web Tokens (`HS256`).
- **Expiration & Validation**: Expiration is calculated in UTC (`exp` claim) and enforced by `python-jose`. Tokens missing the `sub` claim or malformed tokens are immediately rejected with HTTP 401.
- **Account State Verification**: Every authenticated request verifies `user.is_active`. Deactivated accounts are barred with HTTP 403.

---

## 2. Prevention of Privilege Escalation

### 2.1 Public Registration
- The public registration endpoint (`POST /users`) accepts email and password.
- Any role submitted in the payload is ignored; the backend unconditionally assigns `role = UserRole.CUSTOMER.value`.
- Regression tests in `tests/test_auth_and_security.py` verify that public attempts to supply `role: "ADMIN"` or `role: "VENDOR"` are completely thwarted.

### 2.2 Controlled Administrator Provisioning
Administrators cannot be created through public HTTP endpoints. They must be provisioned via the secure CLI bootstrap command:

```bash
python -m app.scripts.create_admin --email admin@mizigo.com --password "YourStrongSecretPassword!"
```

This utility enforces:
- Valid email format.
- Minimum password length (8+ characters).
- Explicit promotion or creation with `ADMIN` role.

### 2.3 Vendor Onboarding & Suspension
- Customers can onboard as a vendor through authenticated profile creation (`POST /vendors`).
- When an administrator suspends a vendor (`PATCH /admin/vendors/{id}/suspend`), `is_active` is set to `False`.
- Suspended vendors are blocked from:
  - Creating products (`HTTP 403 Vendor account is suspended`)
  - Updating products
  - Deleting products
  - Upgrading subscriptions
  - Having products shown in public marketplace catalogues

---

## 3. Configuration & Secret Hardening

Configuration is managed in `app/core/config.py`:
- In **development**, convenient defaults are available to avoid friction.
- In **production** (`ENVIRONMENT=production`):
  - Application startup fails immediately with `RuntimeError` if `SECRET_KEY` is empty, uses a default placeholder (e.g. `supersecretkey123456789`), or is shorter than 32 characters.
  - Startup validates that `DATABASE_URL` is set and does not point to a local fallback.
  - CORS origins are restricted to explicit whitelist domains specified in `CORS_ORIGINS`.

---

## 4. Transaction & Inventory Concurrency Control

- **Row-Level Locking**: `SELECT ... FOR UPDATE` row locks are acquired during order placement to eliminate race conditions and overselling.
- **Deterministic Ordering**: Product IDs are sorted before locking to prevent concurrent transaction deadlocks.
- **Atomic Payments**: Order status updates and payment receipts are written in a single database transaction.

---

## 5. Security Recommendations for Production

1. **Reverse Proxy & HTTPS**: Terminate TLS using Nginx, Cloudflare, or AWS ALB with HSTS enabled.
2. **CORS Whitelist**: Ensure `CORS_ORIGINS` in `.env` lists only trusted production frontend domains.
3. **External Secret Storage**: Store production `SECRET_KEY` and database passwords in HashiCorp Vault, AWS Secrets Manager, or GitHub Actions Secrets.
