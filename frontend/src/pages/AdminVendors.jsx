import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { API_URL } from "../config";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function AdminVendors() {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchVendors();
  }, []);

  async function fetchVendors() {
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/admin/vendors`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to fetch vendors");
      }

      setVendors(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSuspendVendor(id) {
    if (!window.confirm(`Are you sure you want to suspend vendor store #${id}?`)) return;

    try {
      const res = await fetch(`${API_URL}/admin/vendors/${id}/suspend`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to suspend vendor");
      }

      fetchVendors();
    } catch (err) {
      alert(`Suspend failed: ${err.message}`);
    }
  }

  if (loading) return <Loading message="Loading vendor stores..." />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900">Vendor Management</h1>
          <p className="text-slate-500 text-sm mt-1">Review vendor store profiles and enforce moderation status.</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to="/admin"
            className="bg-slate-200 hover:bg-slate-300 text-slate-800 text-sm font-semibold px-4 py-2 rounded-lg transition"
          >
            ← Admin Hub
          </Link>
          <button
            onClick={fetchVendors}
            className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold px-4 py-2 rounded-lg shadow transition"
          >
            Refresh
          </button>
        </div>
      </div>

      <ErrorMessage message={error} onRetry={fetchVendors} />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-slate-700 text-sm">
          Vendor Stores ({vendors.length})
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-100 text-slate-700 uppercase text-xs">
              <tr>
                <th className="py-3 px-4">Vendor ID</th>
                <th className="py-3 px-4">Store Name</th>
                <th className="py-3 px-4">Owner User ID</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {vendors.map((v) => (
                <tr key={v.id} className="hover:bg-slate-50 transition">
                  <td className="py-3 px-4 font-mono text-xs text-slate-500">#{v.id}</td>
                  <td className="py-3 px-4 font-bold text-slate-900">{v.store_name}</td>
                  <td className="py-3 px-4 font-mono text-xs text-slate-600">User #{v.user_id}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                        v.is_active ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
                      }`}
                    >
                      {v.is_active ? "Active" : "Suspended"}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    {v.is_active ? (
                      <button
                        onClick={() => handleSuspendVendor(v.id)}
                        className="bg-red-100 hover:bg-red-200 text-red-700 text-xs font-semibold px-3 py-1.5 rounded transition"
                      >
                        Suspend Vendor
                      </button>
                    ) : (
                      <span className="text-xs text-slate-400 italic">Suspended</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
