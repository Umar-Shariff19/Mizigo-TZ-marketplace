import ProductImage from "./ProductImage";

export default function ProductCard({ product, onAddToCart, onBuyClick }) {
  const isOutOfStock = product.quantity_available <= 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition p-5 flex flex-col justify-between">
      <div>
        <div className="w-full h-44 rounded-lg overflow-hidden bg-slate-100 mb-4 flex items-center justify-center border border-slate-100">
          <ProductImage
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover hover:scale-105 transition duration-300"
          />
        </div>

        <div className="flex items-start justify-between gap-2">
          <h3 className="text-lg font-bold text-slate-900 line-clamp-1">
            {product.name}
          </h3>
          <span className="text-lg font-extrabold text-amber-600 whitespace-nowrap">
            ${Number(product.price).toFixed(2)}
          </span>
        </div>

        <p className="text-slate-600 text-sm mt-2 line-clamp-2 min-h-[2.5rem]">
          {product.description || "No description provided."}
        </p>

        <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500 space-y-1">
          <div className="flex justify-between">
            <span>Vendor ID:</span>
            <span className="font-semibold text-slate-700">#{product.vendor_id}</span>
          </div>
          <div className="flex justify-between">
            <span>Inventory:</span>
            <span className={`font-bold ${isOutOfStock ? "text-red-500" : "text-emerald-600"}`}>
              {isOutOfStock ? "Out of Stock" : `${product.quantity_available} left`}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Status:</span>
            <span className={`font-semibold ${product.is_active ? "text-emerald-600" : "text-amber-600"}`}>
              {product.is_active ? "Active" : "Inactive"}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-5 pt-3 border-t border-slate-100 flex gap-2">
        {onAddToCart && (
          <button
            onClick={() => onAddToCart(product)}
            disabled={isOutOfStock || !product.is_active}
            className={`flex-1 py-2 px-3 rounded-lg font-semibold text-xs transition ${
              isOutOfStock || !product.is_active
                ? "bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200"
                : "bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300"
            }`}
          >
            + Add to Cart
          </button>
        )}
        {onBuyClick && (
          <button
            onClick={() => onBuyClick(product)}
            disabled={isOutOfStock || !product.is_active}
            className={`flex-1 py-2 px-3 rounded-lg font-bold text-xs transition ${
              isOutOfStock || !product.is_active
                ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                : "bg-amber-500 hover:bg-amber-600 text-slate-950 shadow-xs"
            }`}
          >
            {isOutOfStock ? "Sold Out" : "Buy Now"}
          </button>
        )}
      </div>
    </div>
  );
}
