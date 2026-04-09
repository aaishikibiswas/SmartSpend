"use client";

import { useEffect, useMemo, useState } from "react";
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer } from "recharts";
import { MoreHorizontal } from "lucide-react";
import { type CategoryBreakdownItem } from "@/lib/api-client";

const defaultData = [
  { name: "Food", amount: 0 },
  { name: "Transport", amount: 0 },
  { name: "Shopping", amount: 0 },
];

export default function CategoryChart({ dataOverride }: { dataOverride?: CategoryBreakdownItem[] }) {
  const [liveData, setLiveData] = useState<CategoryBreakdownItem[] | null>(null);
  const baseData = useMemo(() => (dataOverride && dataOverride.length > 0 ? dataOverride : defaultData).slice(0, 6), [dataOverride]);
  const data = liveData ?? baseData;

  useEffect(() => {
    function handleRealtimeUpdate(event: Event) {
      const detail = (event as CustomEvent).detail;
      const nextBreakdown = detail?.data?.categoryBreakdown;
      if (Array.isArray(nextBreakdown)) {
        setLiveData((nextBreakdown.length > 0 ? nextBreakdown : defaultData).slice(0, 6));
      }
    }

    window.addEventListener("smartspend:ws-update", handleRealtimeUpdate);
    return () => window.removeEventListener("smartspend:ws-update", handleRealtimeUpdate);
  }, []);

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

      <div className="h-[185px] w-full min-w-0">
        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
          <BarChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }} barGap={8}>
            <defs>
              <linearGradient id="categoryFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8B5CF6" />
                <stop offset="100%" stopColor="#4F7CFF" />
              </linearGradient>
            </defs>
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: "#8793b8", fontSize: 12 }} dy={10} />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.05)" }}
              contentStyle={{ backgroundColor: "#1A2035", border: "1px solid #2A324A", borderRadius: "8px" }}
              formatter={(value) => [`Rs. ${Number(value).toLocaleString()}`, "Spent"]}
            />
            <Bar dataKey="amount" fill="url(#categoryFill)" radius={[8, 8, 0, 0]} maxBarSize={42} />
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
