"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { 
  AlertTriangle, 
  Car, 
  CheckCircle2, 
  ChevronDown, 
  ChevronRight, 
  ChevronUp, 
  Home, 
  Info, 
  Landmark, 
  LoaderCircle, 
  Play, 
  Plus, 
  Scale, 
  ShoppingBag, 
  TrendingUp, 
  UtensilsCrossed, 
  WalletCards, 
  X 
} from "lucide-react";
import {
  apiClient,
  type BudgetCategoryItem,
  type BudgetSnapshot,
  type CategoryBreakdownItem,
  type DecisionResult,
} from "@/lib/api-client";

type BudgetingPanelProps = {
  categories: CategoryBreakdownItem[];
  budgetSnapshot: BudgetSnapshot;
};

function normalizeCategory(name: string) {
  const value = name.trim().toLowerCase();
  if (value === "food") return "Food";
  if (value === "food & dining") return "Food";
  if (value === "health") return "Healthcare";
  return name;
}

const FALLBACK_CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Other"];

function getDecisionTone(status: string) {
  if (status === "success") return "border-[#8BE2E8]/30 bg-[#8BE2E8]/10 text-[#8BE2E8]";
  if (status === "warning") return "border-amber-400/30 bg-amber-500/10 text-amber-100";
  return "border-[#ff6e84]/30 bg-[#ff6e84]/10 text-[#ff6e84]";
}

export default function BudgetingPanel({ categories, budgetSnapshot }: BudgetingPanelProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const categoryOptions = useMemo(() => {
    const names = new Set<string>();
    for (const item of categories) names.add(normalizeCategory(item.name));
    for (const item of budgetSnapshot.categories) names.add(normalizeCategory(item.name));
    const normalized = Array.from(names).filter(Boolean);
    return normalized.length > 0 ? normalized : FALLBACK_CATEGORIES;
  }, [budgetSnapshot.categories, categories]);

  const [view, setView] = useState<"monthly" | "weekly">("monthly");
  const [globalMonthly, setGlobalMonthly] = useState(budgetSnapshot.global.monthly_budget);
  const [autoDistribute, setAutoDistribute] = useState(budgetSnapshot.global.auto_distribute);
  const [selectedCategory, setSelectedCategory] = useState(categoryOptions[0] ?? "Food");
  const [selectedFrequency, setSelectedFrequency] = useState<"Monthly" | "Weekly">("Monthly");
  const [amountInput, setAmountInput] = useState("");
  const [entries, setEntries] = useState<BudgetCategoryItem[]>(budgetSnapshot.categories);
  const [feedback, setFeedback] = useState<string[]>(budgetSnapshot.feedback);
  const [message, setMessage] = useState("");
  const [decisionItem, setDecisionItem] = useState("");
  const [decisionPrice, setDecisionPrice] = useState("");
  const [decisionResult, setDecisionResult] = useState<DecisionResult | null>(null);

  const globalUsage = budgetSnapshot.global.usage_percent;

  useEffect(() => {
    setGlobalMonthly(budgetSnapshot.global.monthly_budget);
    setAutoDistribute(budgetSnapshot.global.auto_distribute);
    setEntries(budgetSnapshot.categories);
    setFeedback(budgetSnapshot.feedback);
  }, [budgetSnapshot]);

  useEffect(() => {
    if (!categoryOptions.includes(selectedCategory)) {
      setSelectedCategory(categoryOptions[0] ?? "Food");
    }
  }, [categoryOptions, selectedCategory]);

  async function refreshUI() {
    window.dispatchEvent(new Event("smartspend:budget-updated"));
    startTransition(() => router.refresh());
  }

  async function handleSaveGlobalBudget() {
    setMessage("");
    try {
      const response = await apiClient.updateGlobalBudget({
        monthly_budget: globalMonthly,
        auto_distribute: autoDistribute,
      });
      setFeedback(response.data.feedback);
      setEntries(response.data.categories);
      setMessage("Global budget updated.");
      await refreshUI();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to update global budget.");
    }
  }

  async function handleAddEntry() {
    const parsed = Number(amountInput);
    if (!selectedCategory || Number.isNaN(parsed) || parsed <= 0) {
      setMessage("Enter a valid category budget amount.");
      return;
    }

    try {
      const response = await apiClient.upsertCategoryBudget({
        name: selectedCategory,
        amount: parsed,
        frequency: selectedFrequency,
      });
      setEntries(response.data.categories);
      setFeedback(response.data.feedback);
      setAmountInput("");
      setMessage(`${selectedCategory} budget saved.`);
      await refreshUI();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to save category budget.");
    }
  }

  async function handleRemoveEntry(name: string) {
    try {
      const response = await apiClient.deleteCategoryBudget(name);
      setEntries(response.data.categories);
      setFeedback(response.data.feedback);
      setMessage(`${name} budget removed.`);
      await refreshUI();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to remove category budget.");
    }
  }

  async function handleDecisionCheck() {
    const price = Number(decisionPrice);
    if (!decisionItem.trim() || Number.isNaN(price) || price <= 0) {
      setMessage("Enter an item and price to run the decision engine.");
      return;
    }

    try {
      const response = await apiClient.evaluateDecision({
        item_name: decisionItem,
        price,
      });
      setDecisionResult(response.data);
      setMessage("Decision engine evaluated your purchase.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Decision check failed.");
    }
  }

  const progressTone = globalUsage >= 100 ? "bg-[#ff6e84]" : globalUsage >= 80 ? "bg-amber-400" : "bg-[#8BE2E8]";

  return (
    <section className="relative overflow-hidden rounded-[2.5rem] bg-[#0A0F1E] border border-white/[0.05] p-8 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
      {/* Background atmospheric glow */}
      <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-[#A897FF]/[0.05] blur-[100px]" />
      
      {/* Header Section */}
      <div className="relative mb-8 flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
        <div>
          <h2 className="text-[26px] font-bold tracking-tight text-white">Financial Settings & Budgeting</h2>
          <p className="mt-1 text-[13px] font-medium text-slate-400">Configure your global limits and category-wise constraints</p>
        </div>

        <div className="flex items-center gap-1 rounded-2xl border border-white/[0.1] bg-[#0D1225] p-1 shadow-inner">
          <button
            type="button"
            onClick={() => setView("monthly")}
            className={`rounded-xl px-6 py-1.5 text-[12px] font-bold transition-all ${
              view === "monthly" ? "bg-[#5D57E8] text-white shadow-lg" : "text-slate-400 hover:text-white"
            }`}
          >
            Monthly
          </button>
          <button
            type="button"
            onClick={() => setView("weekly")}
            className={`rounded-xl px-6 py-1.5 text-[12px] font-bold transition-all ${
              view === "weekly" ? "bg-[#5D57E8] text-white shadow-lg" : "text-slate-400 hover:text-white"
            }`}
          >
            Weekly
          </button>
        </div>
      </div>

      <div className="relative grid grid-cols-1 gap-6 xl:grid-cols-[45fr_55fr]">
        {/* LEFT COLUMN: 3 STACKED CARDS */}
        <div className="flex flex-col gap-6">
          {/* 1. Global Monthly Budget Card */}
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 shadow-xl">
            <div className="mb-4 flex items-center gap-3">
              <Landmark className="h-4 w-4 text-[#A897FF]" />
              <h4 className="text-[14px] font-bold text-white">Global Monthly Budget</h4>
            </div>
            <div className="relative mb-5">
              <div className="h-14 w-full flex items-center rounded-xl border border-white/[0.1] bg-[#060A16] px-4 group focus-within:border-[#A897FF]/50 transition-all">
                <span className="text-xl font-bold text-[#A897FF] mr-3">₹</span>
                <input
                  type="number"
                  value={globalMonthly}
                  onChange={(event) => setGlobalMonthly(Number(event.target.value) || 0)}
                  className="w-full bg-transparent text-xl font-bold text-white outline-none"
                />
                <div className="flex flex-col border-l border-white/10 pl-2 ml-2">
                  <ChevronUp className="h-3 w-3 text-slate-500 cursor-pointer hover:text-white" onClick={() => setGlobalMonthly(prev => prev + 1000)} />
                  <ChevronDown className="h-3 w-3 text-slate-500 cursor-pointer hover:text-white mt-1" onClick={() => setGlobalMonthly(prev => Math.max(0, prev - 1000))} />
                </div>
              </div>
            </div>
            <label className="mb-6 flex cursor-pointer items-center gap-3 text-[11px] font-medium text-slate-400 hover:text-slate-200 transition-colors">
              <input checked={autoDistribute} onChange={(event) => setAutoDistribute(event.target.checked)} type="checkbox" className="h-4 w-4 rounded border-white/20 bg-[#0D1225] accent-[#5D57E8]" />
              Auto-distribute across active categories
              <Info className="h-3 w-3 text-slate-500 ml-0.5" />
            </label>
            <button
              type="button"
              onClick={() => void handleSaveGlobalBudget()}
              disabled={isPending}
              className="flex w-full items-center justify-center gap-3 rounded-xl bg-[#5D57E8] px-4 py-3.5 text-[13px] font-bold text-white shadow-[0_0_20px_rgba(93,87,232,0.3)] transition-all hover:bg-[#6c67ef] active:scale-[0.98] disabled:opacity-60"
            >
              {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <WalletCards className="h-4 w-4" />}
              Save Budget Logic
            </button>
          </div>

          {/* 2. Budget Progress Card */}
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 shadow-xl">
            <div className="mb-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <TrendingUp className="h-4 w-4 text-[#A897FF]" />
                <h4 className="text-[14px] font-bold text-white">Budget Progress</h4>
              </div>
              <span className="rounded-full bg-[#ff6e84]/20 px-3 py-1 text-[11px] font-bold text-[#ff6e84]">{Math.round(globalUsage)}%</span>
            </div>
            <div className="mb-6 h-[14px] overflow-hidden rounded-full bg-[#060A16] shadow-inner">
              <div className={`h-full rounded-full transition-all duration-1000 ${progressTone} shadow-[0_0_12px_rgba(255,110,132,0.3)]`} style={{ width: `${Math.min(globalUsage, 100)}%` }} />
            </div>
            <div className="space-y-2">
              <p className="text-[12px] font-medium text-slate-400">You have ₹ {Math.round(budgetSnapshot.global.remaining_amount).toLocaleString()} left this month.</p>
              <div className="flex items-center gap-2">
                <p className="text-[12px] font-medium text-slate-400">Daily allowance: ₹{Math.round(budgetSnapshot.global.daily_allowance).toLocaleString()}</p>
                <Info className="h-3 w-3 text-slate-500" />
              </div>
            </div>
          </div>

          {/* 3. Decision Engine Card */}
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 shadow-xl">
            <div className="mb-1 flex items-center gap-3">
              <Scale className="h-4 w-4 text-[#A897FF]" />
              <h4 className="text-[14px] font-bold text-white">Decision Engine</h4>
            </div>
            <p className="mb-5 text-[12px] font-medium text-slate-400">Can I afford a new purchase?</p>
            <div className="space-y-3">
              <input
                value={decisionItem}
                onChange={(event) => setDecisionItem(event.target.value)}
                placeholder="Item name..."
                className="h-12 w-full rounded-xl border border-white/[0.1] bg-[#060A16] px-4 text-[12px] font-medium text-white outline-none focus:border-[#A897FF]/50"
              />
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[12px] font-bold text-slate-500">₹</span>
                  <input
                    type="number"
                    value={decisionPrice}
                    onChange={(event) => setDecisionPrice(event.target.value)}
                    placeholder="Price"
                    className="h-12 w-full rounded-xl border border-white/[0.1] bg-[#060A16] pl-8 pr-4 text-[12px] font-medium text-white outline-none focus:border-[#A897FF]/50"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => void handleDecisionCheck()}
                  className="flex h-12 items-center gap-2 rounded-xl bg-[#5D57E8] px-6 text-[12px] font-bold text-white transition-all hover:bg-[#6c67ef]"
                >
                  Check <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
            {decisionResult ? (
              <div className={`mt-5 rounded-xl border p-4 text-[11px] leading-relaxed ${getDecisionTone(decisionResult.status)}`}>
                <p className="font-bold uppercase mb-1 tracking-tight">{decisionResult.affordability === "Yes" ? "Clear for purchase" : decisionResult.affordability === "Maybe" ? "Caution" : "Not recommended"}</p>
                <p className="font-medium">{decisionResult.recommendation}</p>
              </div>
            ) : null}
          </div>
        </div>

        {/* RIGHT COLUMN: 2 PANELS */}
        <div className="flex flex-col gap-6">
          {/* 1. Category Budget Management Panel */}
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 lg:p-6 shadow-xl transition-all duration-500 hover:border-white/[0.12] hover:bg-white/[0.04] hover:shadow-[0_15px_30px_rgba(0,0,0,0.4)] group/panel relative overflow-hidden min-w-0">
            {/* Atmospheric light bar */}
            <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-right from-transparent via-[#A897FF]/20 to-transparent opacity-0 group-hover/panel:opacity-100 transition-opacity duration-700" />
            
            {/* HEADER ZONE: Compact Flex Layout */}
            <div className="mb-6 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3 min-w-0 max-w-[55%]">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#A897FF]/10 text-[#A897FF] shadow-inner mt-0.5">
                  <ShoppingBag className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <h4 className="text-[14px] font-bold text-white tracking-tight leading-[1.2]">
                    Category Budget Management
                  </h4>
                </div>
              </div>
              
              <div className="flex items-center gap-2 shrink-0 bg-white/[0.05] px-2.5 py-1 rounded-lg border border-white/[0.08] mt-0.5">
                <span className="h-1 w-1 rounded-full bg-[#8BE2E8] shadow-[0_0_6px_#8BE2E8] animate-pulse" />
                <span className="text-[8px] font-black text-slate-400 uppercase tracking-[0.2em]">Active Engine</span>
              </div>
            </div>

            {/* FORM ZONE: Rebalanced 4-Column Grid */}
            <div className="grid grid-cols-1 gap-y-6 gap-x-3 md:grid-cols-[1.3fr_1fr_1.2fr_auto] items-end min-w-0">
              <div className="flex flex-col gap-1.5 min-w-0">
                <label className="text-[9px] font-bold uppercase tracking-widest text-slate-500 pl-0.5">Category</label>
                <SelectField value={selectedCategory} onChange={setSelectedCategory} options={categoryOptions} />
              </div>
              
              <div className="flex flex-col gap-1.5 min-w-0">
                <label className="text-[9px] font-bold uppercase tracking-widest text-slate-500 pl-0.5">Frequency</label>
                <SelectField value={selectedFrequency} onChange={(value) => setSelectedFrequency(value as "Monthly" | "Weekly")} options={["Monthly", "Weekly"]} />
              </div>
              
              <div className="flex flex-col gap-1.5 min-w-0">
                <label className="text-[9px] font-bold uppercase tracking-widest text-slate-500 pl-0.5">Amount</label>
                <div className="relative group/input">
                  <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[10px] font-bold text-[#A897FF]">₹</span>
                  <input
                    type="number"
                    value={amountInput}
                    onChange={(event) => setAmountInput(event.target.value)}
                    placeholder="0"
                    className="h-[38px] w-full rounded-xl border border-white/[0.1] bg-[#060A16] pl-6 pr-2 text-[12px] font-bold text-white outline-none focus:border-[#A897FF]/50 focus:bg-[#090D1A] transition-all shadow-inner"
                  />
                </div>
              </div>

              <div className="flex items-center pb-0.5 justify-center">
                <button
                  type="button"
                  onClick={() => void handleAddEntry()}
                  disabled={isPending}
                  className="flex h-[32px] w-[32px] items-center justify-center rounded-lg bg-[#5D57E8] text-white shadow-[0_2px_8px_rgba(93,87,232,0.3)] transition-all hover:bg-[#6c67ef] hover:scale-[1.05] active:scale-95 disabled:opacity-50 disabled:hover:scale-100 shrink-0"
                >
                  <Plus className="h-4 w-4 stroke-[3]" />
                </button>
              </div>
            </div>
          </div>

          {/* 2. Active Category Budgets Panel */}
          <div className="flex-1 rounded-2xl border border-white/[0.08] bg-white/[0.03] flex flex-col shadow-xl min-h-0 min-w-0">
            <div className="px-6 py-5 flex items-center justify-between border-b border-white/[0.05]">
              <h4 className="text-[14px] font-bold text-white tracking-wide">Active Category Budgets</h4>
              <span className="text-[12px] font-bold text-[#A897FF] whitespace-nowrap ml-4">{entries.length} Categories</span>
            </div>
            
            <div className="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar p-5 pr-2 max-h-[520px]">
              <div className="pr-3 space-y-4">
                {entries.map((entry) => {
                  const isOver = entry.usage_percent >= 100;
                  const statusColor = isOver ? "text-[#ff6e84]" : "text-[#8BE2E8]";
                  const barColor = isOver ? "bg-[#ff6e84]" : "bg-[#8BE2E8]";
                  
                  return (
                    <div key={`${entry.name}-${entry.frequency}`} className="rounded-xl border border-white/[0.05] bg-[#0D1225]/50 p-6 group hover:bg-[#0D1225] transition-all min-w-0 relative">
                      {/* ROW 1: HEADER + LIMIT */}
                      <div className="flex items-start justify-between mb-5 gap-4">
                        <div className="flex items-center gap-4 min-w-0">
                          <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/[0.05] ${statusColor} shadow-lg`}>
                            {entry.name.toLowerCase().includes("food") ? <UtensilsCrossed className="h-5 w-5" /> : 
                             entry.name.toLowerCase().includes("car") || entry.name.toLowerCase().includes("transport") ? <Car className="h-5 w-5" /> :
                             entry.name.toLowerCase().includes("house") || entry.name.toLowerCase().includes("housing") ? <Home className="h-5 w-5" /> :
                             entry.name.toLowerCase().includes("entertain") ? <Play className="h-5 w-5" /> : <ShoppingBag className="h-5 w-5" />}
                          </div>
                          <div className="min-w-0">
                            <p className="text-[15px] font-bold text-white truncate leading-tight mb-1">{entry.name}</p>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.1em]">{entry.frequency}</p>
                          </div>
                        </div>

                        <div className="text-right shrink-0">
                          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1.5">Limit</p>
                          <p className="text-[14px] font-black text-white tabular-nums tracking-tight">₹{Math.round(entry.allocated_amount).toLocaleString()}</p>
                        </div>

                        <button type="button" onClick={() => void handleRemoveEntry(entry.name)} className="absolute right-3 top-3 text-slate-600 hover:text-white transition-all opacity-0 group-hover:opacity-100 p-1">
                          <X className="h-4 w-4" />
                        </button>
                      </div>

                      {/* ROW 2: SPENT + REMAINING */}
                      <div className="flex justify-between items-end mb-6 gap-6 pt-1 border-t border-white/[0.03]">
                        <div className="min-w-0">
                          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1.5">Spent</p>
                          <p className="text-[14px] font-black text-white tabular-nums tracking-tight">₹{Math.round(entry.spent_amount).toLocaleString()}</p>
                        </div>
                        <div className="text-right min-w-0">
                          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1.5">Remaining</p>
                          <p className={`text-[14px] font-black tabular-nums tracking-tight ${entry.remaining_amount < 0 ? "text-[#ff6e84]" : "text-[#8BE2E8]"}`}>
                            {entry.remaining_amount < 0 ? "-" : ""}₹{Math.abs(Math.round(entry.remaining_amount)).toLocaleString()}
                          </p>
                        </div>
                      </div>

                      {/* ROW 3: PROGRESS + STATUS */}
                      <div className="flex flex-col gap-3">
                        <div className="h-[6px] w-full rounded-full bg-white/[0.04] overflow-hidden shadow-inner">
                          <div 
                            className={`h-full rounded-full transition-all duration-1000 ${barColor} shadow-[0_0_10px_rgba(139,226,232,0.2)]`} 
                            style={{ width: `${Math.min(entry.usage_percent, 100)}%` }} 
                          />
                        </div>
                        <div className="flex justify-between items-center px-0.5">
                          <p className={`text-[11px] font-black uppercase tracking-wider ${statusColor}`}>
                            {isOver ? "Limit Breached" : "Healthy Status"}
                          </p>
                          <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest">
                            {Math.round(entry.usage_percent)}% <span className="text-[9px] opacity-60 font-bold ml-0.5">USED</span>
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER ALERTS (2 Horizontal Cards) */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-5">
        {feedback.slice(0, 2).map((line, idx) => {
          const isError = line.toLowerCase().includes("over") || line.toLowerCase().includes("breach");
          return (
            <div key={idx} className={`flex items-center gap-5 rounded-2xl border px-6 py-5 transition-all ${
              isError ? "border-[#ff6e84]/20 bg-[#ff6e84]/[0.05]" : "border-amber-500/20 bg-amber-500/[0.05]"
            }`}>
              <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${
                isError ? "bg-[#ff6e84]/20 text-[#ff6e84]" : "bg-amber-500/20 text-amber-500"
              }`}>
                <AlertTriangle className="h-6 w-6" />
              </div>
              <p className="text-[14px] font-bold text-white/90 leading-tight">
                {line.split(" ").map((word, i) => (
                  <span key={i} className={word.includes("₹") || (i > 0 && line.split(" ")[i-1].toLowerCase() === "in") ? (isError ? "text-[#ff6e84]" : "text-amber-500") : ""}>
                    {word}{" "}
                  </span>
                ))}
              </p>
            </div>
          );
        })}
      </div>

      {/* FOOTER INFO */}
      <div className="mt-6 flex items-center gap-2 text-[12px] font-medium text-slate-500">
        <Info className="h-4 w-4" />
        Enter a valid category budget amount.
      </div>

      {message ? (
        <div className="fixed bottom-10 right-10 z-50 flex items-center gap-4 rounded-2xl bg-[#5D57E8] pl-5 pr-4 py-3.5 text-white shadow-[0_20px_50px_rgba(0,0,0,0.3)] animate-in fade-in slide-in-from-bottom-5">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span className="text-[12px] font-bold tracking-tight leading-none mb-[0.5px]">
              {message}
            </span>
          </div>
          <button 
            onClick={() => setMessage("")}
            className="ml-2 rounded-lg p-1 hover:bg-white/10 transition-colors shrink-0"
          >
            <X className="h-4 w-4 text-white/70" />
          </button>
        </div>
      ) : null}
    </section>
  );
}

function SelectField({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <div className="relative group min-w-[110px]">
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-[40px] w-full appearance-none rounded-xl border border-white/[0.1] bg-[#060A16] pl-4 pr-10 text-[13px] font-bold text-white outline-none focus:border-[#A897FF]/50 transition-all cursor-pointer hover:bg-[#090D1A] shadow-inner truncate"
      >
        {options.map((option) => (
          <option key={option} value={option} className="bg-[#0A0F1E] text-white py-2">
            {option}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500 group-hover:text-white transition-colors" />
    </div>
  );
}
