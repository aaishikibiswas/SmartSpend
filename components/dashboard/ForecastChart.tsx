"use client";

import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer, ReferenceDot } from "recharts";
import { apiClient } from "@/lib/api-client";

type ForecastPoint = {
  day: string;
  value: number;
};

type PredictionSummary = {
  predicted_expense: number;
  risk_level: string;
  budget_usage_percent: number;
};

export default function ForecastChart() {
  const [points, setPoints] = useState<ForecastPoint[]>([]);
  const [peak, setPeak] = useState<{ day: string; amount: number } | null>(null);
  const [summary, setSummary] = useState<PredictionSummary | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await apiClient.getPrediction({ timelineDays: 15 });
        const series = res.data.forecast.series.map((value, index) => ({
          day: `Day ${index + 1}`,
          value,
        }));
        setPoints(series);
        setPeak(res.data.forecast.peakAlert);
        setSummary(res.data.next_expense_prediction);
      } catch (error) {
        console.error(error);
        setPoints([]);
        setPeak(null);
        setSummary(null);
      }
    }

    load();
  }, []);

  useEffect(() => {
    function handleRealtimeUpdate(event: Event) {
      const detail = (event as CustomEvent).detail;
      const prediction = detail?.data?.prediction;
      if (!prediction) return;

      const series = (prediction.forecast?.series || []).map((value: number, index: number) => ({
        day: `Day ${index + 1}`,
        value,
      }));

      setPoints(series);
      setPeak(prediction.forecast?.peakAlert || null);
      setSummary(prediction.next_expense_prediction || null);
    }

    window.addEventListener("smartspend:ws-update", handleRealtimeUpdate);
    return () => window.removeEventListener("smartspend:ws-update", handleRealtimeUpdate);
  }, []);

  const peakPoint = peak
    ? {
        day: peak.day.replace(" (Peak)", ""),
        value: peak.amount,
      }
    : null;

  return (
    <div className="glass-card panel-shell relative p-5">
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D8AB5]">Prophet Engine Forecasting</p>
          <h3 className="mt-1.5 text-[15px] font-bold text-white">15-day projected spending trend</h3>
        </div>
        <div className="flex items-center gap-1.5 rounded-full border border-[#8B5CF6]/30 bg-[#8B5CF6]/10 px-2.5 py-1 text-[10px] font-semibold text-[#8B5CF6] shadow-[0_0_10px_rgba(139,92,246,0.2)]">
          <div className="w-1.5 h-1.5 bg-[#8B5CF6] rounded-full animate-pulse" />
          PROPHET ENGINE ACTIVE
        </div>
      </div>

      <div className="mb-5 grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-white/5 bg-[#11182b] p-3.5">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D8AB5]">Next Expense Prediction</p>
          <p className="mt-1.5 text-[1.45rem] font-bold text-white">
            {summary ? `Rs. ${summary.predicted_expense.toLocaleString()}` : "Loading..."}
          </p>
        </div>
        <div className="rounded-2xl border border-white/5 bg-[#11182b] p-3.5">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D8AB5]">Risk Level</p>
          <p className={`mt-1.5 text-[1.45rem] font-bold ${summary?.risk_level === "High" ? "text-rose-400" : "text-emerald-400"}`}>
            {summary?.risk_level || "Loading..."}
          </p>
          <p className="mt-1 text-[11px] text-[#94A1C8]">
            Budget usage: {summary ? `${Math.round(summary.budget_usage_percent || 0)}%` : "Calculating..."}
          </p>
        </div>
        <div className="rounded-2xl border border-white/5 bg-[#11182b] p-3.5">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D8AB5]">Peak Forecast</p>
          <p className="mt-1.5 text-[1.45rem] font-bold text-white">{peak ? `Rs. ${peak.amount.toLocaleString()}` : "Loading..."}</p>
          <p className="mt-1 text-[11px] text-[#94A1C8]">{peak?.day || "Calculating..."}</p>
        </div>
      </div>

      <div className="mt-2 h-[220px] w-full min-w-0">
        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
          <AreaChart data={points} margin={{ top: 20, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.5} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: "#8793b8", fontSize: 12 }} dy={10} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-[#8B5CF6] text-white px-3 py-2 rounded-lg font-bold shadow-[0_0_15px_rgba(139,92,246,0.5)]">
                      Forecast
                      <div className="text-sm border-t border-white/20 mt-1 pt-1">Rs. {Number(payload[0].value || 0).toLocaleString()} / day</div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area type="monotone" dataKey="value" stroke="#8B5CF6" strokeWidth={4} fillOpacity={1} fill="url(#colorForecast)" animationDuration={1500} />
            {peakPoint ? <ReferenceDot x={peakPoint.day} y={peakPoint.value} r={6} fill="#fff" stroke="#8B5CF6" strokeWidth={3} /> : null}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
