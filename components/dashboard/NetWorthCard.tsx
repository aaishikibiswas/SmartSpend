import type { NetworthData } from "@/lib/api-client";

function fmt(value: number) {
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

export default function NetWorthCard({ data }: { data: NetworthData }) {
  return (
    <section className="glass-card panel-shell rounded-[28px] p-5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D8AB5]">Net Worth</p>
      <h3 className="mt-2 text-[16px] font-bold text-white">{fmt(data.net_worth)}</h3>
      <div className="mt-5 grid gap-3">
        <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D8AB5]">Assets</p>
          <p className="mt-2 text-sm font-semibold text-[#edf2ff]">{fmt(data.assets)}</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D8AB5]">Liabilities</p>
          <p className="mt-2 text-sm font-semibold text-[#ffd3db]">{fmt(data.liabilities)}</p>
        </div>
      </div>
    </section>
  );
}

