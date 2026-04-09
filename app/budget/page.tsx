import Link from "next/link";
import { PieChart, AlertTriangle, Settings2 } from "lucide-react";

const BACKEND_BASE = process.env.BACKEND_API_BASE || "http://127.0.0.1:8001";

async function getDashboard() {
  const response = await fetch(`${BACKEND_BASE}/dashboard/`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to load budget data.");
  }
  return response.json();
}

async function getAlerts() {
  const response = await fetch(`${BACKEND_BASE}/alerts/`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to load alerts.");
  }
  return response.json();
}

function formatCurrency(value: number) {
  return `Rs. ${Number(value || 0).toLocaleString()}`;
}

export default async function BudgetPage() {
  const dashboard = await getDashboard();
  const alerts = await getAlerts();
  const metrics = dashboard.data.metrics;
  const budgetAlerts = alerts.data.filter((item: { type: string }) => item.type === "breach" || item.type === "warning");

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Budget Center</h1>
          <p className="text-gray-400 mt-2">Track your imported spending and review budget-related alerts.</p>
        </div>
        <Link href="/settings" className="flex items-center gap-2 bg-[#8B5CF6] hover:bg-[#A78BFA] text-white px-4 py-2 rounded-xl transition-colors">
          <Settings2 className="w-4 h-4" />
          Edit Budget Settings
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <PieChart className="w-6 h-6 text-purple-400 mb-3" />
          <p className="text-sm text-gray-400 mb-2">Current Imported Spend</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(metrics.totalExpense)}</p>
          <p className="text-gray-400 mt-2">Savings ratio is currently {metrics.savingsRatio}%.</p>
        </div>
        <div className="glass-card p-6">
          <AlertTriangle className="w-6 h-6 text-rose-400 mb-3" />
          <p className="text-sm text-gray-400 mb-2">Budget Alerts</p>
          <p className="text-2xl font-bold text-white">{budgetAlerts.length}</p>
          <p className="text-gray-400 mt-2">Active warning or breach alerts generated from uploaded transactions.</p>
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-xl font-bold text-white mb-4">Live Budget Signals</h2>
        <div className="flex flex-col gap-3">
          {budgetAlerts.length === 0 ? <p className="text-gray-400">No active budget warnings right now.</p> : null}
          {budgetAlerts.map((alert: { id: number; title: string; message: string }) => (
            <div key={alert.id} className="rounded-xl border border-white/5 bg-white/5 p-4">
              <p className="font-semibold text-white">{alert.title}</p>
              <p className="text-sm text-gray-400 mt-1">{alert.message}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
