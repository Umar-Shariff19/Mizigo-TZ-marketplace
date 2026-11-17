import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";

export default function Navbar({ cartCount = 0 }) {
  const navigate = useNavigate();
  useLocation();
  const [, setAuthSync] = useState(0);

  const token = localStorage.getItem("token");
  const userRole = localStorage.getItem("userRole");
  const userEmail = localStorage.getItem("userEmail");

  useEffect(() => {
    function syncAuth() {
      setAuthSync((prev) => prev + 1);
    }
    window.addEventListener("storage", syncAuth);
    return () => window.removeEventListener("storage", syncAuth);
  }, []);

  function handleLogout() {
    localStorage.removeItem("token");
    localStorage.removeItem("userRole");
    localStorage.removeItem("userEmail");
    setAuthSync((prev) => prev + 1);
    navigate("/login");
  }

  return (
    <nav className="bg-slate-900 text-white shadow-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand Logo */}
        <Link to="/" className="text-xl font-extrabold tracking-wide text-amber-400 hover:text-amber-300 flex items-center gap-2">
          <span>📦</span> Mizigo TZ Marketplace
        </Link>

        {/* Navigation Links */}
        <div className="flex flex-wrap items-center space-x-1 sm:space-x-4 text-sm">
          <Link to="/" className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition">
            Home
          </Link>

          <Link to="/products" className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition">
            Products
          </Link>

          {/* Customer Links */}
          {token && (userRole === "CUSTOMER" || !userRole) && (
            <>
              <Link to="/orders/me" className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition">
                My Orders
              </Link>
              <Link to="/vendor/dashboard" className="px-3 py-1.5 rounded-lg text-amber-300 hover:text-amber-200 hover:bg-slate-800 transition font-medium">
                Become a Seller
              </Link>
            </>
          )}

          {/* Vendor Links */}
          {token && userRole === "VENDOR" && (
            <>
              <Link to="/vendor/dashboard" className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition">
                Vendor Dashboard
              </Link>
              <Link to="/vendor/products" className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition">
                My Products
              </Link>
            </>
          )}

          {/* Admin Links */}
          {token && userRole === "ADMIN" && (
            <div className="flex items-center space-x-1">
              <Link to="/admin" className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition">
                Admin Hub
              </Link>
              <Link to="/admin/users" className="px-2 py-1.5 text-xs rounded text-slate-400 hover:text-white hover:bg-slate-800 transition">
                Users
              </Link>
              <Link to="/admin/vendors" className="px-2 py-1.5 text-xs rounded text-slate-400 hover:text-white hover:bg-slate-800 transition">
                Vendors
              </Link>
              <Link to="/admin/orders" className="px-2 py-1.5 text-xs rounded text-slate-400 hover:text-white hover:bg-slate-800 transition">
                Orders
              </Link>
            </div>
          )}

          {/* Auth State Control */}
          {token ? (
            <div className="flex items-center space-x-3 ml-2">
              <span className="text-xs bg-slate-800 text-slate-300 px-3 py-1 rounded-full border border-slate-700 hidden sm:inline-block">
                {userEmail} <span className="font-bold text-amber-400">({userRole})</span>
              </span>
              <button
                onClick={handleLogout}
                className="bg-red-600 hover:bg-red-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center space-x-2 ml-2">
              <Link
                to="/login"
                className="text-slate-300 hover:text-white px-3 py-1.5 rounded-lg text-xs font-medium transition"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-3 py-1.5 rounded-lg text-xs transition"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
