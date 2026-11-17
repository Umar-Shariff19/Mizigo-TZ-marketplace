export default function ErrorMessage({ message, onRetry }) {
  if (!message) return null;

  return (
    <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl text-sm mb-6 flex flex-wrap items-center justify-between gap-3 shadow-xs">
      <div className="flex items-center space-x-2">
        <span className="font-bold text-base">⚠️</span>
        <span>{message}</span>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="bg-red-100 hover:bg-red-200 text-red-800 text-xs font-semibold px-3 py-1.5 rounded transition"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
