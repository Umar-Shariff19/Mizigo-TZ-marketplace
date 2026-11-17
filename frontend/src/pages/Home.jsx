import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { API_URL } from "../config";
import ProductCard from "../components/ProductCard";

export default function Home() {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem("token");
  const userRole = localStorage.getItem("userRole");

  useEffect(() => {
    fetchFeatured();
  }, []);

  async function fetchFeatured() {
    try {
      const res = await fetch(`${API_URL}/products?limit=4`);
      const data = await res.json();
      if (res.ok) {
        setFeaturedProducts(data);
      }
    } catch {
      // Ignore initial home fetch error gracefully
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      {/* Hero Banner */}
      <div className="bg-slate-900 text-white rounded-2xl p-8 md:p-12 shadow-xl mb-12 relative overflow-hidden">
        <div className="max-w-2xl relative z-10">
          <span className="inline-block bg-amber-500 text-slate-950 font-bold text-xs uppercase px-3 py-1 rounded-full mb-4">
            FastAPI + React Marketplace
          </span>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4 leading-tight">
            Discover Quality Products on Mizigo TZ
          </h1>
          <p className="text-slate-300 text-lg mb-8 leading-relaxed">
            Your reliable marketplace for local products, vendor stores, and seamless order delivery across Tanzania.
          </p>

          <div className="flex flex-wrap gap-4">
            <Link
              to="/products"
              className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-6 py-3 rounded-xl shadow-md transition"
            >
              Browse Products
            </Link>

            {!token ? (
              <Link
                to="/register"
                className="bg-slate-800 hover:bg-slate-700 text-white font-semibold px-6 py-3 rounded-xl border border-slate-700 transition"
              >
                Create Account
              </Link>
            ) : userRole === "VENDOR" ? (
              <Link
                to="/vendor/dashboard"
                className="bg-slate-800 hover:bg-slate-700 text-white font-semibold px-6 py-3 rounded-xl border border-slate-700 transition"
              >
                Manage My Store
              </Link>
            ) : userRole === "ADMIN" ? (
              <Link
                to="/admin"
                className="bg-slate-800 hover:bg-slate-700 text-white font-semibold px-6 py-3 rounded-xl border border-slate-700 transition"
              >
                Admin Control Panel
              </Link>
            ) : (
              <Link
                to="/orders/me"
                className="bg-slate-800 hover:bg-slate-700 text-white font-semibold px-6 py-3 rounded-xl border border-slate-700 transition"
              >
                View My Orders
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Featured Products Section */}
      {featuredProducts.length > 0 && (
        <div className="mb-12">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-extrabold text-slate-900">Featured Products</h2>
              <p className="text-sm text-slate-500">Explore recent listings from verified vendors</p>
            </div>
            <Link to="/products" className="text-sm font-bold text-amber-600 hover:text-amber-700">
              View All Products →
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      )}

      {/* Marketplace Value Proposition */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-12 h-12 bg-amber-100 text-amber-700 rounded-lg flex items-center justify-center font-bold text-xl mb-4">
            🛍️
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">Customer Shopping</h3>
          <p className="text-slate-600 text-sm">
            Search products, filter by price, accumulate items in your cart, and process simulated payments safely.
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-lg flex items-center justify-center font-bold text-xl mb-4">
            🏪
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">Vendor Stores</h3>
          <p className="text-slate-600 text-sm">
            Create your vendor store profile, manage inventory, list new products, and track total revenue.
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-12 h-12 bg-indigo-100 text-indigo-700 rounded-lg flex items-center justify-center font-bold text-xl mb-4">
            ⚡
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">FastAPI Backend</h3>
          <p className="text-slate-600 text-sm">
            Powered by high-performance REST APIs, JWT OAuth2 authentication, and transactional database integrity.
          </p>
        </div>
      </div>
    </div>
  );
}
