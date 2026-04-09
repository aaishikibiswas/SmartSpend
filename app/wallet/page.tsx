import { Landmark, ArrowUpRight, ArrowDownRight, PiggyBank } from "lucide-react";

const BACKEND_BASE = process.env.BACKEND_API_BASE || "http://127.0.0.1:8001";

async function getDashboard() {
  const response = await fetch(`${BACKEND_BASE}/dashboard/`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to load wallet data.");
  }
  return response.json();
}

function formatCurrency(value: number) {
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

export default async function WalletPage() {
  const payload = await getDashboard();
  const metrics = payload.data.metrics;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Wallet Overview</h1>
        <p className="text-gray-400 mt-2">A clean summary of the balances and cashflow coming from your imported data.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6">
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
