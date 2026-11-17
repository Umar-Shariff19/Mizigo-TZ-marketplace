# Mizigo Marketplace Frontend Implementation Audit

## 1. Existing Backend Capabilities
The FastAPI backend (`app/`) is a fully functional e-commerce API built with SQLAlchemy and Pydantic. Its core capabilities include:
- **Authentication & Security**: OAuth2 password flow (`/login`), JWT access token generation, bcrypt password hashing, role-based access control (`CUSTOMER`, `VENDOR`, `ADMIN`), and rate limiting (via SlowAPI).
- **User Management**: User registration (`POST /users`), admin user listing (`GET /users` & `GET /admin/users`).
- **Vendor Management**: Store creation (`POST /vendors`), listing vendor stores (`GET /vendors`), subscription upgrades (`POST /vendors/upgrade`), vendor product management (`/vendor/products`), and vendor metrics dashboard (`GET /vendor/dashboard`).
- **Product & Inventory Management**: Product listing with pagination, search, price range filtering, and sorting (`GET /products`); product creation (`POST /products`); updating vendor products (`PATCH /vendor/products/{id}`); deleting vendor products (`DELETE /vendor/products/{id}`); admin product deactivation (`PATCH /admin/products/{id}/deactivate`).
- **Order Management**: Order placement (`POST /orders`) with automatic stock validation and reservation; customer order history (`GET /orders/me`); single order details lookup (`GET /orders/{id}`); admin order listing (`GET /admin/orders`).
- **Payments**: Simulated payment processing (`POST /payments`) supporting providers (e.g. Razorpay, Stripe, M-Pesa), which transitions order status from `PENDING` to `CONFIRMED`.
- **Database & Migrations**: PostgreSQL schema managed via Alembic (`alembic/versions/0001_initial_schema.py`).
- **Containerization & Testing**: Docker configuration (`Dockerfile`, `docker-compose.yml`), unit/integration test suite (`tests/test_api_smoke.py`).

---

## 2. Existing Frontend Capabilities
The React + Vite frontend (`frontend/`) has:
- **Build & Styling System**: Vite build tool with Tailwind CSS v4 and React Router v7.
- **Routing & Navigation**: Navbar header with authentication status and role-based links (`Navbar.jsx`), ProtectedRoute wrapper (`ProtectedRoute.jsx`).
- **Public Marketplace**: Home page hero banner (`Home.jsx`), Product listing with search, filtering, and sorting (`Products.jsx`), Product card component (`ProductCard.jsx`).
- **Authentication Pages**: User login (`Login.jsx`) storing JWT and role in `localStorage`, User registration (`Register.jsx`).
- **Customer Pages**: Order listing and order detail modal (`MyOrders.jsx`).
- **Vendor & Admin Dashboards**: Consolidated dashboard pages (`VendorDashboard.jsx` & `AdminDashboard.jsx`).

---

## 3. Backend Endpoints Available to Frontend
The frontend can interact with the following active FastAPI endpoints:

| Endpoint | Method | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | Public | API health check |
| `/login` | `POST` | Public | OAuth2 password login, returns JWT token |
| `/users` | `POST` | Public | Register new user account |
| `/users` | `GET` | Admin | List all registered users |
| `/vendors` | `POST` | Vendor | Create vendor store profile |
| `/vendors` | `GET` | Public | List all vendor store profiles |
| `/vendors/upgrade` | `POST` | Vendor | Upgrade vendor subscription to PRO |
| `/products` | `GET` | Public | List products (with pagination, min/max price, search, sorting) |
| `/products` | `POST` | Vendor | Create new product and inventory record |
| `/products/{id}` | `GET` | Public | Get single product details |
| `/vendor/products` | `GET` | Vendor | List products owned by authenticated vendor |
| `/vendor/products/{id}` | `PATCH` | Vendor | Update product details |
| `/vendor/products/{id}` | `DELETE` | Vendor | Delete vendor product |
| `/vendor/dashboard` | `GET` | Vendor | Fetch vendor product/order/revenue metrics |
| `/orders/me` | `GET` | Authenticated | List orders placed by current user |
| `/orders/{id}` | `GET` | Owner/Admin | Fetch order details |
| `/orders` | `POST` | Authenticated | Create order and reserve stock |
| `/payments` | `POST` | Owner | Process simulated payment for order |
| `/admin/status` | `GET` | Admin | Verify admin role access |
| `/admin/users` | `GET` | Admin | List users for admin management |
| `/admin/vendors` | `GET` | Admin | List vendors for admin management |
| `/admin/orders` | `GET` | Admin | List orders for admin management |
| `/admin/vendors/{id}/suspend` | `PATCH` | Admin | Mark vendor account inactive |
| `/admin/products/{id}/deactivate` | `PATCH` | Admin | Deactivate a product |

---

## 4. Frontend Functionality That Can Already Be Implemented
1. **Public Browsing & Search**: Home page, catalog view with price filter, text search, and multi-field sorting.
2. **Customer Shopping Cart**: Client-side cart using React state/`localStorage` allowing multi-item accumulation before creating an order (`POST /orders`).
3. **Authentication Flow**: User registration with role selection (`CUSTOMER` or `VENDOR`), JWT token acquisition and storage in `localStorage`, role extraction from JWT claims, and secure logout.
4. **Order Management & Payments**: View personal order history, view itemized order details, process simulated payment (`POST /payments`), update status to `CONFIRMED`.
5. **Vendor Management**: Store setup prompt for new vendors, product listing, standalone create/edit pages and modal forms, product deletion, subscription upgrade.
6. **Admin Moderation**: Platform statistics, user audit table, vendor list with suspend action, order list view, product list with deactivate action.

---

## 5. Functionality Blocked by Missing Backend Endpoints
1. **Dedicated User Profile Endpoint (`GET /users/me`)**:
   - *Impact*: No direct endpoint to refresh user profile data.
   - *Resolution*: Decoded standard claims (`sub` email, `role`) directly from the JWT payload using `atob()`.
2. **Order Status Management (`PATCH /orders/{id}`)**:
   - *Impact*: Order status changes occur exclusively via payment processing (`POST /payments`). Manual cancellation or order status updates are not exposed.
   - *Resolution*: Customer UI provides simulated payment to transition status from `PENDING` to `CONFIRMED`.
3. **Vendor Profile Update (`PATCH /vendors/{id}`)**:
   - *Impact*: Vendor store names cannot be updated after creation.
   - *Resolution*: Store creation is supported once per vendor user; updates are omitted.

---

## 6. Inconsistencies Between Backend Schemas and Expected Frontend Data
1. **Order Items in Response**: Originally, `OrderResponse` omitted itemized product details (`items`).
   - *Resolution*: Updated `OrderResponse` schema in backend to include `items: List[OrderItemResponse]` and `created_at` field, populating them with `joinedload(Order.items)`.
2. **Single Product Retrieval Endpoint**: Frontend deep links to `/vendor/products/:id/edit` require fetching a single product's state.
   - *Resolution*: Added a lightweight `GET /products/{id}` endpoint to `app/routers/products.py`.
3. **Hardcoded API URLs**: Frontend components previously hardcoded `http://localhost:8000`.
   - *Resolution*: Refactored API client calls to utilize `import.meta.env.VITE_API_URL || "http://localhost:8000"` and created `.env.example`.

---

## 7. Existing Frontend Code That Should Be Reused
- `src/components/Navbar.jsx`: Clean top navigation bar with role-aware badge and link rendering.
- `src/components/ProductCard.jsx`: High quality card component formatting stock and prices.
- `src/components/ProtectedRoute.jsx`: Effective route guard enforcing JWT presence and role eligibility.
- `src/pages/Home.jsx`: Public landing page with hero banner and feature overview.

---

## 8. Existing Frontend Code That Should Be Replaced or Restructured
- **Monolithic Dashboard Pages**: `VendorDashboard.jsx` and `AdminDashboard.jsx` previously bundled all sub-views into single components.
  - *Restructuring*: Extracted sub-views into dedicated route components (`VendorProducts.jsx`, `CreateProduct.jsx`, `EditProduct.jsx`, `AdminUsers.jsx`, `AdminVendors.jsx`, `AdminOrders.jsx`, `OrderDetails.jsx`) while maintaining consolidated dashboards as summary hubs.
- **Standalone Reusable Components**: Extracted reusable `Loading.jsx` and `ErrorMessage.jsx` components as specified in project structure requirements.

---

## 9. Final Recommended Implementation Structure
```text
frontend/
├── src/
│   ├── components/
│   │   ├── Navbar.jsx
│   │   ├── ProductCard.jsx
│   │   ├── Loading.jsx
│   │   ├── ErrorMessage.jsx
│   │   └── ProtectedRoute.jsx
│   │
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Products.jsx
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── MyOrders.jsx
│   │   ├── OrderDetails.jsx
│   │   ├── VendorDashboard.jsx
│   │   ├── VendorProducts.jsx
│   │   ├── CreateProduct.jsx
│   │   ├── EditProduct.jsx
│   │   ├── AdminDashboard.jsx
│   │   ├── AdminUsers.jsx
│   │   ├── AdminVendors.jsx
│   │   └── AdminOrders.jsx
│   │
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
│
├── .env
├── .env.example
├── package.json
├── vite.config.js
└── README.md
```
