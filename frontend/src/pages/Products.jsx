import { useState, useEffect } from "react";
import { API_URL } from "../config";
import ProductCard from "../components/ProductCard";
import ProductImage from "../components/ProductImage";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Pagination & Filter params
  const [page, setPage] = useState(0);
  const limit = 8;
  const [searchTerm, setSearchTerm] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [sortBy, setSortBy] = useState("");
  const [sortOrder, setSortOrder] = useState("asc");

  // Persistent Cart state (localStorage)
  const [cart, setCart] = useState(() => {
    try {
      const saved = localStorage.getItem("mizigo_cart");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [showCartDrawer, setShowCartDrawer] = useState(false);

  // Single Order / Modal state
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [orderQuantity, setOrderQuantity] = useState(1);
  const [orderLoading, setOrderLoading] = useState(false);
  const [orderMessage, setOrderMessage] = useState("");
  const [createdOrder, setCreatedOrder] = useState(null);

  // Payment modal state
  const [paymentProvider, setPaymentProvider] = useState("razorpay");
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState("");

  const token = localStorage.getItem("token");

  useEffect(() => {
    localStorage.setItem("mizigo_cart", JSON.stringify(cart));
  }, [cart]);

  useEffect(() => {
    fetchProducts();
  }, [page, sortBy, sortOrder]);

  async function fetchProducts() {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();
      params.append("skip", page * limit);
      params.append("limit", limit);
      if (searchTerm) params.append("search", searchTerm);
      if (minPrice) params.append("min_price", minPrice);
      if (maxPrice) params.append("max_price", maxPrice);
      if (sortBy) params.append("sort_by", sortBy);
      if (sortOrder) params.append("sort_order", sortOrder);

      const response = await fetch(`${API_URL}/products?${params.toString()}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || "Failed to fetch products");
      }

      setProducts(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleFilterSubmit(e) {
    e.preventDefault();
    setPage(0);
    fetchProducts();
  }

  function addToCart(product) {
    setCart((prevCart) => {
      const existing = prevCart.find((item) => item.product.id === product.id);
      if (existing) {
        return prevCart.map((item) =>
          item.product.id === product.id
            ? { ...item, quantity: Math.min(item.quantity + 1, product.quantity_available) }
            : item
        );
      }
      return [...prevCart, { product, quantity: 1 }];
    });
    setShowCartDrawer(true);
  }

  function updateCartQuantity(productId, quantity) {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCart((prevCart) =>
      prevCart.map((item) =>
        item.product.id === productId ? { ...item, quantity } : item
      )
    );
  }

  function removeFromCart(productId) {
    setCart((prevCart) => prevCart.filter((item) => item.product.id !== productId));
  }

  function clearCart() {
    setCart([]);
  }

  async function handleCheckoutCart() {
    if (!token) {
      alert("Please log in to place an order.");
      return;
    }

    if (cart.length === 0) return;

    setOrderLoading(true);
    setOrderMessage("");

    try {
      const itemsPayload = cart.map((item) => ({
        product_id: item.product.id,
        quantity: item.quantity,
      }));

      const res = await fetch(`${API_URL}/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ items: itemsPayload }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Checkout failed");
      }

      setCreatedOrder(data);
      setCart([]);
      setShowCartDrawer(false);
      setOrderMessage("Cart order placed successfully! Proceed to simulated payment.");
      fetchProducts();
    } catch (err) {
      setOrderMessage(`Checkout error: ${err.message}`);
    } finally {
      setOrderLoading(false);
    }
  }

  function openBuyNowModal(product) {
    if (!token) {
      alert("Please log in to place an order.");
      return;
    }
    setSelectedProduct(product);
    setOrderQuantity(1);
    setOrderMessage("");
    setCreatedOrder(null);
    setPaymentStatus("");
  }

  async function handleSingleBuySubmit(e) {
    e.preventDefault();
    if (!selectedProduct) return;

    setOrderLoading(true);
    setOrderMessage("");

    try {
      const res = await fetch(`${API_URL}/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          items: [{ product_id: selectedProduct.id, quantity: Number(orderQuantity) }],
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to create order");
      }

      setCreatedOrder(data);
      setOrderMessage("Order created! You can now complete simulated payment.");
      fetchProducts();
    } catch (err) {
      setOrderMessage(`Error: ${err.message}`);
    } finally {
      setOrderLoading(false);
    }
  }

  async function handleProcessPayment() {
    if (!createdOrder) return;

    setPaymentLoading(true);
    setPaymentStatus("");

    try {
      const res = await fetch(`${API_URL}/payments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          order_id: createdOrder.id,
          provider: paymentProvider,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Payment failed");
      }

      setPaymentStatus(`Payment Successful! Order status: ${data.order_status}`);
      setTimeout(() => {
        setSelectedProduct(null);
        setCreatedOrder(null);
      }, 2000);
    } catch (err) {
      setPaymentStatus(`Payment Error: ${err.message}`);
    } finally {
      setPaymentLoading(false);
    }
  }

  const cartTotal = cart.reduce(
    (sum, item) => sum + Number(item.product.price) * item.quantity,
    0
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header & Cart Button */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900">Marketplace Catalog</h1>
          <p className="text-slate-500 text-sm mt-1">
            Browse products, filter by price, manage your cart, and place orders.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowCartDrawer(!showCartDrawer)}
            className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-sm px-4 py-2 rounded-xl shadow-xs transition flex items-center gap-2"
          >
            <span>🛒</span>
            <span>Cart</span>
            {cart.length > 0 && (
              <span className="bg-slate-950 text-amber-400 text-xs px-2 py-0.5 rounded-full">
                {cart.reduce((sum, item) => sum + item.quantity, 0)}
              </span>
            )}
          </button>

          <button
            onClick={fetchProducts}
            className="bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold px-4 py-2 rounded-xl shadow-xs transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm mb-8">
        <form onSubmit={handleFilterSubmit} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-slate-500 mb-1">Search Keywords</label>
            <input
              type="text"
              placeholder="Search product names & descriptions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-500 mb-1">Min Price ($)</label>
            <input
              type="number"
              placeholder="0"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-500 mb-1">Max Price ($)</label>
            <input
              type="number"
              placeholder="1000"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 outline-none"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-2 px-4 rounded-lg text-sm transition"
            >
              Apply Filters
            </button>
          </div>
        </form>

        {/* Sort Controls */}
        <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-600 gap-2">
          <div className="flex items-center space-x-3">
            <span className="font-bold text-slate-700">Sort By:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white font-medium"
            >
              <option value="">Default (ID)</option>
              <option value="id">Product ID</option>
              <option value="name">Name</option>
              <option value="price">Price</option>
            </select>

            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white font-medium"
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </div>
        </div>
      </div>

      <ErrorMessage message={error} onRetry={fetchProducts} />

      {/* Product List */}
      {loading ? (
        <Loading message="Fetching products from Mizigo API..." />
      ) : products.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500 shadow-xs">
          No products found matching your filter criteria.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={addToCart}
                onBuyClick={openBuyNowModal}
              />
            ))}
          </div>

          {/* Pagination Controls */}
          <div className="mt-8 flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className={`px-4 py-2 text-xs font-bold rounded-lg transition ${
                page === 0
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-slate-200 hover:bg-slate-300 text-slate-800"
              }`}
            >
              ← Previous Page
            </button>
            <span className="text-xs font-bold text-slate-600">
              Page {page + 1}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={products.length < limit}
              className={`px-4 py-2 text-xs font-bold rounded-lg transition ${
                products.length < limit
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-slate-200 hover:bg-slate-300 text-slate-800"
              }`}
            >
              Next Page →
            </button>
          </div>
        </>
      )}

      {/* Persistent Shopping Cart Modal / Drawer */}
      {showCartDrawer && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex justify-end z-50">
          <div className="bg-white max-w-md w-full h-full p-6 shadow-2xl flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex justify-between items-center border-b border-slate-100 pb-4 mb-4">
                <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                  <span>🛒</span> Shopping Cart
                </h3>
                <button
                  onClick={() => setShowCartDrawer(false)}
                  className="text-slate-400 hover:text-slate-600 font-bold text-lg"
                >
                  ✕
                </button>
              </div>

              {cart.length === 0 ? (
                <p className="text-sm text-slate-500 py-8 text-center">Your shopping cart is empty.</p>
              ) : (
                <div className="space-y-4 divide-y divide-slate-100">
                  {cart.map(({ product, quantity }) => (
                    <div key={product.id} className="pt-3 flex justify-between items-center">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-md overflow-hidden bg-slate-100 border border-slate-200 shrink-0">
                          <ProductImage src={product.image_url} alt={product.name} />
                        </div>
                        <div>
                          <div className="font-bold text-slate-800 text-sm line-clamp-1">{product.name}</div>
                          <div className="text-xs text-amber-600 font-extrabold mt-0.5">
                            ${Number(product.price).toFixed(2)} each
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => updateCartQuantity(product.id, quantity - 1)}
                          className="w-6 h-6 bg-slate-100 text-slate-700 font-bold rounded flex items-center justify-center hover:bg-slate-200"
                        >
                          -
                        </button>
                        <span className="text-sm font-semibold">{quantity}</span>
                        <button
                          onClick={() => updateCartQuantity(product.id, quantity + 1)}
                          disabled={quantity >= product.quantity_available}
                          className="w-6 h-6 bg-slate-100 text-slate-700 font-bold rounded flex items-center justify-center hover:bg-slate-200 disabled:opacity-50"
                        >
                          +
                        </button>
                        <button
                          onClick={() => removeFromCart(product.id)}
                          className="text-red-500 hover:text-red-700 text-xs font-bold ml-2"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {cart.length > 0 && (
              <div className="pt-4 border-t border-slate-200 space-y-3">
                <div className="flex justify-between text-base font-extrabold text-slate-900">
                  <span>Total Amount:</span>
                  <span className="text-amber-600">${cartTotal.toFixed(2)}</span>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={clearCart}
                    className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg"
                  >
                    Clear Cart
                  </button>
                  <button
                    onClick={handleCheckoutCart}
                    disabled={orderLoading}
                    className="flex-2 py-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-bold rounded-lg shadow"
                  >
                    {orderLoading ? "Placing Order..." : "Checkout Order"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Buy Now / Order Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-slate-900">Place Direct Order</h3>
              <button onClick={() => setSelectedProduct(null)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            <div className="bg-slate-50 p-3 rounded-lg mb-4 text-sm flex items-center gap-3">
              <div className="w-16 h-16 rounded-lg overflow-hidden bg-white border border-slate-200 shrink-0">
                <ProductImage src={selectedProduct.image_url} alt={selectedProduct.name} />
              </div>
              <div>
                <div className="font-bold text-slate-900">{selectedProduct.name}</div>
                <div className="text-amber-600 font-extrabold mt-0.5">${Number(selectedProduct.price).toFixed(2)}</div>
                <div className="text-xs text-slate-500 mt-0.5">Available Stock: {selectedProduct.quantity_available} units</div>
              </div>
            </div>

            {!createdOrder ? (
              <form onSubmit={handleSingleBuySubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    max={selectedProduct.quantity_available}
                    value={orderQuantity}
                    onChange={(e) => setOrderQuantity(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
                  />
                </div>

                <div className="text-sm font-extrabold text-slate-900">
                  Total Amount: ${(Number(selectedProduct.price) * orderQuantity).toFixed(2)}
                </div>

                {orderMessage && (
                  <div className="text-xs p-2.5 rounded-lg bg-amber-50 text-amber-900 border border-amber-200 font-medium">
                    {orderMessage}
                  </div>
                )}

                <div className="flex space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setSelectedProduct(null)}
                    className="w-1/2 py-2 border border-slate-300 text-slate-700 rounded-lg text-sm font-semibold hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={orderLoading}
                    className="w-1/2 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-lg text-sm shadow"
                  >
                    {orderLoading ? "Ordering..." : "Confirm Order"}
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4 pt-2">
                <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs p-3 rounded-lg font-medium">
                  Order #{createdOrder.id} created! Total: ${Number(createdOrder.total_amount).toFixed(2)}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Payment Provider</label>
                  <select
                    value={paymentProvider}
                    onChange={(e) => setPaymentProvider(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-sm focus:ring-2 focus:ring-amber-500 outline-none"
                  >
                    <option value="razorpay">Razorpay</option>
                    <option value="stripe">Stripe</option>
                    <option value="mpesa">M-Pesa</option>
                  </select>
                </div>

                {paymentStatus && (
                  <div className="text-xs p-3 rounded-lg bg-indigo-50 text-indigo-800 border border-indigo-200 font-medium">
                    {paymentStatus}
                  </div>
                )}

                <button
                  onClick={handleProcessPayment}
                  disabled={paymentLoading}
                  className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg text-sm transition shadow"
                >
                  {paymentLoading ? "Processing Payment..." : "Pay Now (Simulated)"}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
