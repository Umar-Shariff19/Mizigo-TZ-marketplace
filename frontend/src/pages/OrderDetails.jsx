import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { API_URL } from "../config";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function OrderDetails() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [paymentProvider, setPaymentProvider] = useState("razorpay");
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [paymentMsg, setPaymentMsg] = useState("");

  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchOrderDetails();
  }, [id]);

  async function fetchOrderDetails() {
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/orders/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to fetch order details");
      }

      setOrder(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handlePayment() {
    setPaymentLoading(true);
    setPaymentMsg("");

    try {
      const res = await fetch(`${API_URL}/payments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          order_id: Number(id),
          provider: paymentProvider,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Payment failed");
      }

      setPaymentMsg(`Payment successful! Order status: ${data.order_status}`);
      fetchOrderDetails();
    } catch (err) {
      setPaymentMsg(`Error: ${err.message}`);
    } finally {
      setPaymentLoading(false);
    }
  }

  async function handleCancelOrder() {
    if (!window.confirm("Are you sure you want to cancel this order? This will release reserved stock.")) return;
    try {
      const res = await fetch(`${API_URL}/orders/${id}/cancel`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to cancel order");
      }
      setPaymentMsg("Order cancelled successfully. Stock released.");
      fetchOrderDetails();
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <Loading message="Loading order details..." />;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <Link to="/orders/me" className="text-sm font-semibold text-amber-600 hover:text-amber-700 flex items-center gap-1">
          ← Back to My Orders
        </Link>
        <button
          onClick={fetchOrderDetails}
          className="text-xs bg-slate-200 hover:bg-slate-300 text-slate-800 px-3 py-1.5 rounded transition"
        >
          Refresh
        </button>
      </div>

      <ErrorMessage message={error} onRetry={fetchOrderDetails} />

      {order && (
        <div className="space-y-6">
          {/* Order Header Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <div className="flex flex-wrap justify-between items-start gap-4 pb-4 border-b border-slate-100">
              <div>
                <h1 className="text-2xl font-extrabold text-slate-900">Order #{order.id}</h1>
                <p className="text-xs text-slate-500 mt-1">Customer User ID: #{order.user_id}</p>
                {order.created_at && (
                  <p className="text-xs text-slate-400 mt-0.5">
                    Placed on: {new Date(order.created_at).toLocaleString()}
                  </p>
                )}
              </div>

              <div className="text-right">
                <span
                  className={`inline-block text-xs font-bold px-3 py-1 rounded-full uppercase ${
                    order.status === "CONFIRMED"
                      ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                      : order.status === "PENDING"
                      ? "bg-amber-100 text-amber-800 border border-amber-200"
                      : "bg-red-100 text-red-800 border border-red-200"
                  }`}
                >
                  {order.status}
                </span>
                <div className="text-2xl font-extrabold text-amber-600 mt-2">
                  ${Number(order.total_amount).toFixed(2)}
                </div>
              </div>
            </div>

            {/* Itemized Products */}
            <div className="mt-6">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">
                Order Items ({order.items?.length || 0})
              </h3>

              {order.items && order.items.length > 0 ? (
                <div className="divide-y divide-slate-100 border border-slate-100 rounded-lg overflow-hidden">
                  {order.items.map((item) => (
                    <div key={item.id} className="p-4 flex justify-between items-center bg-slate-50/50">
                      <div>
                        <div className="font-semibold text-slate-800 text-sm">Product #{item.product_id}</div>
                        <div className="text-xs text-slate-500 mt-0.5">Vendor ID: #{item.vendor_id}</div>
                      </div>
                      <div className="text-right text-sm">
                        <div className="font-medium text-slate-700">
                          {item.quantity} × ${Number(item.price_at_purchase).toFixed(2)}
                        </div>
                        <div className="font-bold text-slate-900 mt-0.5">
                          ${(item.quantity * Number(item.price_at_purchase)).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 bg-slate-50 p-4 rounded-lg">No item detail available.</p>
              )}
            </div>
          </div>

          {/* Payment Section if PENDING */}
          {order.status === "PENDING" && (
            <div className="bg-amber-50/60 border border-amber-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-amber-900 mb-2">Complete Payment</h3>
              <p className="text-xs text-amber-700 mb-4">
                This order is pending payment. Select a payment provider to simulate transaction completion.
              </p>

              <div className="max-w-xs space-y-3">
                <select
                  value={paymentProvider}
                  onChange={(e) => setPaymentProvider(e.target.value)}
                  className="w-full px-3 py-2 border border-amber-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-amber-500 outline-none"
                >
                  <option value="razorpay">Razorpay</option>
                  <option value="stripe">Stripe</option>
                  <option value="mpesa">M-Pesa</option>
                </select>

                {paymentMsg && (
                  <div className="text-xs p-3 rounded-lg bg-white border border-amber-300 text-slate-800 font-medium">
                    {paymentMsg}
                  </div>
                )}

                <button
                  onClick={handlePayment}
                  disabled={paymentLoading}
                  className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg text-sm transition shadow"
                >
                  {paymentLoading ? "Processing Payment..." : "Pay Now (Simulated)"}
                </button>

                <button
                  onClick={handleCancelOrder}
                  className="w-full py-2 border border-red-300 hover:bg-red-50 text-red-700 font-semibold rounded-lg text-xs transition"
                >
                  Cancel Order & Release Items
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
