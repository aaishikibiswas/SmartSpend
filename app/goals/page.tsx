"use client";

import Link from "next/link";
import { useMemo } from "react";
import { Target, Plus } from "lucide-react";
import { useFinance } from "@/context/FinanceContext";

export default function GoalsPage() {
  const { transactions, goals } = useFinance();

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
    return goals.map((goal) => {
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

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Financial Goals</h1>
        <Link href="/settings" className="flex items-center gap-2 bg-[#8BE2E8] hover:bg-[#A897FF] text-white px-4 py-2 rounded-xl transition-colors shadow-[0_0_15px_rgba(139,92,246,0.3)]">
          <Plus className="w-4 h-4" /> Configure Goals
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        {updatedGoals.map((goal) => {
          const percent = Number(goal.progress);
          return (
            <div key={goal.id} className="glass-card p-6 flex flex-col gap-4 group hover:bg-[#10182E]/80 transition-colors cursor-pointer">
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
                  <span className="text-gray-400 font-medium">Rs. {goal.savedAmount.toLocaleString()}</span>
                  <span className="text-white font-bold">Rs. {goal.target.toLocaleString()}</span>
                </div>
                <div className="w-full bg-[#050816] rounded-full h-2.5 border border-white/5 overflow-hidden">
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
