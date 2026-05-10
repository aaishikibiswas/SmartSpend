"use client";

import Image from "next/image";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { useFinance } from "@/context/FinanceContext";
import { apiClient, type DashboardData, type TransactionItem } from "@/lib/api-client";

function currency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Math.round(Number(value || 0)));
}

function greetingForHour(hour: number) {
  if (hour < 5) return "Still watching the numbers";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  if (hour < 22) return "Good evening";
  return "Good night";
}

function topExpenseCategory(transactions: TransactionItem[]) {
  const totals = new Map<string, number>();
  for (const tx of transactions) {
    if (tx.type !== "expense" && tx.amount >= 0) continue;
    const category = tx.category || "Other";
    totals.set(category, (totals.get(category) || 0) + Math.abs(Number(tx.amount || 0)));
  }
  return [...totals.entries()].sort((a, b) => b[1] - a[1])[0] || null;
}

function weekSpend(transactions: TransactionItem[], offsetDays: number) {
  const now = new Date();
  const end = new Date(now);
  end.setDate(now.getDate() - offsetDays);
  const start = new Date(end);
  start.setDate(end.getDate() - 7);

  return transactions.reduce((sum, tx) => {
    const date = new Date(tx.rawDate || tx.date);
    if (Number.isNaN(date.getTime()) || date < start || date > end) return sum;
    if (tx.type === "expense" || tx.amount < 0) return sum + Math.abs(Number(tx.amount || 0));
    return sum;
  }, 0);
}

function buildInsights(data: DashboardData | null, transactions: TransactionItem[], firstName: string) {
  const now = new Date();
  const greeting = `${greetingForHour(now.getHours())}, ${firstName}!`;
  const messages: string[] = [];

  const tx = transactions.length ? transactions : data?.allTransactions || data?.recentTransactions || [];
  const metrics = data?.metrics;
  const budget = data?.budgeting?.global;

  if (!tx.length || !metrics || !budget) {
    messages.push("Upload a statement and I will start tracking budget pressure, anomalies, and savings drift.");
    return { greeting, messages };
  }

  const currentWeek = weekSpend(tx, 0);
  const previousWeek = weekSpend(tx, 7);
  if (previousWeek > 0) {
    const change = Math.round(((currentWeek - previousWeek) / previousWeek) * 100);
    if (change < 0) messages.push(`You spent ${Math.abs(change)}% less than last week.`);
    if (change > 0) messages.push(`Spending is ${change}% higher than last week.`);
  }

  if (metrics.netSavings >= 0) {
    messages.push(`Net savings are holding at ${currency(metrics.netSavings)} this cycle.`);
  } else {
    messages.push(`Savings pressure detected: ${currency(Math.abs(metrics.netSavings))} below break-even.`);
  }

  if (Number.isFinite(metrics.burnRate)) {
    messages.push(`Current burn rate is ${currency(metrics.burnRate)} per day.`);
  }

  if (budget.remaining_amount >= 0) {
    messages.push(`You are under budget by ${currency(budget.remaining_amount)} this month.`);
  } else {
    messages.push(`Budget overrun detected: ${currency(Math.abs(budget.remaining_amount))} above plan.`);
  }

  const topCategory = topExpenseCategory(tx);
  if (topCategory) {
    messages.push(`${topCategory[0]} is the largest spend signal at ${currency(topCategory[1])}.`);
  }

  const metricSignals = metrics as typeof metrics & { anomalyCount?: number };
  const dataSignals = data as typeof data & { anomalySummary?: { count?: number } };
  const anomalyCount = Number(metricSignals.anomalyCount || dataSignals?.anomalySummary?.count || 0);
  if (anomalyCount > 0) {
    messages.push(`${anomalyCount} unusual expense${anomalyCount === 1 ? "" : "s"} detected in your account data.`);
  }

  if (metrics.healthScore) {
    messages.push(`Financial health score is ${Math.round(metrics.healthScore)}. I am monitoring drift in real time.`);
  }

  return { greeting, messages: [...new Set(messages)].slice(0, 8) };
}

export default function AICatAssistant() {
  const { user } = useAuth();
  const { transactions, dashboardSnapshot } = useFinance();
  const firstName = user?.full_name?.split(" ")[0] || "there";
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        const response = await apiClient.getDashboardData();
        if (!cancelled) setDashboardData(response.data);
      } catch {
        if (!cancelled) setDashboardData(null);
      }
    }

    void loadDashboard();

    const handleLiveUpdate = (event: Event) => {
      const payload = (event as CustomEvent).detail;
      if (payload?.data?.metrics) {
        setDashboardData((current) => ({
          ...current,
          ...payload.data,
        }) as DashboardData);
      }
    };

    window.addEventListener("smartspend:live-update", handleLiveUpdate);
    window.addEventListener("smartspend:ws-update", handleLiveUpdate);

    return () => {
      cancelled = true;
      window.removeEventListener("smartspend:live-update", handleLiveUpdate);
      window.removeEventListener("smartspend:ws-update", handleLiveUpdate);
    };
  }, [user?.id]);

  const mergedData = useMemo<DashboardData | null>(() => {
    if (!dashboardSnapshot || !dashboardData) return dashboardData;
    return {
      ...dashboardData,
      metrics: dashboardSnapshot.metrics,
      categoryBreakdown: dashboardSnapshot.categoryBreakdown,
      recentTransactions: dashboardSnapshot.recentTransactions,
      allTransactions: dashboardSnapshot.allTransactions || dashboardData.allTransactions,
    };
  }, [dashboardData, dashboardSnapshot]);

  const insightSet = useMemo(
    () => buildInsights(mergedData, transactions, firstName),
    [firstName, mergedData, transactions],
  );
  const insights = insightSet.messages.length ? insightSet.messages : ["I am watching your authenticated workspace for fresh financial signals."];

  useEffect(() => {
    setActiveIndex(0);
    if (insights.length <= 1) return;
    const timer = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % insights.length);
    }, 4200);
    return () => window.clearInterval(timer);
  }, [insights]);

  return (
    <div className="ai-cat-assistant relative flex min-h-[154px] w-full max-w-[720px] items-center gap-5 overflow-visible">
      <motion.div
        className="ai-cat-avatar relative h-[148px] w-[148px] shrink-0"
        animate={{ y: [0, -7, 0], rotate: [0, 1.2, -0.9, 0] }}
        transition={{ duration: 5.8, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="ai-cat-aura absolute inset-[-24px] rounded-[38px]" />
        <div className="ai-cat-frame relative h-full w-full overflow-hidden rounded-[30px]">
          <Image
            src="/ai-cat-assistant.png"
            alt="SmartSpend AI cat assistant"
            fill
            sizes="148px"
            className="scale-[1.18] object-contain object-center p-3"
            priority
          />
          <div className="ai-cat-shimmer absolute inset-0" />
        </div>
      </motion.div>

      <motion.div
        className="ai-insight-cloud relative min-h-[128px] w-[390px] min-w-[390px] px-8 py-6"
        animate={{ y: [0, -4, 0] }}
        transition={{ duration: 6.2, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="ai-cloud-tail" />
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.32em] text-[#66E6FF]/85">Live AI Insight</p>
        <p className="mb-2 text-[20px] font-extrabold leading-tight tracking-[-0.01em] text-[#F2FBFF]">{insightSet.greeting} ✨</p>
        <AnimatePresence mode="wait">
          <motion.p
            key={`${activeIndex}-${insights[activeIndex]}`}
            initial={{ opacity: 0, y: 8, filter: "blur(6px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -8, filter: "blur(6px)" }}
            transition={{ duration: 0.45, ease: "easeOut" }}
            className="line-clamp-2 text-[15px] font-medium leading-snug text-[#DCEBFF]"
          >
            {insights[activeIndex]}
          </motion.p>
        </AnimatePresence>
        <div className="ai-carousel-bars absolute -bottom-5 left-1/2 flex -translate-x-1/2 gap-2">
          {[0, 1, 2].map((item) => (
            <span key={item} className={item === activeIndex % 3 ? "is-active" : ""} />
          ))}
        </div>
      </motion.div>
    </div>
  );
}
