# Mizigo Marketplace Architecture

## 1. Overview & Technology Stack

Mizigo is a near-production multi-vendor marketplace designed with a clean, accessible technology stack:

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL, Alembic
- **Security**: OAuth2 Bearer JWT (`python-jose`), bcrypt password hashing (`passlib`)
- **Frontend**: React 18, Vite, Tailwind CSS, React Router v6, native browser `fetch`
- **Testing**: Pytest, Starlette `TestClient`, isolated SQLite in-memory engine
- **Infrastructure**: Docker, Docker Compose, GitHub Actions CI

---

## 2. Request Lifecycle & Layered Responsibilities

```
[ Client Request ]
       │
       ▼
[ FastAPI App & Middlewares ]
 ├── CORS Middleware (Configurable Origins)
 ├── Rate Limiting (SlowAPI)
 └── Exception Handlers (Consistent JSON error responses)
       │
       ▼
[ Routers (HTTP & Routing Layer) ]
 ├── Dependency Injection (get_db, get_current_user, require_admin_user, require_active_vendor)
 └── Pydantic Schema Validation (Request validation & Response serialization)
       │
       ▼
[ Services (Business Logic & Transactions) ]
 ├── Product Service (Subscription plan limits, active state verification)
 ├── Order Service (Deterministic sorted locking, inventory checks, price calculation)
 └── Payment Service (Atomic state transitions, idempotency, unique transaction generation)
       │
       ▼
[ SQLAlchemy ORM & PostgreSQL Database ]
```

### Layer Responsibilities
1. **Routers (`app/routers/`)**: Handle HTTP requests, status codes, query/path parameters, and authorization dependencies.
2. **Schemas (`app/schemas/`)**: Pydantic models for request payload validation and response contracts.
3. **Services (`app/services/`)**: Enforce business rules, coordinate multi-model updates, and manage transaction commit/rollback boundaries.
4. **Models (`app/models/`)**: Declarative SQLAlchemy models defining schema, column constraints, and foreign key relationships.

---

## 3. Database Entity Relationships

```mermaid
erDiagram
    USERS ||--o| VENDORS : "owns (1:1)"
    USERS ||--o{ ORDERS : "places (1:N)"
    VENDORS ||--o{ PRODUCTS : "lists (1:N)"
    VENDORS ||--o{ ORDER_ITEMS : "supplies (1:N)"
    PRODUCTS ||--|| INVENTORY : "tracks (1:1)"
    PRODUCTS ||--o{ ORDER_ITEMS : "included_in (1:N)"
    ORDERS ||--|{ ORDER_ITEMS : "contains (1:N)"
    ORDERS ||--o| PAYMENTS : "paid_by (1:1)"

    USERS {
        int id PK
        string email UK
        string hashed_password
        string role
        boolean is_active
    }
    VENDORS {
        int id PK
        int user_id FK,UK
        string store_name
        string subscription_plan
        datetime subscription_expiry
        boolean is_active
    }
    PRODUCTS {
        int id PK
        int vendor_id FK
        string name
        numeric price
        boolean is_active
    }
    INVENTORY {
        int id PK
        int product_id FK,UK
        int quantity_available
        int reserved_quantity
    }
    ORDERS {
        int id PK
        int user_id FK
        string status
        numeric total_amount
        datetime created_at
    }
    ORDER_ITEMS {
        int id PK
        int order_id FK
        int product_id FK
        int vendor_id FK
        int quantity
        numeric price_at_purchase
    }
    PAYMENTS {
        int id PK
        int order_id FK
        numeric amount
        string status
        string provider
        string transaction_id
        datetime created_at
    }
```

---

## 4. Order & Payment Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING : POST /orders (Stock decremented & reserved)
    PENDING --> CONFIRMED : POST /payments (Payment successful, Order confirmed)
    PENDING --> CANCELLED : POST /orders/{id}/cancel (Stock released to inventory)
    CONFIRMED --> [*] : Order completed
    CANCELLED --> [*] : Order cancelled
```

### Key Business Rules:
1. **Server-Authoritative Pricing**: Customers submit only `product_id` and `quantity`. Total prices are derived strictly from the database.
2. **Inventory Concurrency Protection**: Orders acquire row locks using `SELECT ... FOR UPDATE` ordered by `product_id` to prevent deadlocks and race conditions.
3. **Pending Reservation**: Stock is decremented upon order creation. If unpaid, orders can be cancelled via `POST /orders/{id}/cancel`, which returns items back to available inventory.
4. **Idempotent Payment**: Once an order is `CONFIRMED`, duplicate payment requests are rejected. Cancelled orders cannot be paid.
