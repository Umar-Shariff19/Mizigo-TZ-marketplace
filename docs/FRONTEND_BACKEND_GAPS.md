# Mizigo Frontend-Backend Gap Analysis & Resolutions

This document details the functional alignment between the React frontend UI and the FastAPI backend endpoints, including identified gaps, resolutions, and safe backend modifications made.

---

## 1. Mapped Endpoint Integrations

All active frontend features are strictly mapped to existing, validated FastAPI endpoints:

| Feature / UI Flow | Backend Endpoint | HTTP Method | Auth Required | Status |
| :--- | :--- | :--- | :--- | :--- |
| User Registration | `/users` | `POST` | Public | Active |
| User Login | `/login` | `POST` | Public | Active |
| List Marketplace Products | `/products` | `GET` | Public | Active |
| Get Single Product | `/products/{id}` | `GET` | Public | Added & Active |
| Create Product | `/products` | `POST` | Vendor | Active |
| List Vendor Products | `/vendor/products` | `GET` | Vendor | Active |
| Update Vendor Product | `/vendor/products/{id}` | `PATCH` | Vendor | Active |
| Delete Vendor Product | `/vendor/products/{id}` | `DELETE` | Vendor | Active |
| Vendor Dashboard Metrics | `/vendor/dashboard` | `GET` | Vendor | Active |
| Create Vendor Store Profile | `/vendors` | `POST` | Vendor | Active |
| List Vendor Stores | `/vendors` | `GET` | Public | Active |
| Upgrade Vendor Subscription | `/vendors/upgrade` | `POST` | Vendor | Active |
| Create Customer Order | `/orders` | `POST` | Authenticated | Active |
| View My Orders | `/orders/me` | `GET` | Authenticated | Active |
| View Single Order Details | `/orders/{id}` | `GET` | Owner/Admin | Active |
| Process Simulated Payment | `/payments` | `POST` | Owner | Active |
| Check Admin Status | `/admin/status` | `GET` | Admin | Active |
| Admin List Users | `/admin/users` | `GET` | Admin | Active |
| Admin List Vendors | `/admin/vendors` | `GET` | Admin | Active |
| Admin List Orders | `/admin/orders` | `GET` | Admin | Active |
| Admin Suspend Vendor | `/admin/vendors/{id}/suspend` | `PATCH` | Admin | Active |
| Admin Deactivate Product | `/admin/products/{id}/deactivate` | `PATCH` | Admin | Active |

---

## 2. Identified Gaps & Backend Modifications Made

### 1. Order Itemization in Order Responses (`OrderResponse` Schema)
- **Gap Identified**: `OrderResponse` previously returned only `id`, `user_id`, `status`, and `total_amount`, omitting order items (`items`) and timestamp (`created_at`).
- **Resolution**: Updated `app/schemas/order.py` to include `items: List[OrderItemResponse]` and `created_at`. Updated `list_my_orders`, `get_order`, and `list_admin_orders` to eager-load `joinedload(Order.items)`.

### 2. Single Product Details Lookup (`GET /products/{id}`)
- **Gap Identified**: Direct linking to `/vendor/products/:id/edit` required fetching a single product's state by ID.
- **Resolution**: Added a lightweight, safe `GET /products/{id}` endpoint in `app/routers/products.py`.

### 3. User Profile Endpoint (`GET /users/me`)
- **Gap Identified**: There is no dedicated `/users/me` endpoint.
- **Resolution**: Per prompt directives, no fake endpoint was invented. The frontend extracts user `email` (`sub`) and `role` from the signed JWT payload in `localStorage` using standard Base64 decoding (`atob`).

### 4. Client-Side Persistent Cart
- **Gap Identified**: The backend does not maintain server-side cart tables.
- **Resolution**: Implemented client-side persistent cart in React state backed by `localStorage` (`mizigo_cart`). When the user checks out, the cart generates the standard request body for `POST /orders` (`{ items: [{ product_id, quantity }] }`).

---

## 3. Remaining Limitations

1. **Vendor Store Profile Editing (`PATCH /vendors/{id}`)**: Vendors can create a store profile (`POST /vendors`), but editing the store name post-creation is not currently supported by backend routers.
2. **Order Status Updates**: Order status transitions exclusively from `PENDING` to `CONFIRMED` upon payment (`POST /payments`). Manual cancellation or delivery status updates remain out of scope for the backend.
