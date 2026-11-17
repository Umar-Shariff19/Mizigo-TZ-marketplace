import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { API_URL } from "../config";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchUsers();
  }, []);

  async function fetchUsers() {
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to fetch users");
      }

      setUsers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <Loading message="Loading platform users..." />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900">User Management</h1>
          <p className="text-slate-500 text-sm mt-1">Platform user accounts audit and role distribution.</p>
        </div>
        <div className="flex space-x-3">
          <Link
            to="/admin"
            className="bg-slate-200 hover:bg-slate-300 text-slate-800 text-sm font-semibold px-4 py-2 rounded-lg transition"
          >
            ← Admin Hub
          </Link>
          <button
            onClick={fetchUsers}
            className="bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold px-4 py-2 rounded-lg shadow transition"
          >
            Refresh
          </button>
        </div>
      </div>

      <ErrorMessage message={error} onRetry={fetchUsers} />

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-slate-700 text-sm">
          Registered Accounts ({users.length})
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-100 text-slate-700 uppercase text-xs">
              <tr>
                <th className="py-3 px-4">User ID</th>
                <th className="py-3 px-4">Email Address</th>
                <th className="py-3 px-4">Account Role</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50 transition">
                  <td className="py-3 px-4 font-mono text-xs text-slate-500">#{u.id}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{u.email}</td>
                  <td className="py-3 px-4">
                    <span className="bg-slate-100 text-slate-800 border border-slate-200 text-xs px-2.5 py-1 rounded-full font-bold">
                      {u.role}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-bold ${
                        u.is_active ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
                      }`}
                    >
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
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
