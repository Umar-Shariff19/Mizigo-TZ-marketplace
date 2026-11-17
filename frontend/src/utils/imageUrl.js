import { API_URL } from "../config";

export function resolveImageUrl(src) {
  if (!src) return null;
  if (
    src.startsWith("http://") ||
    src.startsWith("https://") ||
    src.startsWith("blob:") ||
    src.startsWith("data:")
  ) {
    return src;
  }
  const baseUrl = (API_URL || "").replace(/\/+$/, "");
  const cleanPath = src.startsWith("/") ? src : `/${src}`;
  return `${baseUrl}${cleanPath}`;
}
