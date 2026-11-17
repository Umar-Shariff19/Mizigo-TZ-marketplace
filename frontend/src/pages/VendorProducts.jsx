import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { API_URL } from "../config";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";
import ProductImage from "../components/ProductImage";

export default function VendorProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchVendorProducts();
  }, []);

  async function fetchVendorProducts() {
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/vendor/products`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to fetch vendor products");
      }

      setProducts(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteProduct(id) {
    if (!window.confirm(`Are you sure you want to delete product #${id}?`)) return;

    try {
      const res = await fetch(`${API_URL}/vendor/products/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to delete product");
      }

      fetchVendorProducts();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  }

  if (loading) return <Loading message="Loading vendor catalog..." />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900">Vendor Products</h1>
          <p className="text-slate-500 text-sm mt-1">Manage your store's inventory and active product listings.</p>
        </div>

        <div className="flex space-x-3">
          <Link
            to="/vendor/dashboard"
            className="bg-slate-200 hover:bg-slate-300 text-slate-800 text-sm font-semibold px-4 py-2 rounded-lg transition"
          >
            ← Dashboard Hub
          </Link>
          <Link
            to="/vendor/products/new"
            className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-sm px-4 py-2 rounded-lg shadow transition"
          >
            + Create New Product
          </Link>
        </div>
      </div>

      <ErrorMessage message={error} onRetry={fetchVendorProducts} />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-slate-700 text-sm flex justify-between items-center">
          <span>Catalog Items ({products.length})</span>
        </div>

        {products.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            You have no products listed. Click "+ Create New Product" to get started.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-100 text-slate-700 uppercase text-xs">
                <tr>
                  <th className="py-3 px-4">Image</th>
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">Name</th>
                  <th className="py-3 px-4">Price</th>
                  <th className="py-3 px-4">Stock</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-4">
                      <div className="w-12 h-12 rounded-lg overflow-hidden bg-slate-100 border border-slate-200 shrink-0">
                        <ProductImage
                          src={p.image_url}
                          alt={p.name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-500">#{p.id}</td>
                    <td className="py-3 px-4 font-semibold text-slate-900">{p.name}</td>
                    <td className="py-3 px-4 text-amber-600 font-extrabold">${Number(p.price).toFixed(2)}</td>
                    <td className="py-3 px-4 font-medium">{p.quantity_available} units</td>
                    <td className="py-3 px-4">
                      <span
                        className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                          p.is_active ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {p.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <Link
                        to={`/vendor/products/${p.id}/edit`}
                        className="inline-block bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold px-3 py-1.5 rounded transition"
                      >
                        Edit
                      </Link>
                      <button
                        onClick={() => handleDeleteProduct(p.id)}
                        className="bg-red-100 hover:bg-red-200 text-red-700 text-xs font-semibold px-3 py-1.5 rounded transition"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
