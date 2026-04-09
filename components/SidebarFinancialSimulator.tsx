"use client";

import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { ChevronDown, LoaderCircle, SlidersHorizontal, Sparkles, TrendingUp } from "lucide-react";
import { apiClient, type DashboardMetrics, type SimulationResult } from "@/lib/api-client";

function formatCurrency(value: number) {
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

function riskTone(level: string) {
  if (level === "High") return "bg-rose-500/15 text-rose-200 border-rose-400/30";
  if (level === "Medium") return "bg-amber-500/15 text-amber-100 border-amber-400/30";
  return "bg-emerald-500/15 text-emerald-100 border-emerald-400/30";
}

export default function SidebarFinancialSimulator() {
  const [open, setOpen] = useState(true);
  const [incomeAdjustment, setIncomeAdjustment] = useState(0);
  const [expenseAdjustment, setExpenseAdjustment] = useState(0);
  const [months, setMonths] = useState(6);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadMetrics() {
      try {
        const response = await apiClient.getDashboardData();
        setMetrics(response.data.metrics);
      } catch (loadError) {
        console.error(loadError);
      } finally {
        setIsBootstrapping(false);
      }
    }

    void loadMetrics();
  }, []);

  const comparison = useMemo(() => {
    if (!metrics || !result) return null;
    const current = metrics.netSavings;
    const projected = result.monthly_savings;
    const maxValue = Math.max(Math.abs(current), Math.abs(projected), 1);
    return {
      maxValue,
      items: [
        { label: "Current", value: current, tone: "bg-[#5db8ff]" },
        { label: "Projected", value: projected, tone: projected >= 0 ? "bg-[#8B7DFF]" : "bg-[#ff7a98]" },
      ],
    };
  }, [metrics, result]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const response = await apiClient.runSimulation({
        income_adjustment: incomeAdjustment,
        expense_adjustment: expenseAdjustment,
        months,
      });
      setResult(response.data);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Simulation failed.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="mt-4 rounded-2xl border border-[#6d758c]/20 bg-[rgba(18,28,49,0.75)] p-4 backdrop-blur-md">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex w-full items-center justify-between gap-3 text-left"
      >
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-[#8B7DFF]/15 p-2 text-[#b8b4ff]">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#91a0c5]">Financial Simulator</p>
            <p className="mt-1 text-sm font-semibold text-[#edf2ff]">Plan future savings</p>
          </div>
        </div>
        <ChevronDown className={`h-4 w-4 text-[#91a0c5] transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {open ? (
        <div className="mt-4 space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block">
              <div className="mb-2 flex items-center justify-between text-[11px]">
                <span className="font-semibold text-[#dbe4ff]">Income Adjustment</span>
                <span className="text-[#91a0c5]">{formatCurrency(incomeAdjustment)}</span>
              </div>
              <input
                type="range"
                min={-20000}
                max={50000}
                step={500}
                value={incomeAdjustment}
                onChange={(event) => setIncomeAdjustment(Number(event.target.value))}
                className="w-full accent-[#8B7DFF]"
              />
              <p className="mt-1 text-[10px] text-[#7f8bac]">Increase or decrease your income</p>
            </label>

            <label className="block">
              <div className="mb-2 flex items-center justify-between text-[11px]">
                <span className="font-semibold text-[#dbe4ff]">Expense Adjustment</span>
                <span className="text-[#91a0c5]">{formatCurrency(expenseAdjustment)}</span>
              </div>
              <input
                type="range"
                min={-20000}
                max={50000}
                step={500}
                value={expenseAdjustment}
                onChange={(event) => setExpenseAdjustment(Number(event.target.value))}
                className="w-full accent-[#8B7DFF]"
              />
              <p className="mt-1 text-[10px] text-[#7f8bac]">Simulate spending changes</p>
            </label>

            <label className="block">
              <div className="mb-2 flex items-center justify-between text-[11px]">
                <span className="font-semibold text-[#dbe4ff]">Time Period</span>
                <span className="text-[#91a0c5]">{months} months</span>
              </div>
              <input
                type="range"
                min={1}
                max={24}
                step={1}
                value={months}
                onChange={(event) => setMonths(Number(event.target.value))}
                className="w-full accent-[#8B7DFF]"
              />
            </label>

            <button
              type="submit"
              disabled={isLoading || isBootstrapping}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#7B6CF6] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#8B7DFF] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <SlidersHorizontal className="h-4 w-4" />}
              Run Simulation
            </button>
          </form>

          {error ? <p className="text-xs text-rose-300">{error}</p> : null}

          {result ? (
            <div className="space-y-3">
              <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                <p className="text-[10px] uppercase tracking-[0.18em] text-[#91a0c5]">Projected Savings</p>
                <p className={`mt-2 text-2xl font-bold ${result.projected_savings >= 0 ? "text-[#7cf0bd]" : "text-[#ff9db2]"}`}>
                  {formatCurrency(result.projected_savings)}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-white/8 bg-white/5 p-3">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-[#91a0c5]">Monthly Savings</p>
                  <p className="mt-2 text-sm font-semibold text-[#edf2ff]">{formatCurrency(result.monthly_savings)}</p>
                </div>
                <div className={`rounded-2xl border p-3 ${riskTone(result.risk_level)}`}>
                  <p className="text-[10px] uppercase tracking-[0.16em]">Risk</p>
                  <p className="mt-2 text-sm font-semibold">{result.risk_level}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-white/8 bg-white/5 p-3">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-[#91a0c5]">New Income</p>
                  <p className="mt-2 text-sm font-semibold text-[#edf2ff]">{formatCurrency(result.new_income)}</p>
                </div>
                <div className="rounded-2xl border border-white/8 bg-white/5 p-3">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-[#91a0c5]">New Expense</p>
                  <p className="mt-2 text-sm font-semibold text-[#edf2ff]">{formatCurrency(result.new_expense)}</p>
                </div>
              </div>

              {comparison ? (
                <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-[#b8b4ff]" />
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#91a0c5]">Current vs Projected</p>
                  </div>
                  <div className="space-y-3">
                    {comparison.items.map((item) => (
                      <div key={item.label}>
                        <div className="mb-1.5 flex items-center justify-between text-[11px]">
                          <span className="font-semibold text-[#edf2ff]">{item.label}</span>
                          <span className="text-[#a8b1ce]">{formatCurrency(item.value)}</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-white/8">
                          <div className={`h-full rounded-full ${item.tone}`} style={{ width: `${Math.max(8, (Math.abs(item.value) / comparison.maxValue) * 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
