"use client";

import { useMemo, useState } from "react";
import { Laptop, PlusCircle, ShieldAlert, Plane, Calendar } from "lucide-react";
import { apiClient, type GoalSuggestion } from "@/lib/api-client";
import { useFinance } from "@/context/FinanceContext";
import CalendarPopup from "./CalendarPopup";
import { AnimatePresence } from "framer-motion";

function goalIcon(index: number) {
  return [Laptop, ShieldAlert, Plane][index] ?? Laptop;
}

function goalTone(index: number) {
  return [
    { text: "text-[#A897FF]", bg: "bg-[#A897FF]/10", bar: "bg-[#A897FF]" },
    { text: "text-[#a88cfb]", bg: "bg-[#a88cfb]/10", bar: "bg-[#a88cfb]" },
    { text: "text-[#ffa5d9]", bg: "bg-[#ffa5d9]/10", bar: "bg-[#ffa5d9]" },
  ][index] ?? { text: "text-[#A897FF]", bg: "bg-[#A897FF]/10", bar: "bg-[#A897FF]" };
}

function formatCurrency(value: number) {
  return `Rs${Math.round(value).toLocaleString()}`;
}

function formatDate(date: Date | null) {
  if (!date) return "Select target date";
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export default function GoalTracker({ suggestion }: { suggestion: GoalSuggestion }) {
  const { transactions, goals, appendGoal } = useFinance();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [target, setTarget] = useState("");
  const [targetDate, setTargetDate] = useState<Date | null>(null);
  const [showCalendar, setShowCalendar] = useState(false);
  const [error, setError] = useState("");

  const daysUntil = useMemo(() => {
    if (!targetDate) return 0;
    const diff = targetDate.getTime() - new Date().getTime();
    return Math.max(1, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  }, [targetDate]);

  async function handleCreateGoal() {
    setError("");
    const normalizedName = name.trim();
    const targetValue = Number(target);

    if (!normalizedName || !Number.isFinite(targetValue) || targetValue <= 0 || !targetDate) {
      setError("Enter goal name, target amount, and date.");
      return;
    }

    try {
      const created = await apiClient.addGoal({
        name: normalizedName,
        target: targetValue,
        achieved: 0,
        daysLeft: daysUntil,
        color: "bg-[#8BE2E8]",
      });
      appendGoal(created.data);
      setName("");
      setTarget("");
      setTargetDate(null);
      setShowCreate(false);
      window.dispatchEvent(new Event("smartspend:goals-updated"));
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create goal right now.");
    }
  }

  const currentSavings = useMemo(() => {
    let income = 0;
    let expense = 0;
    for (const tx of transactions) {
      if (tx.type === "income") income += Number(tx.amount || 0);
      if (tx.type === "expense") expense += Math.abs(Number(tx.amount || 0));
    }
    return income - expense;
  }, [transactions]);

  const updatedGoals = useMemo(() => {
    return goals.slice(0, 3).map((goal) => {
      const target = Math.max(0, Number(goal.target || 0));
      const savedAmount = Math.max(0, Math.min(currentSavings, target));
      const progress = target > 0 ? Math.max(0, Math.min((currentSavings / target) * 100, 100)) : 0;
      return {
        ...goal,
        achieved: savedAmount,
        savedAmount,
        progress: progress.toFixed(0),
      };
    });
  }, [goals, currentSavings]);

  const liveSuggestedContribution = useMemo(() => {
    return Math.max(Math.round(Math.max(currentSavings, 0) * 0.3), Math.round(suggestion.recommendedContribution || 0));
  }, [currentSavings, suggestion.recommendedContribution]);

  return (
    <section className="glass-card rounded-[2rem] p-8">
      <div className="mb-6 flex items-center justify-between">
        <h4 className="font-bold text-[#F4F6FF]">Financial Goals</h4>
        <PlusCircle className="h-5 w-5 cursor-pointer text-[#B7BDD9] transition-colors hover:text-[#A897FF]" />
      </div>

      <div className="space-y-10">
        {updatedGoals.length === 0 ? <p className="text-sm text-[#B7BDD9]">No goals yet.</p> : null}

        {updatedGoals.map((goal, index) => {
          const percent = Number(goal.progress);
          const remaining = Math.max(0, goal.target - goal.savedAmount);
          const Icon = goalIcon(index);
          const tone = goalTone(index);

          return (
            <div key={goal.id} className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${tone.bg} ${tone.text}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold leading-tight text-[#F4F6FF]">{goal.name}</p>
                    <p className="text-[10px] font-medium text-[#B7BDD9]">
                      {formatCurrency(goal.savedAmount)} saved of {formatCurrency(goal.target)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-manrope text-lg font-black ${tone.text}`}>{percent}%</p>
                  <p className={`text-[9px] font-bold uppercase tracking-widest ${tone.text}`}>
                    {percent >= 90 ? "Nearly Goal" : percent >= 45 ? "On Track" : "Progress"}
                  </p>
                </div>
              </div>

              <div className="pt-1">
                <div className="flex h-3 overflow-hidden rounded-full border border-[rgba(255,255,255,0.05)]/10 bg-[#10182E] shadow-inner">
                  <div className={`${tone.bar} relative rounded-full`} style={{ width: `${percent}%` }}>
                    <div className="absolute bottom-0 right-0 top-0 w-2 bg-white/20 blur-[2px]" />
                  </div>
                </div>
                <div className="mt-2 flex justify-between">
                  <div className="flex flex-col">
                    <span className="text-[9px] font-bold uppercase tracking-tighter text-[#B7BDD9]">Remaining</span>
                    <span className="text-xs font-bold text-[#F4F6FF]">{formatCurrency(remaining)}</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[9px] font-bold uppercase tracking-tighter text-[#B7BDD9]">Deadline</span>
                    <span className="text-xs font-bold text-[#F4F6FF]">{goal.daysLeft} days left</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8">
        <div className="mb-4 rounded-2xl border border-[rgba(255,255,255,0.05)]/20 bg-[#10182E] px-4 py-3 text-xs text-[#B7BDD9]">
          <span className="font-semibold text-[#F4F6FF]">Suggested contribution:</span> Rs{Math.round(liveSuggestedContribution).toLocaleString()}
          <p className="mt-1">{suggestion.message}</p>
        </div>
        <button onClick={() => setShowCreate((current) => !current)} className="flex w-full items-center justify-center gap-2 rounded-2xl border border-[rgba(255,255,255,0.05)]/30 bg-[#10182E] py-3 text-xs font-bold text-[#F4F6FF] transition-colors hover:bg-[#1f2b49]">
          <PlusCircle className="h-4 w-4" /> Create New Goal
        </button>
        {showCreate ? (
          <div className="mt-3 space-y-2 rounded-2xl border border-white/10 bg-white/5 p-3">
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Goal name" className="h-10 w-full rounded-xl border border-white/8 bg-[#10182E] px-3 text-sm text-white outline-none placeholder:text-[#6D769B] focus:border-[#7B6CF6]/50 transition-all" />
            <input value={target} onChange={(event) => setTarget(event.target.value)} type="number" min="1" placeholder="Target amount" className="h-10 w-full rounded-xl border border-white/8 bg-[#10182E] px-3 text-sm text-white outline-none placeholder:text-[#6D769B] focus:border-[#7B6CF6]/50 transition-all" />
            
            <div className="relative">
              <button 
                type="button"
                onClick={() => setShowCalendar(!showCalendar)}
                className="flex h-10 w-full items-center justify-between rounded-xl border border-white/8 bg-[#10182E] px-3 text-sm text-white outline-none transition-all hover:bg-[#1f2b49] focus:border-[#7B6CF6]/50"
              >
                <span className={targetDate ? "text-white" : "text-[#6D769B]"}>
                  {formatDate(targetDate)}
                </span>
                <Calendar className="h-4 w-4 text-[#7B6CF6]" />
              </button>
              
              <AnimatePresence>
                {showCalendar && (
                  <CalendarPopup 
                    selectedDate={targetDate} 
                    onSelect={(date) => {
                      setTargetDate(date);
                      setShowCalendar(false);
                    }} 
                    onClose={() => setShowCalendar(false)} 
                  />
                )}
              </AnimatePresence>
            </div>

            {targetDate && target && (
              <div className="flex flex-col gap-1 px-1">
                <p className="text-[10px] font-bold text-[#8BE2E8] uppercase tracking-wider">
                  Target in {daysUntil} days
                </p>
                <p className="text-[10px] font-bold text-[#A897FF] uppercase tracking-wider">
                  Recommended: Rs. {Math.round(Number(target) / Math.max(1, daysUntil / 30)).toLocaleString()}/mo
                </p>
              </div>
            )}

            {error ? <p className="text-xs text-rose-300">{error}</p> : null}
            <button type="button" onClick={() => void handleCreateGoal()} className="w-full rounded-xl bg-[#7B6CF6] px-3 py-2 text-sm font-semibold text-white transition hover:bg-[#8B7DFF] shadow-[0_0_15px_rgba(123,108,246,0.3)]">
              Add Goal
            </button>
          </div>
        ) : null}
      </div>
    </section>
  );
}
