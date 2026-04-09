import type { PriorityItem } from "@/lib/api-client";

export default function PriorityPanel({ items }: { items: PriorityItem[] }) {
  return (
    <section className="glass-card panel-shell rounded-[28px] p-5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D8AB5]">Financial Priority Engine</p>
      <h3 className="mt-1.5 text-[16px] font-bold text-white">Recommended actions</h3>

      <div className="mt-5 space-y-3">
        {items.map((item, index) => (
          <div key={`${item.title}-${index}`} className="rounded-2xl border border-white/8 bg-white/5 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-[#edf2ff]">{item.title}</p>
              <span className="rounded-full bg-white/8 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#b8c2e7]">{item.level}</span>
            </div>
            <p className="mt-2 text-xs leading-5 text-[#97a3c5]">{item.message}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
