import type { ExpenseSplitData } from "@/lib/api-client";

export default function ExpenseSplitCard({ data }: { data: ExpenseSplitData }) {
  return (
    <section className="glass-card panel-shell rounded-[28px] p-5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D8AB5]">Expense Split</p>
      <h3 className="mt-1.5 text-[16px] font-bold text-white">Fixed vs Variable</h3>

      <div className="mt-5 space-y-4">
        {data.breakdown.map((item) => {
          const percent = item.name === "Fixed" ? data.fixed_percent : data.variable_percent;
          return (
            <div key={item.name}>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="font-semibold text-[#edf2ff]">{item.name}</span>
                <span className="text-[#a8b1ce]">Rs. {Number(item.amount || 0).toLocaleString()} · {percent}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-white/8">
                <div
                  className={`h-full rounded-full ${item.name === "Fixed" ? "bg-[#8B7DFF]" : "bg-[#6ec7ff]"}`}
                  style={{ width: `${Math.max(6, Math.min(percent, 100))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

