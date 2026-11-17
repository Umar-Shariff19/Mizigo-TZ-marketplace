import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { API_URL } from "../config";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";
import ProductImage from "../components/ProductImage";

export default function VendorDashboard() {
  const [dashboardMetrics, setDashboardMetrics] = useState(null);
  const [vendorProducts, setVendorProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [upgradeMsg, setUpgradeMsg] = useState("");

  const [storeName, setStoreName] = useState("");
  const [storeCreating, setStoreCreating] = useState(false);
  const token = localStorage.getItem("token");
  const userRole = localStorage.getItem("userRole");
  const [hasVendorStore, setHasVendorStore] = useState(userRole === "VENDOR");

  useEffect(() => {
    loadVendorData();
  }, []);

  async function loadVendorData() {
    setLoading(true);
    setError("");

    try {
      const dashRes = await fetch(`${API_URL}/vendor/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const dashData = await dashRes.json();

      if (!dashRes.ok) {
        if (
          (dashRes.status === 400 && dashData.detail === "Vendor not found") ||
          (dashRes.status === 403 && dashData.detail === "Only vendors allowed")
        ) {
          setHasVendorStore(false);
          setLoading(false);
          return;
        }
        throw new Error(dashData.detail || "Failed to load vendor dashboard");
      }

      setHasVendorStore(true);
      setDashboardMetrics(dashData);

      const prodRes = await fetch(`${API_URL}/vendor/products`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const prodData = await prodRes.json();
      if (prodRes.ok) {
        setVendorProducts(prodData);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateStore(e) {
    e.preventDefault();
    setStoreCreating(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/vendors`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ store_name: storeName }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to create vendor store");
      }

      localStorage.setItem("userRole", "VENDOR");
      window.dispatchEvent(new Event("storage"));
      setHasVendorStore(true);
      await loadVendorData();
    } catch (err) {
      setError(err.message);
    } finally {
      setStoreCreating(false);
    }
  }

  async function handleUpgradeSubscription() {
    setUpgradeMsg("");
    try {
      const res = await fetch(`${API_URL}/vendors/upgrade`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Subscription upgrade failed");
      }

      setUpgradeMsg(`Upgraded to PRO Plan! Subscription Expiry: ${new Date(data.expiry).toLocaleDateString()}`);
    } catch (err) {
      setUpgradeMsg(`Upgrade Error: ${err.message}`);
    }
  }

  if (loading) return <Loading message="Loading Vendor Dashboard..." />;

  if (!hasVendorStore) {
    return (
      <div className="max-w-md mx-auto my-12 px-4">
        <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-md">
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Create Vendor Store</h2>
          <p className="text-sm text-slate-500 mb-6">
            Set up your official store name to start selling and listing items on Mizigo Marketplace.
          </p>

          <ErrorMessage message={error} />

          <form onSubmit={handleCreateStore} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Store Name</label>
              <input
                type="text"
                required
                value={storeName}
                onChange={(e) => setStoreName(e.target.value)}
                placeholder="e.g. Mizigo Tech Supplies"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
              />
            </div>
            <button
              type="submit"
              disabled={storeCreating}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-lg transition text-sm shadow"
            >
              {storeCreating ? "Creating Store..." : "Create Vendor Store"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header & Sub Upgrade */}
      <div className="flex flex-wrap justify-between items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900">Vendor Control Hub</h1>
          <p className="text-slate-500 text-sm mt-1">Manage products, inventory, revenue metrics, and subscription plan.</p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleUpgradeSubscription}
            className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-sm px-4 py-2 rounded-lg shadow transition"
          >
            Upgrade to PRO (30 Days)
          </button>
          <Link
            to="/vendor/products/new"
            className="bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm px-4 py-2 rounded-lg shadow transition"
          >
            + Create Product
          </Link>
          <Link
            to="/vendor/products"
            className="bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold text-sm px-4 py-2 rounded-lg transition"
          >
            Manage Catalog
          </Link>
        </div>
      </div>

      <ErrorMessage message={error} onRetry={loadVendorData} />

      {upgradeMsg && (
        <div className="bg-amber-50 border border-amber-200 text-amber-900 p-4 rounded-xl mb-6 text-sm font-medium">
          {upgradeMsg}
        </div>
      )}

      {/* Metrics Cards */}
      {dashboardMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs uppercase font-extrabold tracking-wider text-slate-400">Total Products Listed</div>
            <div className="text-4xl font-extrabold text-slate-900 mt-2">{dashboardMetrics.total_products}</div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs uppercase font-extrabold tracking-wider text-slate-400">Total Orders Received</div>
            <div className="text-4xl font-extrabold text-slate-900 mt-2">{dashboardMetrics.total_orders}</div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs uppercase font-extrabold tracking-wider text-slate-400">Gross Sales Revenue</div>
            <div className="text-4xl font-extrabold text-emerald-600 mt-2">
              ${Number(dashboardMetrics.total_revenue).toFixed(2)}
            </div>
          </div>
        </div>
      )}

      {/* Vendor Products Preview */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-slate-700 text-sm flex justify-between items-center">
          <span>Active Product Catalog ({vendorProducts.length})</span>
          <Link to="/vendor/products" className="text-xs font-bold text-amber-600 hover:text-amber-700">
            View Full Catalog →
          </Link>
        </div>

        {vendorProducts.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No products listed yet. Click "+ Create Product" to list your first item.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {vendorProducts.slice(0, 5).map((p) => (
              <div key={p.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg overflow-hidden bg-slate-100 border border-slate-200 shrink-0">
                    <ProductImage src={p.image_url} alt={p.name} />
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 text-sm">{p.name}</div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Stock: <span className="font-semibold text-slate-700">{p.quantity_available} units</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-amber-600 font-extrabold text-sm">${Number(p.price).toFixed(2)}</span>
                  <Link
                    to={`/vendor/products/${p.id}/edit`}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold px-3 py-1.5 rounded transition"
                  >
                    Edit
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
