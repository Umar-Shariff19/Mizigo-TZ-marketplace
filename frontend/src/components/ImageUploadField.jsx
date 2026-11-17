import { useState, useRef, useEffect } from "react";
import ProductImage from "./ProductImage";

const MAX_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const ALLOWED_EXTS = [".jpg", ".jpeg", ".png", ".webp"];

export default function ImageUploadField({
  currentImageUrl,
  onFileSelect,
  onRemoveCurrent,
  onError,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXTS.includes(ext)) {
      if (onError) {
        onError("Unsupported image format. Please select a JPEG, PNG, or WebP image.");
      }
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      if (onError) {
        onError("File size exceeds 5 MB. Please choose a smaller image.");
      }
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    if (file.size === 0) {
      if (onError) {
        onError("Selected file is empty. Please choose a valid image.");
      }
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    if (onError) onError("");
    setSelectedFile(file);

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    onFileSelect(file);
  }

  function handleRemoveSelected() {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    if (inputRef.current) inputRef.current.value = "";
    onFileSelect(null);
    if (onError) onError("");
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-slate-700">
        Product Image <span className="text-xs text-slate-400 font-normal">(optional)</span>
      </label>

      {/* Existing image display (when editing) */}
      {currentImageUrl && !previewUrl && (
        <div className="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <div className="w-16 h-16 rounded-lg overflow-hidden bg-white border border-slate-200 shrink-0">
            <ProductImage src={currentImageUrl} alt="Current product" />
          </div>
          <div className="flex-1 min-w-0">
            <span className="text-xs font-semibold text-slate-800 block">Current Image</span>
            <span className="text-xs text-slate-500">Select a new image below to replace it.</span>
          </div>
          {onRemoveCurrent && (
            <button
              type="button"
              onClick={onRemoveCurrent}
              className="text-xs font-semibold text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 px-3 py-1.5 rounded transition cursor-pointer"
            >
              Remove
            </button>
          )}
        </div>
      )}

      {/* Selected file preview */}
      {previewUrl && (
        <div className="flex items-center gap-3 p-3 bg-amber-50/60 border border-amber-200 rounded-lg">
          <div className="w-16 h-16 rounded-lg overflow-hidden bg-white border border-amber-300 shrink-0">
            <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
          </div>
          <div className="flex-1 min-w-0">
            <span className="text-xs font-bold text-slate-900 block truncate">
              {selectedFile?.name}
            </span>
            <span className="text-xs text-slate-500">
              {selectedFile ? (selectedFile.size / (1024 * 1024)).toFixed(2) : 0} MB • Ready to upload
            </span>
          </div>
          <button
            type="button"
            onClick={handleRemoveSelected}
            className="text-xs font-semibold text-slate-600 hover:text-red-600 bg-white hover:bg-red-50 border border-slate-300 px-3 py-1.5 rounded transition cursor-pointer"
          >
            ✕ Remove
          </button>
        </div>
      )}

      {/* File input */}
      <div className="flex items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          id="productImageInput"
          accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
          onChange={handleFileChange}
          className="block w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 cursor-pointer border border-slate-300 rounded-lg p-1.5"
        />
      </div>

      <p className="text-xs text-slate-400">
        Supported formats: JPEG, PNG, WebP (Max size: 5 MB)
      </p>
    </div>
  );
}
