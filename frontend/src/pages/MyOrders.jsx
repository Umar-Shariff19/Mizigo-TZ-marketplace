import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { API_URL } from "../config";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function MyOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [paymentProvider, setPaymentProvider] = useState("razorpay");
  const [payingOrderId, setPayingOrderId] = useState(null);
  const [paymentMsg, setPaymentMsg] = useState("");

  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchOrders();
  }, []);

  async function fetchOrders() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/orders/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || "Failed to fetch orders");
      }

      setOrders(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleQuickPay(orderId) {
    setPayingOrderId(orderId);
    setPaymentMsg("");

    try {
      const response = await fetch(`${API_URL}/payments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          order_id: orderId,
          provider: paymentProvider,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.message || "Payment processing failed");
      }

      setPaymentMsg(`Payment Successful for Order #${orderId}! Status updated to ${data.order_status}`);
      fetchOrders();
    } catch (err) {
      setPaymentMsg(`Error: ${err.message}`);
    } finally {
      setPayingOrderId(null);
    }
  }

  if (loading) return <Loading message="Loading your order history..." />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900">My Orders</h1>
          <p className="text-slate-500 text-sm mt-1">Track your order history, view details, and complete payments.</p>
        </div>
        <button
          onClick={fetchOrders}
          className="bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition"
        >
          Refresh Orders
        </button>
      </div>

      <ErrorMessage message={error} onRetry={fetchOrders} />

      {paymentMsg && (
        <div className="bg-emerald-50 text-emerald-800 border border-emerald-200 text-sm p-4 rounded-xl mb-6 font-medium">
          {paymentMsg}
        </div>
      )}

      {orders.length === 0 ? (
        <div className="bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-500">
          <p className="text-lg font-bold text-slate-700 mb-2">No Orders Placed Yet</p>
          <p className="text-sm text-slate-500 mb-6">Explore our catalog and place your first order!</p>
          <Link
            to="/products"
            className="inline-block bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-6 py-2.5 rounded-lg shadow transition text-sm"
          >
            Browse Products
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 font-bold text-slate-700 text-sm">
            Order History ({orders.length})
          </div>

          <div className="divide-y divide-slate-200">
            {orders.map((order) => (
              <div key={order.id} className="p-5 flex flex-wrap items-center justify-between gap-4 hover:bg-slate-50 transition">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="font-extrabold text-slate-900 text-lg">Order #{order.id}</span>
                    <span
                      className={`text-xs font-bold px-3 py-0.5 rounded-full ${
                        order.status === "CONFIRMED"
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                          : order.status === "PENDING"
                          ? "bg-amber-100 text-amber-800 border border-amber-200"
                          : "bg-red-100 text-red-800 border border-red-200"
                      }`}
                    >
                      {order.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    Customer ID: #{order.user_id} {order.items?.length > 0 && `• ${order.items.length} items`}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xl font-extrabold text-amber-600">
                    ${Number(order.total_amount).toFixed(2)}
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Link
                    to={`/orders/${order.id}`}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold px-4 py-2 rounded-lg transition"
                  >
                    View Details
                  </Link>

                  {order.status === "PENDING" && (
                    <div className="flex items-center space-x-2">
                      <select
                        value={paymentProvider}
                        onChange={(e) => setPaymentProvider(e.target.value)}
                        className="text-xs px-2 py-1.5 border border-slate-300 rounded-lg bg-white"
                      >
                        <option value="razorpay">Razorpay</option>
                        <option value="stripe">Stripe</option>
                        <option value="mpesa">M-Pesa</option>
                      </select>
                      <button
                        onClick={() => handleQuickPay(order.id)}
                        disabled={payingOrderId === order.id}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition shadow-xs"
                      >
                        {payingOrderId === order.id ? "Paying..." : "Pay Now"}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
