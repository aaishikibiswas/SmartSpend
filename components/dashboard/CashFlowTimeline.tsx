import { memo } from "react";
import type { CashflowData } from "@/lib/api-client";

const CashFlowTimeline = memo(function CashFlowTimeline({ data }: { data: CashflowData }) {
  const sortedPayments = [...(data.upcoming_payments || [])].map(p => {
    const dueDate = new Date(p.date);
    const today = new Date();
    const diffDays = Math.ceil((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    
    let priority = 0; 
    let status = "low";
    let level = "L3";
    let levelName = "Lifestyle";
    let levelColor = "text-sky-400";
    let levelBg = "bg-sky-400/10";
    
    const type = p.type.toLowerCase();
    if (type === "emi") {
      priority = diffDays <= 3 ? 1 : 2;
      status = diffDays <= 3 ? "critical" : "high";
      level = "L2";
      levelName = "Debt Commitment";
      levelColor = "text-[#A897FF]";
      levelBg = "bg-[#A897FF]/10";
    } else if (type === "bill") {
      priority = diffDays <= 2 ? 1 : 3;
      status = diffDays <= 2 ? "critical" : "medium";
      level = "L1";
      levelName = "Survival / Fixed";
      levelColor = "text-emerald-400";
      levelBg = "bg-emerald-400/10";
    } else {
      priority = 4;
      status = "low";
      level = "L3";
      levelName = "Discretionary";
      levelColor = "text-[#8BE2E8]";
      levelBg = "bg-[#8BE2E8]/10";
    }

    return { ...p, priority, status, diffDays, level, levelName, levelColor, levelBg };
  }).sort((a, b) => a.priority - b.priority || a.diffDays - b.diffDays);

  const topPriority = sortedPayments[0];

  return (
    <section className="glass-card panel-shell rounded-[28px] p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D839E]">Cash Flow Timeline</p>
          <h3 className="mt-1.5 text-[16px] font-bold text-white">Financial Priority Queue</h3>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 px-3 py-2 text-right">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D839E]">Projected Outflow</p>
          <p className="mt-1 text-sm font-bold text-[#edf2ff]">Rs. {Number(data.monthly_outflow_projection || 0).toLocaleString()}</p>
        </div>
      </div>

      {topPriority && topPriority.priority <= 2 && (
        <div className="mt-4 flex items-center gap-3 rounded-2xl bg-[#ff7e7e]/10 border border-[#ff7e7e]/20 p-3.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#ff7e7e]/20 shadow-[0_0_15px_rgba(255,126,126,0.2)]">
            <span className="text-[#ff7e7e] text-xs font-bold">!</span>
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[#ff7e7e]">Critical Action</p>
            <p className="text-xs text-[#edf2ff] leading-snug">
              Clear <b>{topPriority.name}</b> first to protect your {topPriority.levelName.toLowerCase()} score.
            </p>
          </div>
        </div>
      )}

      <div className="mt-5 space-y-3">
        {sortedPayments.slice(0, 6).map((item, index) => (
          <div key={`${item.type}-${item.name}-${item.date}-${index}`} className="group flex items-center justify-between rounded-2xl border border-white/8 bg-white/5 px-4 py-3 relative overflow-hidden transition-all hover:bg-white/[0.08] hover:border-white/20">
            {item.status === "critical" && (
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#ff7e7e]" />
            )}
            <div>
              <div className="flex items-center gap-2">
                <span className={`text-[8px] font-black px-1.5 py-0.5 rounded ${item.levelBg} ${item.levelColor} border border-white/5`}>
                  {item.level}
                </span>
                <p className="text-sm font-semibold text-[#edf2ff]">{item.name}</p>
              </div>
              <p className="mt-1 text-[10px] font-medium text-[#7D839E]">
                {item.levelName} · <span className="text-[#8f9aba]">{item.date}</span>
              </p>
            </div>
            <div className="text-right">
              <p className={`text-sm font-bold ${item.levelColor}`}>Rs. {Number(item.amount || 0).toLocaleString()}</p>
              <p className="text-[9px] font-bold uppercase tracking-tighter text-[#7D839E] group-hover:text-[#edf2ff] transition-colors">
                {item.diffDays <= 0 ? "Due Today" : `In ${item.diffDays} days`}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
});

export default CashFlowTimeline;
