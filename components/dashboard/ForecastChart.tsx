"use client";

import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer, ReferenceDot } from "recharts";
import { apiClient } from "@/lib/api-client";
import { useFinance } from "@/context/FinanceContext";
import type { PredictionData } from "@/lib/api-client";

type ForecastPoint = {
  day: string;
  value: number;
};

type PredictionSummary = PredictionData["next_expense_prediction"];

const CHART_MARGIN = { top: 20, right: 0, left: 0, bottom: 0 };
const XAXIS_TICK = { fill: "#8793b8", fontSize: 12 };

const renderTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#8BE2E8] text-white px-3 py-2 rounded-lg font-bold shadow-[0_0_15px_rgba(139,92,246,0.5)]">
        Forecast
        <div className="text-sm border-t border-white/20 mt-1 pt-1">Rs. {Number(payload[0].value || 0).toLocaleString()} / day</div>
      </div>
    );
  }
  return null;
};

export default function ForecastChart() {
  const { transactions } = useFinance();
  const [points, setPoints] = useState<ForecastPoint[]>([]);
  const [peak, setPeak] = useState<{ day: string; amount: number } | null>(null);
  const [summary, setSummary] = useState<PredictionSummary | null>(null);
  const [status, setStatus] = useState<"syncing" | "completed" | "fallback">("syncing");

  const generateLocalFallback = () => {
    if (!transactions.length) {
      setPoints(Array.from({ length: 15 }, (_, i) => ({ day: `Day ${i + 1}`, value: 0 })));
      setSummary({ predicted_expense: 0, risk_level: "Low", budget_usage_percent: 0, feature_contributions: {} as any, explainability: {} as any, suggestions: [], disclaimer: "" });
      return;
    }

    const totalSpend = transactions.filter(t => t.amount < 0).reduce((acc, t) => acc + Math.abs(t.amount), 0);
    const avgSpend = totalSpend / Math.max(transactions.length / 5, 1); // rough daily average
    
    const fallbackPoints = Array.from({ length: 15 }, (_, i) => ({
      day: `Day ${i + 1}`,
      value: Math.max(0, avgSpend * (0.85 + Math.random() * 0.3))
    }));

    setPoints(fallbackPoints);
    setPeak({ day: "Day 7", amount: avgSpend * 1.4 });
    setSummary({
      predicted_expense: avgSpend * 1.1,
      risk_level: avgSpend > 5000 ? "Moderate" : "Low",
      budget_usage_percent: Math.min(100, (totalSpend / 50000) * 100),
      feature_contributions: {} as any,
      explainability: { top_positive_driver: "Recent spending patterns", top_negative_driver: "Historical consistency" },
      suggestions: ["Maintain current spending discipline"],
      disclaimer: "Estimated based on local trends"
    });
    setStatus("fallback");
  };

  useEffect(() => {
    let active = true;
    
    // Safety timeout to prevent infinite syncing
    const fallbackTimeout = setTimeout(() => {
      if (active && status === "syncing") {
        console.warn("[Prophet Engine] Sync timeout reached. Switching to local fallback.");
        generateLocalFallback();
      }
    }, 4000);

    async function load() {
      try {
        setStatus("syncing");
        const res = await apiClient.getPrediction({ timelineDays: 15 });
        
        if (!active) return;
        clearTimeout(fallbackTimeout);

        if (res.success && res.data?.forecast?.series) {
          const series = res.data.forecast.series.map((value: number, index: number) => ({
            day: `Day ${index + 1}`,
            value,
          }));
          setPoints(series);
          setPeak(res.data.forecast.peakAlert);
          setSummary(res.data.next_expense_prediction);
          setStatus("completed");
        } else {
          console.warn("[Prophet Engine] API failure or malformed data. Using fallback.");
          generateLocalFallback();
        }
      } catch (err) {
        if (!active) return;
        clearTimeout(fallbackTimeout);
        generateLocalFallback();
      }
    }

    load();

    return () => {
      active = false;
      clearTimeout(fallbackTimeout);
    };
  }, [transactions]);

  useEffect(() => {
    function handleRealtimeUpdate(event: Event) {
      const detail = (event as CustomEvent).detail;
      const prediction = detail?.data?.prediction;
      if (!prediction) return;

      const incomingSeries = Array.isArray(prediction.forecast?.series) ? prediction.forecast.series : [];
      if (incomingSeries.length > 0) {
        const series = incomingSeries.map((value: number, index: number) => ({
          day: `Day ${index + 1}`,
          value,
        }));
        setPoints(series);
        setPeak(prediction.forecast?.peakAlert || null);
      }

      if (prediction.next_expense_prediction) {
        setSummary(prediction.next_expense_prediction || null);
      }
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
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D839E]">Prophet Engine Forecasting</p>
          <h3 className="mt-1.5 text-[15px] font-bold text-white">
            {status === "syncing" ? "Analyzing recent spending patterns..." : "15-day projected spending trend"}
          </h3>
        </div>
        <div className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-semibold shadow-[0_0_10px_rgba(139,92,246,0.2)] ${
          status === "syncing" ? "border-[#8BE2E8]/30 bg-[#8BE2E8]/10 text-[#8BE2E8]" : 
          status === "fallback" ? "border-amber-400/30 bg-amber-400/10 text-amber-400" :
          "border-emerald-400/30 bg-emerald-400/10 text-emerald-400"
        }`}>
          <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${
            status === "syncing" ? "bg-[#8BE2E8]" : 
            status === "fallback" ? "bg-amber-400" :
            "bg-emerald-400"
          }`} />
          {status === "syncing" ? "ENGINE ANALYZING..." : status === "fallback" ? "USING LOCAL TRENDS" : "FORECAST UPDATED"}
        </div>
      </div>

      <div className="mb-5 grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-white/5 bg-[#11182b] p-3.5">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D839E]">Next Expense Prediction</p>
          <p className="mt-1.5 text-[1.45rem] font-bold text-white">
            {summary ? `Rs. ${Math.round(summary.predicted_expense).toLocaleString()}` : "Calculating..."}
          </p>
        </div>
        <div className="rounded-2xl border border-white/5 bg-[#11182b] p-3.5">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D839E]">Risk Level</p>
          <p className={`mt-1.5 text-[1.45rem] font-bold ${summary?.risk_level === "High" ? "text-rose-400" : "text-emerald-400"}`}>
            {summary?.risk_level || "Analyzing..."}
          </p>
          <p className="mt-1 text-[11px] text-[#94A1C8]">
            Budget usage: {summary ? `${Math.round(summary.budget_usage_percent || 0)}%` : "Calculating..."}
          </p>
        </div>
        <div className="rounded-2xl border border-white/5 bg-[#11182b] p-3.5">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D839E]">Peak Forecast</p>
          <p className="mt-1.5 text-[1.45rem] font-bold text-white">
            {peak ? `Rs. ${Math.round(peak.amount).toLocaleString()}` : "Calculating..."}
          </p>
          <p className="mt-1 text-[11px] text-[#94A1C8]">{peak?.day || "Calculating..."}</p>
        </div>
      </div>

      <div className="mt-2 w-full min-w-0">
        <ResponsiveContainer width="100%" height={220} minWidth={0}>
          <AreaChart data={points} margin={CHART_MARGIN}>
            <defs>
              <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8BE2E8" stopOpacity={0.5} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <XAxis dataKey="day" axisLine={false} tickLine={false} tick={XAXIS_TICK} dy={10} />
            <Tooltip content={renderTooltip} />
            <Area type="monotone" dataKey="value" stroke="#8BE2E8" strokeWidth={4} fillOpacity={1} fill="url(#colorForecast)" animationDuration={1500} />
            {peakPoint ? <ReferenceDot x={peakPoint.day} y={peakPoint.value} r={6} fill="#fff" stroke="#8BE2E8" strokeWidth={3} /> : null}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
