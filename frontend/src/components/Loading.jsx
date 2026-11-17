export default function Loading({ message = "Loading..." }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
      <p className="mt-4 text-sm font-medium text-slate-600">{message}</p>
    </div>
  );
}
