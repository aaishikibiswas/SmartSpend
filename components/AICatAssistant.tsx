"use client";

import Image from "next/image";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { useFinance } from "@/context/FinanceContext";
import { usePathname } from "next/navigation";
import { apiClient, type DashboardData, type TransactionItem } from "@/lib/api-client";

function currency(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Math.round(Number(value || 0)));
}

function greetingForHour(hour: number) {
  if (hour < 5) return "Good night";
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  if (hour < 22) return "Good evening";
  return "Good night";
}

function topExpenseCategory(transactions: TransactionItem[]) {
  const totals = new Map<string, number>();
  for (const tx of transactions) {
    const amount = Number(tx.amount || 0);
    if (tx.type !== "expense" && amount >= 0) continue;
    const category = tx.category || "Other";
    totals.set(category, (totals.get(category) || 0) + Math.abs(amount));
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

function buildInsights(data: DashboardData | null, transactions: TransactionItem[]) {
  const messages: string[] = [];
  const tx = transactions.length ? transactions : data?.allTransactions || data?.recentTransactions || [];
  const metrics = data?.metrics;
  const budget = data?.budgeting?.global;

  if (!tx.length || !metrics || !budget) {
    return ["Upload a statement to reveal budget pressure, anomalies, and savings drift."];
  }

  // 1. Savings & Spend Trends
  const currentWeek = weekSpend(tx, 0);
  const previousWeek = weekSpend(tx, 7);
  if (previousWeek > 0) {
    const change = Math.round(((currentWeek - previousWeek) / previousWeek) * 100);
    if (change < -5) messages.push(`You've saved more this week compared to last week ✨`);
    else if (change > 5) messages.push(`Shopping expenses are slightly above your usual trend.`);
  }

  if (metrics.netSavings > 0) {
    messages.push(`Your net savings are looking strong this cycle ✨`);
  }

  // 2. Budget Awareness
  if (budget.remaining_amount >= 0) {
    messages.push(`Your dining expenses stayed within budget today ✨`);
  } else {
    messages.push(`Budget pressure detected: spending is slightly above plan.`);
  }

  // 3. Category Insights
  const topCategory = topExpenseCategory(tx);
  if (topCategory) {
    if (topCategory[0] === "Food" || topCategory[0] === "Entertainment") {
      messages.push(`Your ${topCategory[0].toLowerCase()} spending is well-managed this week.`);
    } else {
      messages.push(`Your largest spend signal is currently in ${topCategory[0]}.`);
    }
  }

  // 4. Liability & Subscriptions
  const subscriptionLoad = data?.subscriptions?.reduce((sum, item) => sum + Number(item.monthly_cost || 0), 0) || metrics.subscriptionLoad || 0;
  if (subscriptionLoad > 0) {
    messages.push(`Your subscription load looks manageable this week.`);
  }

  const emiLoad = data?.emi?.monthly_load || metrics.monthlyEmiLoad || 0;
  if (emiLoad > 0 && metrics.totalIncome > 0) {
    messages.push(`Cash flow looks stable for upcoming EMI payments.`);
  }

  // 5. Anomaly & Health
  const metricSignals = metrics as typeof metrics & { anomalyCount?: number };
  const anomalyCount = Number(metricSignals.anomalyCount || 0);
  if (anomalyCount === 0) {
    messages.push(`No unusual expense patterns detected in your account data ✨`);
  }

  if (metrics.healthScore && metrics.healthScore > 80) {
    messages.push(`Financial health score is excellent. I'm monitoring drift for you.`);
  }

  return [...new Set(messages)].slice(0, 10);
}

export default function AICatAssistant() {
  const pathname = usePathname();
  const isDashboard = pathname === "/" || pathname === "/dashboard" || pathname === "/dashboard/";
  
  const { user } = useAuth();
  const { transactions, dashboardSnapshot } = useFinance();

  const [activeIndex, setActiveIndex] = useState(0);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [now, setNow] = useState<Date>(new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const firstName = user?.full_name?.split(" ")[0] || "Aaishiki";
  const greeting = `${greetingForHour(now.getHours())}, ${firstName} ✨`;
  
  const dateStr = useMemo(() => {
    return now.toLocaleDateString("en-GB", {
      weekday: "long",
      day: "numeric",
      month: "short",
    }).replace(/,/, " •");
  }, [now]);

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
      ...dashboardSnapshot,
      metrics: dashboardSnapshot.metrics,
      allTransactions: dashboardSnapshot.allTransactions || dashboardData.allTransactions,
    };
  }, [dashboardData, dashboardSnapshot]);

  const insights = useMemo(() => buildInsights(mergedData, transactions), [mergedData, transactions]);

  useEffect(() => {
    if (insights.length <= 1) return;
    const timer = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % insights.length);
    }, 5500);
    return () => window.clearInterval(timer);
  }, [insights]);

  if (!isDashboard) return null;

  return (
    <div className="ai-cat-assistant relative flex min-h-[154px] w-full max-w-[750px] items-center gap-6 overflow-visible pb-4">
      <motion.div
        className="ai-cat-avatar relative h-[148px] w-[148px] shrink-0"
        animate={{ y: [0, -7, 0], rotate: [0, 1.2, -0.9, 0] }}
        transition={{ duration: 5.8, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="ai-cat-aura absolute inset-[-24px] rounded-[38px]" />
        <div className="ai-cat-frame relative h-full w-full overflow-hidden rounded-[30px]">
          <Image
            src="/strict-neon-kitten.jpg"
            alt="SmartSpend AI companion"
            fill
            sizes="148px"
            className="scale-[1.18] object-contain object-center p-3"
            priority
          />
          <div className="ai-cat-shimmer absolute inset-0" />
        </div>
      </motion.div>

      <motion.div
        className="ai-insight-cloud relative min-h-[120px] w-[420px] px-9 py-7"
        animate={{ y: [0, -4, 0] }}
        transition={{ duration: 6.2, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="ai-cloud-tail" />
        <div className="mb-2.5 flex items-center justify-between">
          <p className="text-[20px] font-extrabold leading-tight tracking-[-0.01em] text-[#F2FBFF]">{greeting}</p>
          <span className="text-[10px] font-bold tracking-widest text-[#66E6FF]/50">{dateStr}</span>
        </div>

        <AnimatePresence mode="wait">
          <motion.p
            key={`${activeIndex}-${insights[activeIndex]}`}
            initial={{ opacity: 0, y: 8, filter: "blur(6px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -8, filter: "blur(6px)" }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="line-clamp-2 text-[15px] font-medium leading-snug text-[#DCEBFF]"
          >
            {insights[activeIndex] || "I'm monitoring your financial signals for fresh insights ✨"}
          </motion.p>
        </AnimatePresence>

        <div className="ai-carousel-bars absolute -bottom-5 left-1/2 flex -translate-x-1/2 gap-2.5">
          {insights.slice(0, 4).map((_, i) => (
            <span key={i} className={i === activeIndex % insights.slice(0, 4).length ? "is-active" : "opacity-20"} />
          ))}
        </div>
      </motion.div>
    </div>
  );
}
