import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { API_URL } from "../config";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function AdminDashboard() {
  const [adminStatus, setAdminStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [users, setUsers] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);

  const token = localStorage.getItem("token");

  useEffect(() => {
    loadAdminOverview();
  }, []);

  async function loadAdminOverview() {
    setLoading(true);
    setError("");

    try {
      const statusRes = await fetch(`${API_URL}/admin/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!statusRes.ok) {
        throw new Error("Forbidden: Admin access required");
      }
      setAdminStatus("Admin Authorization Verified");

      const [usersRes, vendorsRes, ordersRes, productsRes] = await Promise.all([
        fetch(`${API_URL}/admin/users`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/admin/vendors`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/admin/orders`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/products`),
      ]);

      if (usersRes.ok) setUsers(await usersRes.json());
      if (vendorsRes.ok) setVendors(await vendorsRes.json());
      if (ordersRes.ok) setOrders(await ordersRes.json());
      if (productsRes.ok) setProducts(await productsRes.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSuspendVendor(vendorId) {
    if (!window.confirm(`Are you sure you want to suspend vendor store #${vendorId}?`)) return;

    try {
      const res = await fetch(`${API_URL}/admin/vendors/${vendorId}/suspend`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to suspend vendor");
      }

      loadAdminOverview();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  }

  async function handleDeactivateProduct(productId) {
    if (!window.confirm(`Are you sure you want to deactivate product #${productId}?`)) return;

    try {
      const res = await fetch(`${API_URL}/admin/products/${productId}/deactivate`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to deactivate product");
      }

      loadAdminOverview();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  }

  if (loading) return <Loading message="Loading Admin Panel..." />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900">Admin Control Center</h1>
          <p className="text-slate-500 text-sm mt-1">Platform administration, user management, and moderation controls.</p>
        </div>

        {adminStatus && (
          <span className="text-xs bg-emerald-100 text-emerald-800 font-bold px-3 py-1.5 rounded-full border border-emerald-200">
            ✓ {adminStatus}
          </span>
        )}
      </div>

      <ErrorMessage message={error} onRetry={loadAdminOverview} />

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Link to="/admin/users" className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-amber-400 transition">
          <div className="text-xs uppercase font-extrabold tracking-wider text-slate-400">Total Users</div>
          <div className="text-4xl font-extrabold text-slate-900 mt-2">{users.length}</div>
          <div className="text-xs font-bold text-amber-600 mt-2">Manage Users →</div>
        </Link>

        <Link to="/admin/vendors" className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-amber-400 transition">
          <div className="text-xs uppercase font-extrabold tracking-wider text-slate-400">Registered Vendors</div>
          <div className="text-4xl font-extrabold text-slate-900 mt-2">{vendors.length}</div>
          <div className="text-xs font-bold text-amber-600 mt-2">Manage Vendors →</div>
        </Link>

        <Link to="/admin/orders" className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-amber-400 transition">
          <div className="text-xs uppercase font-extrabold tracking-wider text-slate-400">Total Orders</div>
          <div className="text-4xl font-extrabold text-slate-900 mt-2">{orders.length}</div>
          <div className="text-xs font-bold text-amber-600 mt-2">Manage Orders →</div>
        </Link>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs uppercase font-extrabold tracking-wider text-slate-400">Platform Products</div>
          <div className="text-4xl font-extrabold text-slate-900 mt-2">{products.length}</div>
          <div className="text-xs font-semibold text-slate-500 mt-2">Active Catalog</div>
        </div>
      </div>

      {/* Admin Quick Action Hub */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Vendors List & Suspend */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-slate-700 text-sm flex justify-between items-center">
            <span>Vendor Accounts ({vendors.length})</span>
            <Link to="/admin/vendors" className="text-xs font-bold text-amber-600 hover:text-amber-700">
              View All Vendors →
            </Link>
          </div>
          <div className="divide-y divide-slate-100">
            {vendors.slice(0, 5).map((v) => (
              <div key={v.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition text-sm">
                <div>
                  <div className="font-bold text-slate-900">{v.store_name}</div>
                  <div className="text-xs text-slate-500">User #{v.user_id}</div>
                </div>
                <div className="flex items-center space-x-3">
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                      v.is_active ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
                    }`}
                  >
                    {v.is_active ? "Active" : "Suspended"}
                  </span>
                  {v.is_active && (
                    <button
                      onClick={() => handleSuspendVendor(v.id)}
                      className="bg-red-100 hover:bg-red-200 text-red-700 text-xs font-semibold px-2.5 py-1 rounded transition"
                    >
                      Suspend
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Product Catalog Deactivation */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-slate-700 text-sm flex justify-between items-center">
            <span>Platform Product Moderation ({products.length})</span>
          </div>
          <div className="divide-y divide-slate-100">
            {products.slice(0, 5).map((p) => (
              <div key={p.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition text-sm">
                <div>
                  <div className="font-bold text-slate-900">{p.name}</div>
                  <div className="text-xs text-amber-600 font-extrabold">${Number(p.price).toFixed(2)}</div>
                </div>
                <div className="flex items-center space-x-3">
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                      p.is_active ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {p.is_active ? "Active" : "Deactivated"}
                  </span>
                  {p.is_active && (
                    <button
                      onClick={() => handleDeactivateProduct(p.id)}
                      className="bg-amber-100 hover:bg-amber-200 text-amber-800 text-xs font-semibold px-2.5 py-1 rounded transition"
                    >
                      Deactivate
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
