import { useState } from "react";
import { resolveImageUrl } from "../utils/imageUrl";

export default function ProductImage({
  src,
  alt = "Product",
  className = "w-full h-full object-cover",
  placeholderClassName = "w-full h-full flex flex-col items-center justify-center text-slate-400 bg-slate-100",
}) {
  const [failedSrc, setFailedSrc] = useState(null);
  const fullUrl = resolveImageUrl(src);
  const hasError = failedSrc === fullUrl;

  if (!fullUrl || hasError) {
    return (
      <div className={placeholderClassName} role="img" aria-label={alt || "Product placeholder"}>
        <svg
          className="w-10 h-10 text-slate-300 mb-1"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"
          />
        </svg>
        <span className="text-xs font-medium text-slate-400">No Image</span>
      </div>
    );
  }

  return (
    <img
      src={fullUrl}
      alt={alt}
      className={className}
      onError={() => setFailedSrc(fullUrl)}
      loading="lazy"
    />
  );
}
