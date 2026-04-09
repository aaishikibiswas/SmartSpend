import { CalendarClock, Flame, Landmark, PiggyBank, TrendingDown, TrendingUp, WalletMinimal } from "lucide-react";
import Header from "@/components/Header";
import ForecastChart from "@/components/dashboard/ForecastChart";
import CategoryChart from "@/components/dashboard/CategoryChart";
import BillReminders from "@/components/dashboard/BillReminders";
import TransactionHistory from "@/components/dashboard/TransactionHistory";
import AIChatbot from "@/components/dashboard/AIChatbot";
import AlertsPanel from "@/components/dashboard/AlertsPanel";
import GoalTracker from "@/components/dashboard/GoalTracker";
import BudgetingPanel from "@/components/dashboard/BudgetingPanel";
import HealthScoreCard from "@/components/dashboard/HealthScoreCard";
import SmartAdvice from "@/components/dashboard/SmartAdvice";
import DashboardLiveSocket from "@/components/dashboard/DashboardLiveSocket";
import LiveNotificationCenter from "@/components/dashboard/LiveNotificationCenter";
import RecurringFinancePanel from "@/components/dashboard/RecurringFinancePanel";
import NetWorthCard from "@/components/dashboard/NetWorthCard";
import CashFlowTimeline from "@/components/dashboard/CashFlowTimeline";
import ExpenseSplitCard from "@/components/dashboard/ExpenseSplitCard";
import PriorityPanel from "@/components/dashboard/PriorityPanel";
import MetricCard from "@/components/MetricCard";
import type { DashboardData } from "@/lib/api-client";
import { BACKEND_API_BASE as BACKEND_BASE } from "@/lib/backend-config";

export const dynamic = "force-dynamic";

function formatCurrency(value: number) {
  return `Rs${Number(value || 0).toLocaleString()}`;
}

async function getDashboardData(): Promise<DashboardData> {
  const response = await fetch(`${BACKEND_BASE}/dashboard/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Dashboard request failed with status ${response.status}.`);
  }

  const payload = await response.json();
  return payload.data as DashboardData;
}

export default async function Dashboard() {
  let data: DashboardData | null = null;
  let error = "";

  try {
    data = await getDashboardData();
  } catch (err) {
    console.error(err);
    error = err instanceof Error ? err.message : "Failed to load dashboard data.";
  }

  if (error || !data) {
    return <div className="flex justify-center p-10 text-sm font-semibold text-rose-300">{error || "Failed to load dashboard data."}</div>;
  }

  const { metrics, budgeting, categoryBreakdown, recentTransactions, goalSuggestion, subscriptions, emi, expenseSplit, networth, cashflow, priorities } = data;

  return (
    <div className="-mx-4 -my-5 pb-36 md:-mx-6 md:-my-6 xl:-mx-7 xl:-my-6">
      <DashboardLiveSocket />
      <LiveNotificationCenter />
      <Header financialPersonality={metrics.financialPersonality} />

      <div className="mx-auto w-full max-w-7xl space-y-8 px-8 py-8">
        <section className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard title="Total Balance" value={formatCurrency(metrics.totalBalance)} trend={metrics.trends.balanceTrend} icon={Landmark} color="blue" />
          <MetricCard title="Monthly Income" value={formatCurrency(metrics.totalIncome)} trend={metrics.trends.incomeTrend} icon={TrendingUp} color="purple" />
          <MetricCard title="Monthly Expense" value={formatCurrency(metrics.totalExpense)} trend={metrics.trends.expenseTrend} icon={TrendingDown} color="red" />
          <MetricCard title="Net Savings" value={formatCurrency(metrics.netSavings)} trend={metrics.trends.savingsTrend} icon={PiggyBank} color="green" />
        </section>

        <section className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard title="Burn Rate" value={formatCurrency(metrics.burnRate)} suffix="/ day" trend={metrics.trends.expenseTrend} icon={Flame} color="red" compact />
          <MetricCard title="Savings Growth" value={`+${metrics.savingsGrowth}%`} suffix="MoM" trend={metrics.trends.savingsTrend} icon={TrendingUp} color="purple" compact />
          <MetricCard title="Lifestyle Inflation" value={`+${metrics.lifestyleInflation}%`} suffix="vs LY" trend={metrics.trends.expenseTrend * -1} icon={WalletMinimal} color="red" compact />
          <MetricCard title="Runway" value={`${metrics.runwayMonths}`} suffix="Months" trend={metrics.trends.balanceTrend} icon={CalendarClock} color="blue" compact />
        </section>

        <section className="grid grid-cols-12 gap-8">
          <div className="col-span-12 space-y-8 lg:col-span-8">
            <BudgetingPanel
              key={`${budgeting.global.monthly_budget}-${budgeting.global.weekly_budget}-${budgeting.categories.map((item) => `${item.name}:${item.allocated_amount}:${item.frequency}`).join("|")}`}
              categories={categoryBreakdown}
              budgetSnapshot={budgeting}
            />

            <ForecastChart />

            <SmartAdvice metrics={metrics} budgetFeedback={budgeting.feedback} goalSuggestion={goalSuggestion} />

            <div className="grid grid-cols-1 gap-8 xl:grid-cols-[minmax(0,0.9fr)_260px]">
              <CategoryChart dataOverride={categoryBreakdown} />
              <BillReminders />
            </div>

            <TransactionHistory dataOverride={recentTransactions} />

            <RecurringFinancePanel subscriptions={subscriptions} emiSummary={emi} />

            <div className="grid grid-cols-1 gap-8 xl:grid-cols-2">
              <CashFlowTimeline data={cashflow} />
              <ExpenseSplitCard data={expenseSplit} />
            </div>
          </div>

          <div className="col-span-12 space-y-8 lg:col-span-4">
            <HealthScoreCard score={metrics.healthScore} savingsRatio={metrics.savingsRatio} creditScore={metrics.creditScore} />
            <NetWorthCard data={networth} />
            <AlertsPanel />
            <PriorityPanel items={priorities} />
            <GoalTracker suggestion={goalSuggestion} />
          </div>
        </section>
      </div>

      <AIChatbot metrics={metrics} floating />
    </div>
  );
}
