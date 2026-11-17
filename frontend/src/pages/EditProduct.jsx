import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { API_URL } from "../config";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";
import ImageUploadField from "../components/ImageUploadField";

export default function EditProduct() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [isActive, setIsActive] = useState(true);

  // Image management state
  const [currentImageUrl, setCurrentImageUrl] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [imageRemoved, setImageRemoved] = useState(false);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submittingStep, setSubmittingStep] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchProduct();
  }, [id]);

  async function fetchProduct() {
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_URL}/products/${id}`);
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.message || "Product not found");
      }

      setName(data.name);
      setDescription(data.description || "");
      setPrice(data.price);
      setIsActive(data.is_active);
      setCurrentImageUrl(data.image_url || null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleRemoveCurrentImage() {
    setCurrentImageUrl(null);
    setImageRemoved(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setSuccess("");
    setSubmittingStep("");

    try {
      // 1. If a new image was chosen, upload and replace it
      if (imageFile) {
        setSubmittingStep("Uploading new image...");
        const formData = new FormData();
        formData.append("file", imageFile);

        const imgRes = await fetch(`${API_URL}/vendor/products/${id}/image`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        const imgData = await imgRes.json();
        if (!imgRes.ok) {
          throw new Error(imgData.detail || "Failed to update product image");
        }
      } else if (imageRemoved) {
        // 2. If existing image was explicitly removed, delete it
        setSubmittingStep("Removing previous image...");
        const delRes = await fetch(`${API_URL}/vendor/products/${id}/image`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const delData = await delRes.json();
        if (!delRes.ok) {
          throw new Error(delData.detail || "Failed to remove product image");
        }
      }

      // 3. Update main product details
      setSubmittingStep("Saving product details...");
      const res = await fetch(`${API_URL}/vendor/products/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          description,
          price: parseFloat(price),
          is_active: isActive,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to update product");
      }

      setSuccess("Product updated successfully! Redirecting...");
      setTimeout(() => {
        navigate("/vendor/products");
      }, 1200);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
      setSubmittingStep("");
    }
  }

  if (loading) return <Loading message="Loading product data..." />;

  return (
    <div className="max-w-xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link to="/vendor/products" className="text-sm font-semibold text-amber-600 hover:text-amber-700">
          ← Back to Vendor Products
        </Link>
      </div>

      <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-md">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Edit Product #{id}</h2>
        <p className="text-sm text-slate-500 mb-6">
          Update the product details, pricing, image, or active status.
        </p>

        <ErrorMessage message={error} onRetry={fetchProduct} />

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
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea
              rows="3"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Price ($)</label>
            <input
              type="number"
              step="0.01"
              required
              min="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
            />
          </div>

          <div className="flex items-center space-x-2 pt-2">
            <input
              type="checkbox"
              id="isActiveCheck"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 rounded text-amber-500 focus:ring-amber-500 border-slate-300"
            />
            <label htmlFor="isActiveCheck" className="text-sm font-medium text-slate-700 cursor-pointer">
              Product Listing Active Status
            </label>
          </div>

          {/* Product Image Update / Replace */}
          <div className="pt-2 border-t border-slate-100">
            <ImageUploadField
              currentImageUrl={currentImageUrl}
              onFileSelect={(file) => {
                setImageFile(file);
                if (file) setImageRemoved(false);
              }}
              onRemoveCurrent={handleRemoveCurrentImage}
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
              disabled={submitting}
              className="w-1/2 py-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg transition shadow text-sm disabled:opacity-50 cursor-pointer"
            >
              {submitting ? (submittingStep || "Saving...") : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
