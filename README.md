# Mizigo Marketplace

Mizigo is a reliable, maintainable multi-vendor marketplace platform built with FastAPI, SQLAlchemy, PostgreSQL, and React.

---

## 1. Technology Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL, Alembic
- **Security**: OAuth2 Bearer Tokens (JWT HS256), bcrypt password hashing (`passlib`)
- **Frontend**: React 18, Vite, Tailwind CSS, React Router v6, native browser `fetch`
- **Testing**: Pytest, Starlette `TestClient`, isolated in-memory SQLite test database
- **Infrastructure**: Docker, Docker Compose, GitHub Actions CI

---

## 2. Repository Structure

```
mizigo-backend/
├── .github/workflows/ci.yml       # GitHub Actions CI workflow
├── alembic/                       # Alembic migrations & environment
│   └── versions/                  # Version migration scripts
├── app/
│   ├── core/                      # Config, security, dependencies, exceptions, enums
│   ├── db/                        # Database session & engine setup
│   ├── models/                    # SQLAlchemy declarative models
│   ├── routers/                   # FastAPI API route controllers
│   ├── schemas/                   # Pydantic request/response schemas
│   ├── scripts/                   # Administrative CLI bootstrap scripts
│   └── services/                  # Business logic & transactional services
├── docs/                          # Comprehensive technical documentation
│   ├── ARCHITECTURE.md            # System architecture & lifecycle diagrams
│   ├── SECURITY.md                # Security controls & authorization rules
│   ├── DATABASE_MIGRATIONS.md     # Migration & existing database guide
│   ├── TESTING.md                 # Test suite architecture & instructions
│   ├── DEPLOYMENT.md              # Production deployment & Docker guidelines
│   └── IMPLEMENTATION_REPORT.md   # Implementation findings & verification report
├── frontend/                      # React + Vite frontend application
│   ├── src/                       # Components, pages, assets, router setup
│   └── package.json               # Frontend dependencies & scripts
├── tests/                         # Pytest test suite
│   ├── conftest.py                # Isolated test database fixtures
│   ├── test_admin.py              # Administration & role guard tests
│   ├── test_api_smoke.py          # API route smoke tests
│   ├── test_auth_and_security.py  # Security & privilege escalation tests
│   ├── test_orders_and_inventory.py # Order validation, cancellation & inventory tests
│   ├── test_payments.py           # Payment lifecycle & idempotency tests
│   └── test_products.py           # Product catalog, validation & vendor tests
├── docker-compose.yml             # Local multi-container development configuration
├── Dockerfile                     # Backend container image definition
├── requirements.txt               # Locked backend dependencies
└── README.md                      # Project documentation
```

---

## 3. Quick Start & Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL 15+ (or Docker)

### Backend Setup

```bash
# 1. Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\activate      # Windows PowerShell
# source venv/bin/activate    # Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env

# 4. Run database migrations (or verify against an existing database)
alembic upgrade head

# 5. Bootstrap an initial administrator user
python -m app.scripts.create_admin --email admin@mizigo.com --password "SecureAdminPassword123!"

# 6. Start the API server
uvicorn app.main:app --reload
```

- **API Base URL**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

- **Frontend App**: `http://localhost:5173`

---

## 4. API Endpoints Overview

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/login` | Public | Authenticate user and issue JWT bearer token |
| `POST` | `/users` | Public | Register customer account (privilege escalation blocked) |
| `GET` | `/products` | Public | List active products (search, sort, price filter, pagination) |
| `GET` | `/products/{id}` | Public/Vendor | Get product details by ID |
| `POST` | `/vendors` | Authenticated | Onboard user as a vendor and create store profile |
| `GET` | `/vendors` | Public | List vendor stores |
| `POST` | `/vendors/upgrade` | Vendor | Upgrade vendor subscription to PRO (30 days) |
| `POST` | `/products` | Vendor | Create product with initial inventory |
| `GET` | `/vendor/products` | Vendor | List products owned by authenticated vendor |
| `PATCH` | `/vendor/products/{id}` | Vendor | Update vendor product details |
| `DELETE` | `/vendor/products/{id}` | Vendor | Delete vendor product |
| `POST` | `/products/upload-image` | Vendor | Upload product image file (JPEG, PNG, WebP ≤ 5 MB) |
| `POST` | `/vendor/products/{id}/image` | Vendor | Upload or replace product image for owned product |
| `DELETE` | `/vendor/products/{id}/image` | Vendor | Remove product image from owned product |
| `GET` | `/vendor/dashboard` | Vendor | Vendor sales, order count, and revenue metrics |
| `POST` | `/orders` | Customer | Place order with server-calculated price and inventory locking |
| `GET` | `/orders/me` | Customer | View authenticated user's order history |
| `GET` | `/orders/{id}` | Owner/Admin | View order details |
| `POST` | `/orders/{id}/cancel` | Owner/Admin | Cancel unpaid pending order and release reserved stock |
| `POST` | `/payments` | Owner | Process simulated payment and confirm pending order |
| `GET` | `/admin/status` | Admin | Verify admin module access |
| `GET` | `/admin/users` | Admin | List all registered users |
| `GET` | `/admin/vendors` | Admin | List all vendors |
| `GET` | `/admin/orders` | Admin | List all marketplace orders |
| `PATCH` | `/admin/vendors/{id}/suspend` | Admin | Suspend vendor account and block vendor actions |
| `PATCH` | `/admin/products/{id}/deactivate` | Admin | Deactivate product from marketplace catalogue |

---

## 5. Product Image Uploads

Mizigo supports local product image uploads for active vendors:

### How It Works
1. **Vendor Upload**: Authenticated vendors can attach an image when listing a new product (`CreateProduct`) or update/replace an existing product image (`EditProduct`).
2. **Validation & Security**:
   - Supported Formats: JPEG (`.jpg`, `.jpeg`), PNG (`.png`), and WebP (`.webp`).
   - Size Limit: Maximum 5 MB per file, enforced on both the backend and client-side.
   - Header & MIME Verification: Magic bytes sniffing verifies that the actual binary content matches a valid image, rejecting spoofed extensions or malicious scripts.
   - Path Traversal Prevention: Stored filenames are generated using UUID4 hex strings (e.g., `3f7a1d...png`) rather than client-supplied filenames.
   - Authorization & Ownership: Only active vendors can upload. Updating or deleting an image verifies that the product belongs to the authenticated vendor.
3. **Storage & Access**:
   - Images are stored locally on disk under `uploads/products/`. The directory is created automatically if absent.
   - Images are served via FastAPI static file mounting at `/uploads/products/<filename>`.
   - The database stores a relative URL path (e.g., `/uploads/products/<unique_id>.png`).
   - If a product does not have an image or the file is missing, the frontend displays a clean placeholder instead of a broken image.

### Configuration
- `UPLOAD_DIR`: Configurable base upload directory via environment variable (defaults to `uploads`).
- **Note on Storage Strategy**: Local disk storage is designed for development and demo college deployment. In production multi-server or containerized environments, migrating to cloud object storage (such as AWS S3 or Cloudinary) can be implemented by adapting `app/services/image_service.py`.

---

## 6. Running Tests

The test suite runs against an isolated, in-memory SQLite database (`sqlite:///:memory:`) with zero risk to any PostgreSQL database.
Test uploads are isolated in a temporary directory and automatically cleaned up.

```bash
# Run all backend tests
pytest -v

# Run frontend production build test
cd frontend
npm run build
```

---

## 7. Docker Usage

```bash
# Build and run API and PostgreSQL containers
docker compose up -d

# Check running services
docker compose ps

# Run migrations inside container
docker compose exec api alembic upgrade head
```

---

## 8. Further Documentation

- **[Architecture & Lifecycles](file:///docs/ARCHITECTURE.md)**
- **[Security Architecture](file:///docs/SECURITY.md)**
- **[Database Migrations Guide](file:///docs/DATABASE_MIGRATIONS.md)**
- **[Testing Documentation](file:///docs/TESTING.md)**
- **[Production Deployment](file:///docs/DEPLOYMENT.md)**
- **[Implementation Report](file:///docs/IMPLEMENTATION_REPORT.md)**
