"use client";

import { useMemo } from "react";
import { Landmark, ArrowUpRight, ArrowDownRight, PiggyBank } from "lucide-react";
import { useFinance } from "@/context/FinanceContext";

function formatCurrency(value: number) {
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

export default function WalletPage() {
  const { transactions } = useFinance();

  const metrics = useMemo(() => {
    const totalIncome = transactions.filter((tx) => tx.type === "income").reduce((sum, tx) => sum + tx.amount, 0);
    const totalExpense = transactions.filter((tx) => tx.type === "expense").reduce((sum, tx) => sum + Math.abs(tx.amount), 0);
    const netSavings = totalIncome - totalExpense;
    const totalBalance = netSavings;
    const savingsRatio = totalIncome > 0 ? Number(((netSavings / totalIncome) * 100).toFixed(2)) : 0;
    const healthScore = Math.max(0, Math.min(100, Math.round(50 + savingsRatio / 2)));
    return { totalBalance, totalIncome, totalExpense, netSavings, savingsRatio, healthScore };
  }, [transactions]);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Wallet Overview</h1>
        <p className="text-gray-400 mt-2">A clean summary of the balances and cashflow coming from your imported and synced data.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div id="savings-health" className="glass-card scroll-mt-28 p-6">
          <Landmark className="w-6 h-6 text-blue-400 mb-3" />
          <p className="text-sm text-gray-400 mb-2">Current Balance</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(metrics.totalBalance)}</p>
        </div>
        <div className="glass-card p-6">
          <ArrowUpRight className="w-6 h-6 text-emerald-400 mb-3" />
          <p className="text-sm text-gray-400 mb-2">Total Income</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(metrics.totalIncome)}</p>
        </div>
        <div className="glass-card p-6">
          <ArrowDownRight className="w-6 h-6 text-rose-400 mb-3" />
          <p className="text-sm text-gray-400 mb-2">Total Expense</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(metrics.totalExpense)}</p>
        </div>
      </div>

      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-4">
          <PiggyBank className="w-5 h-5 text-purple-400" />
          <h2 className="text-xl font-bold text-white">Savings Health</h2>
        </div>
        <p className="text-gray-300">Net savings: {formatCurrency(metrics.netSavings)}</p>
        <p className="text-gray-400 mt-2">Savings ratio: {metrics.savingsRatio}%</p>
        <p className="text-gray-400 mt-2">Health score: {metrics.healthScore}/100</p>
      </div>
    </div>
  );
}
