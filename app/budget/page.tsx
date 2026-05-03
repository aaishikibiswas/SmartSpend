"use client";

import Link from "next/link";
import { useMemo } from "react";
import { PieChart, AlertTriangle, Settings2 } from "lucide-react";
import { useFinance } from "@/context/FinanceContext";

function formatCurrency(value: number) {
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

export default function BudgetPage() {
  const { transactions } = useFinance();

  const budgetView = useMemo(() => {
    let totalIncome = 0;
    let totalExpense = 0;
    for (const tx of transactions) {
      if (tx.type === "income") totalIncome += tx.amount;
      if (tx.type === "expense") totalExpense += Math.abs(tx.amount);
    }
    const savingsRatio = totalIncome > 0 ? Number((((totalIncome - totalExpense) / totalIncome) * 100).toFixed(2)) : 0;
    const warnings: string[] = [];
    if (savingsRatio < 20) warnings.push("Savings ratio is below recommended 20%.");
    if (totalExpense > totalIncome && totalIncome > 0) warnings.push("Expense exceeds income.");
    return { totalExpense, savingsRatio, warnings };
  }, [transactions]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Budget Center</h1>
          <p className="text-gray-400 mt-2">Track spending and review budget-related signals from imported and synced transactions.</p>
        </div>
        <Link href="/settings" className="flex items-center gap-2 bg-[#8B5CF6] hover:bg-[#A78BFA] text-white px-4 py-2 rounded-xl transition-colors">
          <Settings2 className="w-4 h-4" />
          Edit Budget Settings
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <PieChart className="w-6 h-6 text-purple-400 mb-3" />
          <p className="text-sm text-gray-400 mb-2">Current Imported + Synced Spend</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(budgetView.totalExpense)}</p>
          <p className="text-gray-400 mt-2">Savings ratio is currently {budgetView.savingsRatio}%.</p>
        </div>
        <div className="glass-card p-6">
          <AlertTriangle className="w-6 h-6 text-rose-400 mb-3" />
          <p className="text-sm text-gray-400 mb-2">Budget Alerts</p>
          <p className="text-2xl font-bold text-white">{budgetView.warnings.length}</p>
          <p className="text-gray-400 mt-2">Live warning signals derived from current transaction flow.</p>
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-xl font-bold text-white mb-4">Live Budget Signals</h2>
        <div className="flex flex-col gap-3">
          {budgetView.warnings.length === 0 ? <p className="text-gray-400">No active budget warnings right now.</p> : null}
          {budgetView.warnings.map((warning, index) => (
            <div key={`${warning}-${index}`} className="rounded-xl border border-white/5 bg-white/5 p-4">
              <p className="font-semibold text-white">Budget Warning</p>
              <p className="text-sm text-gray-400 mt-1">{warning}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
