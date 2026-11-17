# Mizigo Frontend Code Walkthrough & Architectural Guide

This document presents a comprehensive walkthrough of the Mizigo React frontend codebase. It explains components, props, state management, side effects, API integration, routing, and role-based authentication in intermediate-level React terms.

---

## 1. Modular Directory Layout

The application code resides in `frontend/src`:

```text
frontend/src/
├── components/
│   ├── Navbar.jsx          # Top navigation bar with role-aware links, cart badge, & logout
│   ├── ProductCard.jsx     # Reusable presentation card with Add to Cart & Buy Now CTAs
│   ├── Loading.jsx         # Accessible loading spinner & message indicator
│   ├── ErrorMessage.jsx    # Alert box component with optional retry action handler
│   └── ProtectedRoute.jsx  # Client-side route guard enforcing token & role criteria
│
├── pages/
│   ├── Home.jsx            # Public marketplace landing page & featured items
│   ├── Products.jsx        # Catalog browsing, search, price filters, sorting, & cart
│   ├── Login.jsx           # OAuth2 login form with JWT decoding & storage
│   ├── Register.jsx        # Account registration form (Customer / Vendor)
│   ├── MyOrders.jsx        # Customer order history with quick payment action
│   ├── OrderDetails.jsx    # Itemized order details & payment processor
│   ├── VendorDashboard.jsx # Vendor hub displaying revenue metrics & store setup
│   ├── VendorProducts.jsx  # Vendor product table with edit & delete actions
│   ├── CreateProduct.jsx   # Standalone product creation form for vendors
│   ├── EditProduct.jsx     # Standalone product edit form for vendors
│   ├── AdminDashboard.jsx  # Platform management hub & stat summaries
│   ├── AdminUsers.jsx      # Admin table auditing all registered users
│   ├── AdminVendors.jsx    # Admin table auditing vendors with suspension control
│   └── AdminOrders.jsx     # Admin table auditing platform orders
│
├── config.js               # Exporting VITE_API_URL environment configuration
├── App.jsx                 # Central router with protected route definitions
├── main.jsx                # Entry point mounting React root
└── index.css               # Tailwind CSS imports & global resets
```

---

## 2. Route Configuration (`App.jsx`)

The application routes are structured with `react-router-dom`:

- **Public Routes**: `/`, `/products`, `/login`, `/register`.
- **Customer Protected Routes**: `/orders/me`, `/orders/:id` (Allowed: `CUSTOMER`, `VENDOR`, `ADMIN`).
- **Vendor Protected Routes**: `/vendor/dashboard`, `/vendor/products`, `/vendor/products/new`, `/vendor/products/:id/edit` (Allowed: `VENDOR`).
- **Admin Protected Routes**: `/admin`, `/admin/users`, `/admin/vendors`, `/admin/orders` (Allowed: `ADMIN`).

---

## 3. State Management & Hooks

1. **`useState`**: Used within pages for local UI state:
   - `loading` and `error` states for handling API call status.
   - Form inputs (`email`, `password`, `name`, `price`, `quantity`).
   - Catalog controls (`page`, `searchTerm`, `minPrice`, `maxPrice`, `sortBy`, `sortOrder`).
   - Shopping cart state (`cart`), synchronized with `localStorage`.

2. **`useEffect`**: Triggers data loading side-effects upon component mounting or when dependencies change (e.g. `fetchProducts` triggers whenever `page`, `sortBy`, or `sortOrder` changes).

---

## 4. API Communication (`fetch` & `VITE_API_URL`)

API requests use the native browser `fetch` API. The API URL is dynamically retrieved from Vite environment variables (`import.meta.env.VITE_API_URL || "http://localhost:8000"`).

### Example GET Request:
```javascript
const res = await fetch(`${API_URL}/products?skip=${page * limit}&limit=${limit}`);
const data = await res.json();
if (!res.ok) throw new Error(data.detail || "Failed to fetch products");
setProducts(data);
```

### Example Authenticated POST Request:
```javascript
const token = localStorage.getItem("token");

const res = await fetch(`${API_URL}/orders`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  },
  body: JSON.stringify({ items: [{ product_id: 1, quantity: 2 }] }),
});
```

---

## 5. JWT Authentication & Role Decoding

- **Token Storage**: When `POST /login` succeeds, the JWT string is stored in `localStorage.getItem("token")`.
- **Claims Decoding**: In `Login.jsx`, standard Base64 decoding (`atob`) extracts the payload to retrieve `role` (`CUSTOMER`, `VENDOR`, `ADMIN`) and `userEmail` (`sub`).
- **Route Authorization**: `ProtectedRoute.jsx` reads `token` and `userRole` from `localStorage`. If missing or invalid, it redirects the user to `/login` or `/products`.

---

## 6. Tailwind Styling & User Interface

- Built with Tailwind CSS v4 utility classes.
- Vibrant, modern color palette: Slate dark backgrounds (`bg-slate-900`), Amber highlights (`text-amber-500`, `bg-amber-500`), Emerald statuses (`text-emerald-600`), and clean Slate borders (`border-slate-200`).
- Fully responsive design using Tailwind break-points (`sm:`, `md:`, `lg:`).
