import type { CashflowData } from "@/lib/api-client";

export default function CashFlowTimeline({ data }: { data: CashflowData }) {
  return (
    <section className="glass-card panel-shell rounded-[28px] p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D8AB5]">Cash Flow Timeline</p>
          <h3 className="mt-1.5 text-[16px] font-bold text-white">Upcoming payment pressure</h3>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 px-3 py-2 text-right">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D8AB5]">Projected Outflow</p>
          <p className="mt-1 text-sm font-bold text-[#edf2ff]">Rs. {Number(data.monthly_outflow_projection || 0).toLocaleString()}</p>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {data.upcoming_payments.slice(0, 6).map((item) => (
          <div key={`${item.type}-${item.name}-${item.date}`} className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/5 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-[#edf2ff]">{item.name}</p>
              <p className="mt-1 text-xs text-[#8f9aba]">{item.type} · {item.date}</p>
            </div>
            <p className="text-sm font-bold text-[#b9b7ff]">Rs. {Number(item.amount || 0).toLocaleString()}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

