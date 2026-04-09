"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { AlertTriangle, CheckCircle2, ChevronDown, LoaderCircle, Plus, Scale, ShoppingBag, UtensilsCrossed, WalletCards, X } from "lucide-react";
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

function getIcon(name: string): LucideIcon {
  return name.toLowerCase().includes("food") ? UtensilsCrossed : ShoppingBag;
}

function getDecisionTone(status: string) {
  if (status === "success") return "border-emerald-400/30 bg-emerald-500/10 text-emerald-200";
  if (status === "warning") return "border-amber-400/30 bg-amber-500/10 text-amber-100";
  return "border-rose-400/30 bg-rose-500/10 text-rose-100";
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

  const progressTone = globalUsage >= 100 ? "bg-rose-400" : globalUsage >= 80 ? "bg-amber-400" : "bg-emerald-400";

  return (
    <section className="rounded-[2.5rem] bg-[#111a31] p-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]">
      <div className="mb-8 flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h2 className="text-2xl font-bold text-[#dee5ff]">Financial Settings &amp; Budgeting</h2>
          <p className="text-sm text-[#a3aac4]">Configure your global limits and category-wise constraints</p>
        </div>

        <div className="flex rounded-full border border-[#40485d]/20 bg-[#192540] p-1">
          <button
            type="button"
            onClick={() => setView("monthly")}
            className={`rounded-full px-6 py-2 text-xs font-bold transition-all ${
              view === "monthly" ? "bg-[#a3a6ff] text-[#0f00a4]" : "text-[#a3aac4] hover:text-[#dee5ff]"
            }`}
          >
            Monthly
          </button>
          <button
            type="button"
            onClick={() => setView("weekly")}
            className={`rounded-full px-6 py-2 text-xs font-bold transition-all ${
              view === "weekly" ? "bg-[#a3a6ff] text-[#0f00a4]" : "text-[#a3aac4] hover:text-[#dee5ff]"
            }`}
          >
            Weekly
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 xl:grid-cols-[280px_minmax(0,1fr)]">
        <div className="space-y-5">
          <div>
            <label className="mb-2 block text-[10px] font-bold uppercase tracking-widest text-[#a3aac4]">Global Monthly Budget</label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-[#a3a6ff]">₹</span>
              <input
                type="number"
                value={globalMonthly}
                onChange={(event) => setGlobalMonthly(Number(event.target.value) || 0)}
                className="h-[56px] w-full rounded-2xl border border-[#40485d]/10 bg-[#192540] py-3 pl-8 pr-4 text-2xl font-bold text-[#dee5ff] outline-none"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-[11px] text-[#a3aac4]">
            <input checked={autoDistribute} onChange={(event) => setAutoDistribute(event.target.checked)} type="checkbox" className="accent-[#a3a6ff]" />
            Auto-distribute across active categories
          </label>

          <button
            type="button"
            onClick={() => void handleSaveGlobalBudget()}
            disabled={isPending}
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[#a3a6ff] px-4 py-3 text-sm font-bold text-[#0f00a4] disabled:opacity-60"
          >
            {isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <WalletCards className="h-4 w-4" />}
            Save Budget Logic
          </button>

          <div className="rounded-3xl border border-[#40485d]/10 bg-[#0f172b] p-4">
            <div className="mb-3 flex items-center justify-between text-xs font-semibold text-[#dee5ff]">
              <span>Budget Progress</span>
              <span>{Math.round(globalUsage)}%</span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-[#192540]">
              <div className={`h-full rounded-full ${progressTone}`} style={{ width: `${Math.min(globalUsage, 100)}%` }} />
            </div>
            <div className="mt-3 space-y-1 text-xs text-[#a3aac4]">
              <p>You have ₹{Math.round(budgetSnapshot.global.remaining_amount).toLocaleString()} left this month.</p>
              <p>Daily allowance: ₹{Math.round(budgetSnapshot.global.daily_allowance).toLocaleString()}</p>
            </div>
          </div>

          <div className="rounded-3xl border border-[#40485d]/10 bg-[#0f172b] p-4">
            <div className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.24em] text-[#a3a6ff]">
              <Scale className="h-4 w-4" />
              Decision Engine
            </div>
            <p className="mb-3 text-xs text-[#a3aac4]">Can I afford a new purchase?</p>
            <div className="space-y-3">
              <input
                value={decisionItem}
                onChange={(event) => setDecisionItem(event.target.value)}
                placeholder="Item name..."
                className="h-11 w-full rounded-2xl border border-[#40485d]/10 bg-[#192540] px-4 text-sm text-[#dee5ff] outline-none"
              />
              <div className="flex gap-2">
                <input
                  type="number"
                  value={decisionPrice}
                  onChange={(event) => setDecisionPrice(event.target.value)}
                  placeholder="₹ Price"
                  className="h-11 flex-1 rounded-2xl border border-[#40485d]/10 bg-[#192540] px-4 text-sm text-[#dee5ff] outline-none"
                />
                <button
                  type="button"
                  onClick={() => void handleDecisionCheck()}
                  className="rounded-2xl bg-[#7c72ff] px-5 text-sm font-bold text-white"
                >
                  Check
                </button>
              </div>
            </div>
            {decisionResult ? (
              <div className={`mt-4 rounded-2xl border p-3 text-xs ${getDecisionTone(decisionResult.status)}`}>
                <p className="font-bold">{decisionResult.affordability === "Yes" ? "You can afford this." : decisionResult.affordability === "Maybe" ? "Proceed carefully." : "Not affordable right now."}</p>
                <p className="mt-1">{decisionResult.recommendation}</p>
                <p className="mt-2">Impact: {decisionResult.budget_impact_percent}% of monthly budget | New risk: {decisionResult.new_risk_level}</p>
              </div>
            ) : null}
          </div>
        </div>

        <div className="rounded-3xl border border-[#40485d]/10 bg-[#091328]/30 p-6">
          <h4 className="mb-4 flex items-center gap-2 text-sm font-bold text-[#dee5ff]">
            <ShoppingBag className="h-4 w-4 text-[#a3a6ff]" />
            Category Budget Management
          </h4>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-[1.1fr_0.9fr_0.8fr_auto]">
            <div>
              <label className="mb-1 ml-1 block text-[10px] font-bold text-[#a3aac4]">Category</label>
              <SelectField value={selectedCategory} onChange={setSelectedCategory} options={categoryOptions} />
            </div>
            <div>
              <label className="mb-1 ml-1 block text-[10px] font-bold text-[#a3aac4]">Frequency</label>
              <SelectField value={selectedFrequency} onChange={(value) => setSelectedFrequency(value as "Monthly" | "Weekly")} options={["Monthly", "Weekly"]} />
            </div>
            <div>
              <label className="mb-1 ml-1 block text-[10px] font-bold text-[#a3aac4]">Amount</label>
              <input
                type="number"
                value={amountInput}
                onChange={(event) => setAmountInput(event.target.value)}
                placeholder="₹ Amount"
                className="h-[38px] w-full rounded-xl border border-[#40485d]/10 bg-[#192540] px-3 py-2 text-xs text-[#dee5ff] outline-none placeholder:text-[#a3aac4]"
              />
            </div>
            <button
              type="button"
              onClick={() => void handleAddEntry()}
              disabled={isPending}
              className="mt-5 rounded-xl bg-[#a3a6ff]/20 p-2 text-[#a3a6ff] transition-colors hover:bg-[#a3a6ff]/30 disabled:opacity-50"
            >
              <Plus className="h-5 w-5" />
            </button>
          </div>

          <div className="mt-6 space-y-3">
            {entries.map((entry) => {
              const Icon = getIcon(entry.name);
              return (
                <div key={`${entry.name}-${entry.frequency}`} className="rounded-xl border border-[#40485d]/10 bg-[#141f38]/40 p-3">
                  <div className="flex items-center justify-between gap-4 text-xs">
                    <div className="flex items-center gap-3">
                      <Icon className="h-4 w-4 text-[#a88cfb]" />
                      <span className="font-semibold text-[#dee5ff]">{entry.name}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-[10px] uppercase text-[#a3aac4]">{entry.frequency}</span>
                      <span className="font-bold text-[#dee5ff]">₹{Math.round(entry.allocated_amount).toLocaleString()}</span>
                      <button type="button" onClick={() => void handleRemoveEntry(entry.name)} disabled={isPending} className="text-[#a3aac4] disabled:opacity-50">
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  <div className="mt-3">
                    <div className="flex justify-between text-[11px] text-[#a3aac4]">
                      <span>Spent ₹{Math.round(entry.spent_amount).toLocaleString()}</span>
                      <span>Remaining ₹{Math.round(entry.remaining_amount).toLocaleString()}</span>
                    </div>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#192540]">
                      <div
                        className={`${entry.usage_percent >= 100 ? "bg-rose-400" : entry.usage_percent >= 80 ? "bg-amber-400" : "bg-[#8b5cf6]"} h-full rounded-full`}
                        style={{ width: `${Math.min(entry.usage_percent, 100)}%` }}
                      />
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[10px]">
                      <span className={`${entry.status === "error" ? "text-rose-300" : entry.status === "warning" ? "text-amber-200" : "text-emerald-300"}`}>
                        {entry.status === "error" ? "Overspent" : entry.status === "warning" ? "Near limit" : "Healthy"}
                      </span>
                      <span className="text-[#a3aac4]">{Math.round(entry.usage_percent)}% used</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-3">
        {feedback.map((line) => (
          <div key={line} className="flex items-start gap-3 rounded-2xl border border-[#40485d]/10 bg-[#0f172b] px-4 py-3 text-sm text-[#dee5ff]">
            {line.toLowerCase().includes("over") ? <AlertTriangle className="mt-0.5 h-4 w-4 text-rose-300" /> : <CheckCircle2 className="mt-0.5 h-4 w-4 text-emerald-300" />}
            <span>{line}</span>
          </div>
        ))}
      </div>

      {message ? <p className="mt-4 text-[11px] text-[#a3a6ff]">{message}</p> : null}
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
    <div className="relative">
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-[38px] w-full appearance-none rounded-xl border border-[#40485d]/10 bg-[#192540] px-3 py-2 pr-9 text-xs text-[#dee5ff] outline-none"
      >
        {options.length === 0 ? (
          <option value="">No categories</option>
        ) : null}
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3aac4]" />
    </div>
  );
}
