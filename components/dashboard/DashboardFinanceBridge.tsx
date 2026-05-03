"use client";

import { useEffect } from "react";
import type { CategoryBreakdownItem, DashboardMetrics, TransactionItem } from "@/lib/api-client";
import { useFinance } from "@/context/FinanceContext";

export default function DashboardFinanceBridge({
  metrics,
  categoryBreakdown,
  recentTransactions,
  allTransactions,
}: {
  metrics: DashboardMetrics;
  categoryBreakdown: CategoryBreakdownItem[];
  recentTransactions: TransactionItem[];
  allTransactions: TransactionItem[];
}) {
  const { registerDashboardSnapshot } = useFinance();

  useEffect(() => {
    registerDashboardSnapshot({
      metrics,
      categoryBreakdown,
      recentTransactions,
      allTransactions,
    });
  }, [registerDashboardSnapshot, metrics, categoryBreakdown, recentTransactions, allTransactions]);

  return null;
}
