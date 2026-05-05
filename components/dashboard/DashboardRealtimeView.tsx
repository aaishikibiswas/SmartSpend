"use client";

import { useMemo, useEffect, useState } from "react";
import { CalendarClock, Flame, Landmark, PiggyBank, TrendingDown, TrendingUp, WalletMinimal } from "lucide-react";
import BudgetingPanel from "@/components/dashboard/BudgetingPanel";
import SmartAdvice from "@/components/dashboard/SmartAdvice";
import BillReminders from "@/components/dashboard/BillReminders";
import dynamic from "next/dynamic";

const CategoryChart = dynamic(() => import("./CategoryChart"), {
  ssr: false,
  loading: () => <div>Loading chart...</div>
});

const ForecastChart = dynamic(() => import("./ForecastChart"), {
  ssr: false,
  loading: () => <div>Loading chart...</div>
});

import TransactionHistory from "@/components/dashboard/TransactionHistory";
import RecurringFinancePanel from "@/components/dashboard/RecurringFinancePanel";
import HealthScoreCard from "@/components/dashboard/HealthScoreCard";
import GoalTracker from "@/components/dashboard/GoalTracker";
import CashFlowTimeline from "@/components/dashboard/CashFlowTimeline";
import ExpenseSplitCard from "@/components/dashboard/ExpenseSplitCard";
import AIChatbot from "@/components/dashboard/AIChatbot";
import MetricCard from "@/components/MetricCard";
import { useFinance } from "@/context/FinanceContext";
import { formatDateTime } from "@/lib/mock-bank-sync";
import type { CashflowData, CategoryBreakdownItem, DashboardData, DashboardMetrics, ExpenseSplitData, PriorityItem, TransactionItem } from "@/lib/api-client";

function formatCurrency(value: number) {
  return `Rs${Number(value || 0).toLocaleString()}`;
}

function trendFromPair(current: number, baseline: number) {
  if (baseline === 0) return current > 0 ? 100 : 0;
  return Number((((current - baseline) / Math.abs(baseline)) * 100).toFixed(1));
}

function StatsCards({ liveMetrics }: { liveMetrics: DashboardMetrics }) {
  return (
    <>
      <section className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard title="Total Balance" value={formatCurrency(liveMetrics.totalBalance)} trend={liveMetrics.trends.balanceTrend} icon={Landmark} color="blue" />
        <MetricCard title="Monthly Income" value={formatCurrency(liveMetrics.totalIncome)} trend={liveMetrics.trends.incomeTrend} icon={TrendingUp} color="purple" />
        <MetricCard title="Monthly Expense" value={formatCurrency(liveMetrics.totalExpense)} trend={liveMetrics.trends.expenseTrend} icon={TrendingDown} color="red" />
        <MetricCard title="Net Savings" value={formatCurrency(liveMetrics.netSavings)} trend={liveMetrics.trends.savingsTrend} icon={PiggyBank} color="green" />
      </section>

      <section className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard title="Burn Rate" value={formatCurrency(liveMetrics.burnRate)} suffix="/ day" trend={liveMetrics.trends.expenseTrend} icon={Flame} color="red" compact />
        <MetricCard title="Savings Growth" value={`+${liveMetrics.savingsGrowth}%`} suffix="MoM" trend={liveMetrics.trends.savingsTrend} icon={TrendingUp} color="purple" compact />
        <MetricCard title="Lifestyle Inflation" value={`+${liveMetrics.lifestyleInflation}%`} suffix="vs LY" trend={liveMetrics.trends.expenseTrend * -1} icon={WalletMinimal} color="red" compact />
        <MetricCard title="Runway" value={`${liveMetrics.runwayMonths}`} suffix="Months" trend={liveMetrics.trends.balanceTrend} icon={CalendarClock} color="blue" compact />
      </section>
    </>
  );
}

export default function DashboardRealtimeView({ initialData }: { initialData: DashboardData }) {
  const [advisory, setAdvisory] = useState(initialData.advisory.advice);
  const { transactions } = useFinance();

  const txSource = useMemo(() => {
    if (transactions.length > 0) return transactions;
    if (Array.isArray(initialData.allTransactions) && initialData.allTransactions.length > 0) return initialData.allTransactions;
    return initialData.recentTransactions || [];
  }, [transactions, initialData.allTransactions, initialData.recentTransactions]);

  useEffect(() => {
    console.log("DashboardRealtimeView: Initializing websocket listener");
    
    function handleWsUpdate(event: Event) {
      const detail = (event as CustomEvent).detail;
      console.log("DashboardRealtimeView: Received websocket update", detail);
      
      if (detail?.type === "snapshot" && detail?.data?.advisory) {
        console.log("DashboardRealtimeView: Updating advisory from snapshot", detail.data.advisory);
        setAdvisory(detail.data.advisory.advice);
      }
    }

    window.addEventListener("smartspend:ws-update", handleWsUpdate);
    return () => window.removeEventListener("smartspend:ws-update", handleWsUpdate);
  }, [setAdvisory]);

  const monthlyTx = useMemo(() => {
    const now = new Date();
    const month = now.getMonth();
    const year = now.getFullYear();
    const currentMonthTx = txSource.filter((tx) => {
      const d = new Date(tx.rawDate || tx.date);
      return !Number.isNaN(d.getTime()) && d.getMonth() === month && d.getFullYear() === year;
    });
    // Fallback to all available transactions when the current month has no records,
    // so dashboard doesn't collapse to zero.
    return currentMonthTx.length > 0 ? currentMonthTx : txSource;
  }, [txSource]);

  const derived = useMemo(() => {
    let income = 0;
    let expense = 0;
    for (const tx of monthlyTx) {
      if (tx.type === "income") income += Number(tx.amount || 0);
      if (tx.type === "expense") expense += Math.abs(Number(tx.amount || 0));
    }
    const netSavings = income - expense;
    const totalBalance = netSavings;
    const today = Math.max(new Date().getDate(), 1);
    const burnRate = expense / today;
    const savingsRatio = income > 0 ? (netSavings / income) * 100 : 0;
    return { income, expense, netSavings, totalBalance, burnRate, savingsRatio };
  }, [monthlyTx]);

  const categoryBreakdown = useMemo<CategoryBreakdownItem[]>(() => {
    const totals = new Map<string, number>();
    for (const tx of txSource) {
      if (tx.type === "expense") {
        totals.set(tx.category, (totals.get(tx.category) || 0) + Math.abs(tx.amount));
      }
    }
    return Array.from(totals.entries())
      .map(([name, amount]) => ({ name, amount }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 6);
  }, [txSource]);

  const expenseSplit = useMemo<ExpenseSplitData>(() => {
    const fixedSet = new Set(["bills", "housing", "rent", "emi", "subscription", "utilities", "electricity", "internet", "insurance"]);
    let fixed = 0;
    let variable = 0;
    for (const tx of monthlyTx) {
      if (tx.type !== "expense") continue;
      const value = Math.abs(tx.amount);
      if (fixedSet.has(String(tx.category || "").toLowerCase())) fixed += value;
      else variable += value;
    }
    const total = fixed + variable;
    const fixedPercent = total > 0 ? Number(((fixed / total) * 100).toFixed(1)) : 0;
    const variablePercent = total > 0 ? Number(((variable / total) * 100).toFixed(1)) : 0;
    return {
      fixed_total: fixed,
      variable_total: variable,
      fixed_percent: fixedPercent,
      variable_percent: variablePercent,
      breakdown: [
        { name: "Fixed", amount: fixed },
        { name: "Variable", amount: variable },
      ],
    };
  }, [monthlyTx]);

  const priorities = useMemo<PriorityItem[]>(() => {
    const items: PriorityItem[] = [];
    if (derived.savingsRatio < 20) {
      items.push({ level: "High", title: "Increase savings ratio", message: "Current savings ratio is below 20%. Reduce non-essential spending this month." });
    }
    if (derived.burnRate > 0) {
      items.push({ level: "Medium", title: "Monitor daily burn", message: `Average burn rate is ${formatCurrency(derived.burnRate)} per day. Keep this within your budget target.` });
    }
    items.push({ level: "Low", title: "Track category spikes", message: "Review top expense categories and cap one high-leak category this week." });
    return items.slice(0, 3);
  }, [derived.savingsRatio, derived.burnRate]);

  const liveMetrics: DashboardMetrics = useMemo(
    () => ({
      ...initialData.metrics,
      totalIncome: Number(derived.income.toFixed(2)),
      totalExpense: Number(derived.expense.toFixed(2)),
      netSavings: Number(derived.netSavings.toFixed(2)),
      totalBalance: Number(derived.totalBalance.toFixed(2)),
      burnRate: Number(derived.burnRate.toFixed(2)),
      savingsRatio: Number(derived.savingsRatio.toFixed(2)),
      trends: {
        balanceTrend: trendFromPair(derived.totalBalance, initialData.metrics.totalBalance),
        incomeTrend: trendFromPair(derived.income, initialData.metrics.totalIncome),
        expenseTrend: trendFromPair(derived.expense, initialData.metrics.totalExpense),
        savingsTrend: trendFromPair(derived.netSavings, initialData.metrics.netSavings),
      },
    }),
    [initialData.metrics, derived],
  );

  const liveBudgeting = useMemo(() => {
    const monthlyBudget = Number(initialData.budgeting.global.monthly_budget || 0);
    const remainingAmount = monthlyBudget > 0 ? monthlyBudget - derived.expense : initialData.budgeting.global.remaining_amount;
    const usagePercent = monthlyBudget > 0 ? Number(((derived.expense / monthlyBudget) * 100).toFixed(2)) : initialData.budgeting.global.usage_percent;
    const today = Math.max(new Date().getDate(), 1);
    const daysLeft = Math.max(30 - today, 1);
    const spentByCategory = new Map(categoryBreakdown.map((item) => [item.name.toLowerCase(), item.amount]));

    return {
      ...initialData.budgeting,
      global: {
        ...initialData.budgeting.global,
        spent_amount: Number(derived.expense.toFixed(2)),
        remaining_amount: Number(remainingAmount.toFixed(2)),
        usage_percent: usagePercent,
        daily_allowance: Number((Math.max(remainingAmount, 0) / daysLeft).toFixed(2)),
      },
      categories: initialData.budgeting.categories.map((category) => {
        const spentAmount = Number((spentByCategory.get(category.name.toLowerCase()) || category.spent_amount || 0).toFixed(2));
        const remainingCategory = Number((category.allocated_amount - spentAmount).toFixed(2));
        const categoryUsage = category.allocated_amount > 0 ? Number(((spentAmount / category.allocated_amount) * 100).toFixed(2)) : 0;
        return {
          ...category,
          spent_amount: spentAmount,
          remaining_amount: remainingCategory,
          usage_percent: categoryUsage,
          status: categoryUsage >= 100 ? "over" : categoryUsage >= 80 ? "warning" : "ok",
        };
      }),
    };
  }, [categoryBreakdown, derived.expense, initialData.budgeting]);

  useEffect(() => {
    async function fetchSmartAdvice() {
      try {
        console.log("Smart Advice: Fetching live financial insights...");
        const response = await fetch("/api/smart-advice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            metrics: liveMetrics,
            budgeting: liveBudgeting,
            prediction: initialData.prediction,
            expenseSplit,
            behavior: {
              ...initialData.behavior,
              day_of_month: new Date().getDate(),
            },
          }),
        });

        if (!response.ok) {
          console.warn("Smart Advice: Real-time refresh skipped due to server error");
          return;
        }

        const payload = await response.json();
        if (payload.data) {
          console.log("Smart Advice: Live insights updated", payload.data);
          setAdvisory(payload.data.advice || []);
        }
      } catch (err) {
        console.error("Smart Advice: Failed to refresh advice", err);
      }
    }

    fetchSmartAdvice();
    const refreshInterval = setInterval(fetchSmartAdvice, 60000);
    return () => clearInterval(refreshInterval);
  }, [expenseSplit, initialData.behavior, initialData.prediction, liveBudgeting, liveMetrics]);

  const sortedTransactions: TransactionItem[] = useMemo(
    () => [...txSource].sort((a, b) => new Date(b.rawDate || b.date).getTime() - new Date(a.rawDate || a.date).getTime()),
    [txSource],
  );

  const budgetPanelKey = useMemo(
    () =>
      `${initialData.budgeting.global.monthly_budget}-${initialData.budgeting.global.weekly_budget}-${initialData.budgeting.categories
        .map((item) => `${item.name}:${item.allocated_amount}:${item.frequency}`)
        .join("|")}`,
    [initialData.budgeting.categories, initialData.budgeting.global.monthly_budget, initialData.budgeting.global.weekly_budget],
  );

  return (
    <>
      <div className="mx-auto w-full max-w-7xl space-y-8 px-8 py-8">
        <StatsCards liveMetrics={liveMetrics} />

        <section className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div className="space-y-8 min-w-0">
            <section id="budget-panel" className="scroll-mt-28">
              <BudgetingPanel
                key={budgetPanelKey}
                categories={categoryBreakdown}
                budgetSnapshot={liveBudgeting}
              />
            </section>

            <section id="forecast-insights" className="scroll-mt-28">
              <ForecastChart />
            </section>

            <section id="smart-advice" className="scroll-mt-28">
              <SmartAdvice adviceItems={advisory} />
            </section>

            <TransactionHistory dataOverride={sortedTransactions} />
            <section id="recurring-liabilities" className="scroll-mt-28">
              <RecurringFinancePanel subscriptions={initialData.subscriptions} emiSummary={initialData.emi} />
            </section>
          </div>

          <div className="right-column space-y-8 min-w-0 w-full">
            <section id="health-score" className="scroll-mt-28">
              <HealthScoreCard score={liveMetrics.healthScore} savingsRatio={liveMetrics.savingsRatio} creditScore={liveMetrics.creditScore} />
            </section>
            <section id="goal-tracker" className="scroll-mt-28">
              <GoalTracker suggestion={initialData.goalSuggestion} />
            </section>
            <CashFlowTimeline data={initialData.cashflow} />
            <CategoryChart dataOverride={categoryBreakdown} />
            <BillReminders />
            <ExpenseSplitCard data={expenseSplit} />
          </div>
        </section>
      </div>

      <AIChatbot
        metrics={liveMetrics}
        categoryBreakdown={categoryBreakdown}
        subscriptions={initialData.subscriptions}
        emi={initialData.emi}
        cashflow={initialData.cashflow}
        goalSuggestion={initialData.goalSuggestion}
        budgeting={liveBudgeting}
        recentTransactions={sortedTransactions}
        floating
      />
    </>
  );
}
