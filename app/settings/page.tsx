"use client";

import { useEffect, useMemo, useState } from "react";
import { BellRing, LoaderCircle, Plus, Save, Settings as SettingsIcon, Shield, Sliders, Trash2 } from "lucide-react";
import { apiClient, type BudgetCategoryItem, type GlobalBudgetSummary } from "@/lib/api-client";

type CategoryDraft = {
  name: string;
  amount: string;
  frequency: string;
};

const DEFAULT_GLOBAL: GlobalBudgetSummary = {
  monthly_budget: 50000,
  weekly_budget: 11500,
  spent_amount: 0,
  remaining_amount: 0,
  usage_percent: 0,
  daily_allowance: 0,
  auto_distribute: false,
  status: "healthy",
};

function toDraft(item: BudgetCategoryItem): CategoryDraft {
  return {
    name: item.name,
    amount: String(Math.round(item.allocated_amount)),
    frequency: item.frequency || "Monthly",
  };
}

export default function SettingsPage() {
  const [globalBudget, setGlobalBudget] = useState<GlobalBudgetSummary>(DEFAULT_GLOBAL);
  const [categoryDrafts, setCategoryDrafts] = useState<CategoryDraft[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  const weeklyTarget = useMemo(() => Math.round(Number(globalBudget.monthly_budget || 0) / 4.33), [globalBudget.monthly_budget]);

  useEffect(() => {
    async function loadBudgets() {
      setIsLoading(true);
      setMessage("");
      try {
        const [globalResponse, categoriesResponse] = await Promise.all([apiClient.getGlobalBudget(), apiClient.getCategoryBudgets()]);
        setGlobalBudget(globalResponse.data);
        setCategoryDrafts(categoriesResponse.data.map(toDraft));
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "Unable to load budget settings.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadBudgets();
  }, []);

  function updateCategory(index: number, patch: Partial<CategoryDraft>) {
    setCategoryDrafts((current) => current.map((entry, entryIndex) => (entryIndex === index ? { ...entry, ...patch } : entry)));
  }

  function addCategoryDraft() {
    setCategoryDrafts((current) => [...current, { name: "", amount: "", frequency: "Monthly" }]);
  }

  function removeCategoryDraft(index: number) {
    setCategoryDrafts((current) => current.filter((_, entryIndex) => entryIndex !== index));
  }

  async function saveChanges() {
    setMessage("");
    setIsSaving(true);
    try {
      const monthlyBudget = Number(globalBudget.monthly_budget);
      if (!Number.isFinite(monthlyBudget) || monthlyBudget < 0) {
        setMessage("Enter a valid monthly budget.");
        return;
      }

      const validDrafts = categoryDrafts
        .map((entry) => ({ ...entry, name: entry.name.trim(), amountValue: Number(entry.amount) }))
        .filter((entry) => entry.name && Number.isFinite(entry.amountValue) && entry.amountValue >= 0);

      const globalResponse = await apiClient.updateGlobalBudget({
        monthly_budget: monthlyBudget,
        auto_distribute: globalBudget.auto_distribute,
      });

      const savedCategories: BudgetCategoryItem[] = [];
      for (const entry of validDrafts) {
        const response = await apiClient.upsertCategoryBudget({
          name: entry.name,
          amount: entry.amountValue,
          frequency: entry.frequency,
        });
        savedCategories.push(response.data.category);
      }

      setGlobalBudget(globalResponse.data.global);
      setCategoryDrafts((savedCategories.length > 0 ? savedCategories : globalResponse.data.categories).map(toDraft));
      setMessage("Budget settings saved.");
      window.dispatchEvent(new Event("smartspend:budget-updated"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to save budget settings.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8">
      <div>
        <h1 className="bg-gradient-to-r from-white to-gray-400 bg-clip-text text-3xl font-bold text-transparent">Settings</h1>
        <p className="mt-2 text-gray-400">Manage your budget preferences and account settings.</p>
      </div>

      <div className="flex gap-8">
        <div className="flex w-48 shrink-0 flex-col gap-2 xl:w-64">
          <button className="flex items-center gap-3 rounded-xl border border-[#2A324A] bg-[#1A2035] px-4 py-3 font-semibold text-white transition-colors">
            <Sliders className="h-5 w-5 text-[#8B5CF6]" /> Budgets
          </button>
          <button className="flex items-center gap-3 rounded-xl px-4 py-3 text-gray-400 transition-colors hover:bg-white/5 hover:text-white">
            <BellRing className="h-5 w-5" /> Notifications
          </button>
          <button className="flex items-center gap-3 rounded-xl px-4 py-3 text-gray-400 transition-colors hover:bg-white/5 hover:text-white">
            <Shield className="h-5 w-5" /> Security
          </button>
          <button className="flex items-center gap-3 rounded-xl px-4 py-3 text-gray-400 transition-colors hover:bg-white/5 hover:text-white">
            <SettingsIcon className="h-5 w-5" /> General
          </button>
        </div>

        <div className="flex flex-1 flex-col gap-6">
          <div className="glass-card p-6">
            <h2 className="mb-6 text-xl font-bold text-white">Global Budgets</h2>

            <div className="flex flex-col gap-6">
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-400">Monthly Budget</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-gray-500">Rs.</span>
                  <input
                    type="number"
                    value={globalBudget.monthly_budget}
                    onChange={(event) => setGlobalBudget((current) => ({ ...current, monthly_budget: Number(event.target.value) || 0 }))}
                    className="w-full rounded-xl border border-[#2A324A] bg-[#0B0E14] py-3 pl-12 pr-4 text-base text-white outline-none transition-colors focus:border-[#8B5CF6]"
                  />
                </div>
                <p className="mt-2 text-xs text-gray-500">Your predictions and category limits use this monthly cap.</p>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-400">Weekly Target Spend</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 font-bold text-gray-500">Rs.</span>
                  <input
                    type="number"
                    value={weeklyTarget}
                    readOnly
                    className="w-full rounded-xl border border-[#2A324A] bg-[#0B0E14] py-3 pl-12 pr-4 text-base text-white outline-none"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <div className="mb-6 flex items-center justify-between gap-4">
              <h2 className="text-xl font-bold text-white">Category Allocation</h2>
              {isLoading ? <LoaderCircle className="h-5 w-5 animate-spin text-[#8B5CF6]" /> : null}
            </div>

            <div className="flex flex-col gap-4">
              {categoryDrafts.map((category, index) => (
                <div key={`${category.name || "new"}-${index}`} className="grid grid-cols-[minmax(120px,1fr)_minmax(120px,1fr)_44px] items-center gap-4">
                  <input
                    value={category.name}
                    onChange={(event) => updateCategory(index, { name: event.target.value })}
                    placeholder="Category"
                    className="rounded-lg border border-[#2A324A] bg-[#0B0E14] px-4 py-2 text-sm text-white outline-none transition-colors focus:border-[#8B5CF6]"
                  />
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-bold text-gray-500">Rs.</span>
                    <input
                      type="number"
                      value={category.amount}
                      onChange={(event) => updateCategory(index, { amount: event.target.value })}
                      className="w-full rounded-lg border border-[#2A324A] bg-[#0B0E14] py-2 pl-10 pr-4 text-sm text-white outline-none transition-colors focus:border-[#8B5CF6]"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeCategoryDraft(index)}
                    className="flex h-10 w-10 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-white/5 hover:text-white"
                    aria-label="Remove category"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>

            <button type="button" onClick={addCategoryDraft} className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[#8B5CF6] transition-colors hover:text-[#A78BFA]">
              <Plus className="h-4 w-4" /> Add Category Restriction
            </button>
          </div>

          <div className="flex items-center justify-between gap-4">
            <p className={`text-sm ${message.includes("saved") ? "text-emerald-300" : "text-rose-300"}`}>{message}</p>
            <button
              type="button"
              onClick={() => void saveChanges()}
              disabled={isSaving || isLoading}
              className="flex items-center gap-2 rounded-xl bg-[#8B5CF6] px-6 py-3 font-bold text-white shadow-[0_0_15px_rgba(139,92,246,0.3)] transition-all hover:bg-[#A78BFA] hover:shadow-[0_0_25px_rgba(139,92,246,0.5)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSaving ? <LoaderCircle className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
              Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
