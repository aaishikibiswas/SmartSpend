"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { apiClient, type CategoryBreakdownItem, type DashboardMetrics, type GoalItem, type TransactionItem } from "@/lib/api-client";
import { calculateLiveScores, calculateScoreInputs, sortTransactionsByLatest } from "@/lib/financial-scoring";
import { generateFakeTransaction } from "@/lib/mock-bank-sync";

type DashboardSnapshot = {
  metrics: DashboardMetrics;
  categoryBreakdown: CategoryBreakdownItem[];
  recentTransactions: TransactionItem[];
  allTransactions?: TransactionItem[];
};

type FinanceContextValue = {
  transactions: TransactionItem[];
  goals: GoalItem[];
  dashboardSnapshot: DashboardSnapshot | null;
  syncOn: boolean;
  setSyncOn: React.Dispatch<React.SetStateAction<boolean>>;
  financialPersonality: string;
  registerDashboardSnapshot: (snapshot: DashboardSnapshot) => void;
  appendUploadedTransaction: (tx: TransactionItem) => void;
  appendGoal: (goal: GoalItem) => void;
};

const FinanceContext = createContext<FinanceContextValue | null>(null);
const STORAGE_KEY = "smartspend-sync-on";

function randomIntervalMs() {
  return 10000 + Math.floor(Math.random() * 5000);
}

function toTime(value: string | Date | undefined) {
  if (!value) return 0;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? 0 : d.getTime();
}

function sortByLatest(items: TransactionItem[]) {
  return sortTransactionsByLatest(items);
}

function mergeCategoryBreakdown(transactions: TransactionItem[], fallback: CategoryBreakdownItem[]) {
  const totals = new Map<string, number>();
  for (const tx of transactions) {
    if (tx.amount < 0) {
      totals.set(tx.category, (totals.get(tx.category) || 0) + Math.abs(tx.amount));
    }
  }
  const merged = Array.from(totals.entries())
    .map(([name, amount]) => ({ name, amount }))
    .sort((a, b) => b.amount - a.amount);
  return merged.length > 0 ? merged.slice(0, 6) : fallback.slice(0, 6);
}

function updateMetrics(current: DashboardMetrics, tx: TransactionItem, liveTransactions: TransactionItem[]): DashboardMetrics {
  const value = Math.abs(Number(tx.amount) || 0);
  const nextIncome = tx.type === "income" || tx.amount >= 0 ? current.totalIncome + value : current.totalIncome;
  const nextExpense = tx.type === "expense" || tx.amount < 0 ? current.totalExpense + value : current.totalExpense;
  const nextBalance = tx.amount >= 0 ? current.totalBalance + value : current.totalBalance - value;
  const nextSavings = nextIncome - nextExpense;
  const budgetUsagePercent = current.budgetUsagePercent || (current.totalExpense > 0 ? (nextExpense / current.totalExpense) * 100 : 0);
  const scoringInputs = calculateScoreInputs(liveTransactions, budgetUsagePercent);
  const scores = calculateLiveScores(scoringInputs);

  return {
    ...current,
    totalIncome: Number(nextIncome.toFixed(2)),
    totalExpense: Number(nextExpense.toFixed(2)),
    totalBalance: Number(nextBalance.toFixed(2)),
    netSavings: Number(nextSavings.toFixed(2)),
    savingsRatio: nextIncome > 0 ? Number(((nextSavings / nextIncome) * 100).toFixed(2)) : current.savingsRatio,
    volatility: scoringInputs.volatility,
    healthScore: scores.healthScore,
    creditScore: scores.creditScore,
  };
}

export function FinanceProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const syncStorageKey = `${STORAGE_KEY}:${user?.id ?? "anonymous"}`;
  const [syncOn, setSyncOn] = useState(false);
  const [uploadedTransactions, setUploadedTransactions] = useState<TransactionItem[]>([]);
  const [mockTransactions, setMockTransactions] = useState<TransactionItem[]>([]);
  const [goals, setGoals] = useState<GoalItem[]>([]);
  const [dashboardSnapshot, setDashboardSnapshot] = useState<DashboardSnapshot | null>(null);
  const latestTimeRef = useRef<Date | null>(null);
  const persistInFlightRef = useRef(false);

  const transactions = useMemo(() => sortByLatest([...mockTransactions, ...uploadedTransactions]), [mockTransactions, uploadedTransactions]);

  useEffect(() => {
    window.localStorage.removeItem(STORAGE_KEY);
    const stored = window.localStorage.getItem(syncStorageKey);
    if (stored === "1") {
      setSyncOn(true);
    }
  }, [syncStorageKey]);

  useEffect(() => {
    window.localStorage.setItem(syncStorageKey, syncOn ? "1" : "0");
  }, [syncOn, syncStorageKey]);

  useEffect(() => {
    let cancelled = false;
    async function loadInitial() {
      try {
        const res = await fetch("/api/dashboard", { cache: "no-store" });
        const payload = await res.json().catch(() => null);
        const allTx = payload?.data?.allTransactions;
        if (!cancelled && Array.isArray(allTx)) {
          setUploadedTransactions(sortByLatest(allTx));
        }
      } catch {
        // no-op; app already handles local fallbacks
      }
    }
    void loadInitial();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadGoals() {
      try {
        const res = await apiClient.getGoals();
        if (!cancelled) {
          setGoals(res.data);
        }
      } catch {
        if (!cancelled) {
          setGoals([]);
        }
      }
    }
    void loadGoals();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!syncOn) return;
    let cancelled = false;
    let timer: number | null = null;

    const tick = () => {
      if (cancelled) return;
      const base = latestTimeRef.current || new Date(Math.max(toTime(transactions[0]?.rawDate || transactions[0]?.date), Date.now()));
      const tx = generateFakeTransaction(base);
      latestTimeRef.current = new Date(tx.rawDate);
      if (!persistInFlightRef.current) {
        persistInFlightRef.current = true;
        void apiClient.addTransaction({
          ...tx,
          rawDate: tx.rawDate.toISOString(),
        })
          .catch((error) => {
            console.error("Mock bank sync failed to persist transaction", error);
          })
          .finally(() => {
            persistInFlightRef.current = false;
          });
      }

      const liveTransactions = sortByLatest([tx, ...transactions]);
      setMockTransactions((prev) => sortByLatest([tx, ...prev]));

      if (dashboardSnapshot) {
        const recentTransactions = sortByLatest([tx, ...dashboardSnapshot.recentTransactions]).slice(0, 3);
        const categoryBreakdown = mergeCategoryBreakdown(liveTransactions.slice(0, 24), dashboardSnapshot.categoryBreakdown);
        const metrics = updateMetrics(dashboardSnapshot.metrics, tx, liveTransactions);
        setDashboardSnapshot({
          ...dashboardSnapshot,
          recentTransactions,
          categoryBreakdown,
          metrics,
        });

        window.setTimeout(() => {
          window.dispatchEvent(
            new CustomEvent("smartspend:ws-update", {
              detail: {
                type: "new_transaction",
                data: { recentTransactions, categoryBreakdown, metrics },
              },
            }),
          );
        }, 0);
      }

      timer = window.setTimeout(tick, randomIntervalMs());
    };

    timer = window.setTimeout(tick, randomIntervalMs());
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [syncOn, dashboardSnapshot, transactions]);

  const registerDashboardSnapshot = useCallback((snapshot: DashboardSnapshot) => {
    setDashboardSnapshot(snapshot);
    if (snapshot.allTransactions && snapshot.allTransactions.length > 0) {
      setUploadedTransactions(sortByLatest(snapshot.allTransactions));
    }
    const latest = sortByLatest(snapshot.allTransactions || snapshot.recentTransactions || [])[0];
    if (latest) {
      latestTimeRef.current = new Date(latest.rawDate || latest.date);
    }
  }, []);

  const appendUploadedTransaction = useCallback((tx: TransactionItem) => {
    setUploadedTransactions((prev) => sortByLatest([tx, ...prev]));
  }, []);

  const appendGoal = useCallback((goal: GoalItem) => {
    setGoals((current) => [goal, ...current]);
  }, []);

  const financialPersonality = dashboardSnapshot?.metrics?.financialPersonality || "Balanced";

  const value = useMemo<FinanceContextValue>(
    () => ({
      transactions,
      goals,
      dashboardSnapshot,
      syncOn,
      setSyncOn,
      financialPersonality,
      registerDashboardSnapshot,
      appendUploadedTransaction,
      appendGoal,
    }),
    [transactions, goals, dashboardSnapshot, syncOn, financialPersonality, registerDashboardSnapshot, appendUploadedTransaction, appendGoal],
  );

  return <FinanceContext.Provider value={value}>{children}</FinanceContext.Provider>;
}

export function useFinance() {
  const ctx = useContext(FinanceContext);
  if (!ctx) throw new Error("useFinance must be used within FinanceProvider");
  return ctx;
}
