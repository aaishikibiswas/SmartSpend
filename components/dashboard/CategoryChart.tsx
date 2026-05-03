"use client";

import { useMemo } from "react";
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer } from "recharts";
import { MoreHorizontal } from "lucide-react";
import { type CategoryBreakdownItem } from "@/lib/api-client";
import { useFinance } from "@/context/FinanceContext";

const defaultData = [
  { name: "Food", amount: 0 },
  { name: "Transport", amount: 0 },
  { name: "Shopping", amount: 0 },
];

const CHART_MARGIN = { top: 0, right: 0, left: 0, bottom: 0 };
const XAXIS_TICK = { fill: "#8793b8", fontSize: 12 };
const TOOLTIP_CURSOR = { fill: "rgba(255,255,255,0.05)" };
const TOOLTIP_CONTENT_STYLE = { backgroundColor: "#1A2035", border: "1px solid #2A324A", borderRadius: "8px" };
const BAR_RADIUS: [number, number, number, number] = [8, 8, 0, 0];
const tooltipFormatter = (value: any) => [`Rs. ${Number(value).toLocaleString()}`, "Spent"];

export default function CategoryChart({ dataOverride }: { dataOverride?: CategoryBreakdownItem[] }) {
  const { transactions } = useFinance();
  const data = useMemo(() => {
    if (transactions.length > 0) {
      const totals = new Map<string, number>();
      for (const tx of transactions) {
        if (tx.type === "expense") {
          totals.set(tx.category, (totals.get(tx.category) || 0) + Math.abs(tx.amount));
        }
      }
      const computed = Array.from(totals.entries())
        .map(([name, amount]) => ({ name, amount }))
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 6);
      if (computed.length > 0) return computed;
    }
    return (dataOverride && dataOverride.length > 0 ? dataOverride : defaultData).slice(0, 6);
  }, [transactions, dataOverride]);

  return (
    <div className="glass-card panel-shell flex flex-col justify-between p-5">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D8AB5]">Spending Overview</p>
          <h3 className="mt-1.5 text-[15px] font-bold text-white">Category Comparison</h3>
        </div>
        <button className="text-gray-400 transition-colors hover:text-white">
          <MoreHorizontal className="h-4.5 w-4.5" />
        </button>
      </div>

      <div className="w-full min-w-0">
        <ResponsiveContainer width="100%" height={185} minWidth={0}>
          <BarChart data={data} margin={CHART_MARGIN} barGap={8}>
            <defs>
              <linearGradient id="categoryFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8B5CF6" />
                <stop offset="100%" stopColor="#4F7CFF" />
              </linearGradient>
            </defs>
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={XAXIS_TICK} dy={10} />
            <Tooltip
              cursor={TOOLTIP_CURSOR}
              contentStyle={TOOLTIP_CONTENT_STYLE}
              formatter={tooltipFormatter}
            />
            <Bar dataKey="amount" fill="url(#categoryFill)" radius={BAR_RADIUS} maxBarSize={42} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex justify-center gap-4 text-[11px] font-medium text-gray-400">
        <div className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded-full bg-[#6D7CFF]" />
          CATEGORY SPEND
        </div>
      </div>
    </div>
  );
}
