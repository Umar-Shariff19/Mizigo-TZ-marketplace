import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import Home from "./pages/Home";
import Products from "./pages/Products";
import Login from "./pages/Login";
import Register from "./pages/Register";
import MyOrders from "./pages/MyOrders";
import OrderDetails from "./pages/OrderDetails";
import VendorDashboard from "./pages/VendorDashboard";
import VendorProducts from "./pages/VendorProducts";
import CreateProduct from "./pages/CreateProduct";
import EditProduct from "./pages/EditProduct";
import AdminDashboard from "./pages/AdminDashboard";
import AdminUsers from "./pages/AdminUsers";
import AdminVendors from "./pages/AdminVendors";
import AdminOrders from "./pages/AdminOrders";

export default function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
        <Navbar />

        <main className="flex-1">
          <Routes>
            {/* Public Marketplace Routes */}
            <Route path="/" element={<Home />} />
            <Route path="/products" element={<Products />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Customer Protected Routes */}
            <Route
              path="/orders/me"
              element={
                <ProtectedRoute allowedRoles={["CUSTOMER", "VENDOR", "ADMIN"]}>
                  <MyOrders />
                </ProtectedRoute>
              }
            />
            <Route
              path="/orders/:id"
              element={
                <ProtectedRoute allowedRoles={["CUSTOMER", "VENDOR", "ADMIN"]}>
                  <OrderDetails />
                </ProtectedRoute>
              }
            />

            {/* Vendor Protected Routes */}
            <Route
              path="/vendor/dashboard"
              element={
                <ProtectedRoute allowedRoles={["CUSTOMER", "VENDOR"]}>
                  <VendorDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/vendor/products"
              element={
                <ProtectedRoute allowedRoles={["VENDOR"]}>
                  <VendorProducts />
                </ProtectedRoute>
              }
            />
            <Route
              path="/vendor/products/new"
              element={
                <ProtectedRoute allowedRoles={["VENDOR"]}>
                  <CreateProduct />
                </ProtectedRoute>
              }
            />
            <Route
              path="/vendor/products/:id/edit"
              element={
                <ProtectedRoute allowedRoles={["VENDOR"]}>
                  <EditProduct />
                </ProtectedRoute>
              }
            />

            {/* Admin Protected Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <AdminUsers />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/vendors"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <AdminVendors />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/orders"
              element={
                <ProtectedRoute allowedRoles={["ADMIN"]}>
                  <AdminOrders />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>

        {/* Persistent Footer */}
        <footer className="bg-slate-900 text-slate-400 border-t border-slate-800 text-xs py-6 mt-12">
          <div className="max-w-7xl mx-auto px-4 flex justify-between items-center">
            <div>© {new Date().getFullYear()} Mizigo TZ Marketplace. All rights reserved.</div>
            <div>Built with React, Vite, Tailwind CSS, & FastAPI</div>
          </div>
        </footer>
      </div>
    </Router>
  );
}
