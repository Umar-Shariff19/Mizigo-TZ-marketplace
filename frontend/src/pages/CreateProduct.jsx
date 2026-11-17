import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_URL } from "../config";
import ErrorMessage from "../components/ErrorMessage";
import ImageUploadField from "../components/ImageUploadField";

export default function CreateProduct() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [imageFile, setImageFile] = useState(null);

  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const token = localStorage.getItem("token");

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");
    setLoadingStep("");

    try {
      let imageUrl = null;

      // 1. If an image file was selected, upload it first
      if (imageFile) {
        setLoadingStep("Uploading product image...");
        const formData = new FormData();
        formData.append("file", imageFile);

        const uploadRes = await fetch(`${API_URL}/products/upload-image`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        const uploadData = await uploadRes.json();
        if (!uploadRes.ok) {
          throw new Error(uploadData.detail || "Failed to upload product image");
        }
        imageUrl = uploadData.image_url;
      }

      // 2. Create the product record with optional image_url
      setLoadingStep("Saving product...");
      const res = await fetch(`${API_URL}/products`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          description,
          price: parseFloat(price),
          quantity: parseInt(quantity, 10),
          image_url: imageUrl,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to create product");
      }

      setSuccess("Product created successfully! Redirecting...");
      setTimeout(() => {
        navigate("/vendor/products");
      }, 1200);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link to="/vendor/products" className="text-sm font-semibold text-amber-600 hover:text-amber-700">
          ← Back to Vendor Products
        </Link>
      </div>

      <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-md">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">List New Product</h2>
        <p className="text-sm text-slate-500 mb-6">
          Fill in the product details and starting stock quantity to add it to the marketplace.
        </p>

        <ErrorMessage message={error} />

        {success && (
          <div className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-sm p-3 rounded-lg mb-4">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Product Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Wireless Ergonomic Mouse"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea
              rows="3"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detailed description of features, compatibility, etc."
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Price ($)</label>
              <input
                type="number"
                step="0.01"
                required
                min="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="29.99"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Initial Stock</label>
              <input
                type="number"
                required
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="50"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
              />
            </div>
          </div>

          {/* Product Image Upload Field with preview & validation */}
          <div className="pt-2 border-t border-slate-100">
            <ImageUploadField
              onFileSelect={setImageFile}
              onError={setError}
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={() => navigate("/vendor/products")}
              className="w-1/2 py-2.5 border border-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition text-sm cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="w-1/2 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-lg transition shadow text-sm disabled:opacity-50 cursor-pointer"
            >
              {loading ? (loadingStep || "Creating...") : "Save Product"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
