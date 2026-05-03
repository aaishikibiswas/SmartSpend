"use client";

import { useMemo, useEffect, useState } from "react";
import { Landmark, ArrowUpRight, ArrowDownRight, PiggyBank } from "lucide-react";
import { useFinance } from "@/context/FinanceContext";
import NetWorthCard from "@/components/dashboard/NetWorthCard";
import { apiClient } from "@/lib/api-client";

function formatCurrency(value: number) {
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

export default function WalletPage() {
  const { transactions } = useFinance();
  const [networthData, setNetworthData] = useState<any>(null);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const res = await apiClient.getDashboardData();
        setNetworthData(res.data?.networth);
      } catch (e) {
        console.error(e);
      }
    }
    fetchDashboard();
  }, []);

  const metrics = useMemo(() => {
    let totalIncome = 0;
    let totalExpense = 0;
    for (const tx of transactions) {
      if (tx.type === "income") totalIncome += tx.amount;
      if (tx.type === "expense") totalExpense += Math.abs(tx.amount);
    }
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

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_320px] gap-6 items-start">
        <div className="flex flex-col gap-6">
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

        <div className="w-full">
          {networthData ? <NetWorthCard data={networthData} /> : <div className="glass-card p-6 text-center text-sm text-gray-400 animate-pulse">Loading net worth...</div>}
        </div>
      </div>
    </div>
  );
}
