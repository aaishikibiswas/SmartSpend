export default function Loading() {
  return (
    <div className="flex flex-col gap-6 animate-pulse">
      <div className="h-40 w-full rounded-[42px] bg-white/5 border border-white/5" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 rounded-2xl bg-white/5 border border-white/5" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[400px] rounded-3xl bg-white/5 border border-white/5" />
        <div className="h-[400px] rounded-3xl bg-white/5 border border-white/5" />
      </div>
    </div>
  );
}
