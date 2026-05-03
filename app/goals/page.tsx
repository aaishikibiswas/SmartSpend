"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Target, Plus } from "lucide-react";
import { apiClient, type GoalItem } from "@/lib/api-client";
import { useFinance } from "@/context/FinanceContext";

function classifyTransaction(tx: { type?: string; amount?: number }) {
  const normalizedType = String(tx.type || "").toLowerCase();
  const amount = Number(tx.amount || 0);
  if (normalizedType === "income" || normalizedType === "credit") return "income";
  if (normalizedType === "expense" || normalizedType === "debit") return "expense";
  return amount >= 0 ? "income" : "expense";
}

export default function GoalsPage() {
  const { transactions } = useFinance();
  const [goals, setGoals] = useState<GoalItem[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await apiClient.getGoals();
        setGoals(res.data);
      } catch (error) {
        console.error(error);
        setGoals([]);
      }
    }

    load();
  }, []);

  const monthlyNetSavings = useMemo(() => {
    const now = new Date();
    const month = now.getMonth();
    const year = now.getFullYear();
    let income = 0;
    let expense = 0;
    for (const tx of transactions) {
      const parsed = new Date(tx.rawDate || tx.date);
      if (Number.isNaN(parsed.getTime())) continue;
      if (parsed.getMonth() !== month || parsed.getFullYear() !== year) continue;
      const kind = classifyTransaction(tx);
      if (kind === "income") income += Math.abs(Number(tx.amount || 0));
      if (kind === "expense") expense += Math.abs(Number(tx.amount || 0));
    }
    return Math.max(0, income - expense);
  }, [transactions]);

  const liveGoals = useMemo(() => {
    if (goals.length === 0) return goals;
    const totalTarget = goals.reduce((sum, goal) => sum + Math.max(0, Number(goal.target || 0)), 0);
    if (totalTarget <= 0) return goals;
    return goals.map((goal) => {
      const target = Math.max(0, Number(goal.target || 0));
      const share = target / totalTarget;
      const inferredContribution = monthlyNetSavings * share;
      const achieved = Math.min(target, Math.max(Number(goal.achieved || 0), Number(goal.achieved || 0) + inferredContribution));
      return { ...goal, achieved };
    });
  }, [goals, monthlyNetSavings]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Financial Goals</h1>
        <Link href="/settings" className="flex items-center gap-2 bg-[#8B5CF6] hover:bg-[#A78BFA] text-white px-4 py-2 rounded-xl transition-colors shadow-[0_0_15px_rgba(139,92,246,0.3)]">
          <Plus className="w-4 h-4" /> Configure Goals
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        {liveGoals.map((goal) => {
          const percent = Math.min(100, Math.round((goal.achieved / goal.target) * 100));
          return (
            <div key={goal.id} className="glass-card p-6 flex flex-col gap-4 group hover:bg-[#1A2035]/80 transition-colors cursor-pointer">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-white/5 rounded-xl border border-white/10 group-hover:bg-white/10 transition-colors">
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">{goal.name}</h3>
                    <p className="text-gray-400 text-sm">{goal.daysLeft} days remaining</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-white">{percent}%</p>
                </div>
              </div>

              <div className="mt-2">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400 font-medium">Rs. {goal.achieved.toLocaleString()}</span>
                  <span className="text-white font-bold">Rs. {goal.target.toLocaleString()}</span>
                </div>
                <div className="w-full bg-[#0B0E14] rounded-full h-2.5 border border-white/5 overflow-hidden">
                  <div className={`h-2.5 rounded-full ${goal.color} transition-all duration-1000 ease-out`} style={{ width: `${percent}%` }}></div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
