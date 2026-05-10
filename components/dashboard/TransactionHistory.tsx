"use client";

import { CarFront, Search, ShoppingBag, UtensilsCrossed } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { type TransactionItem } from "@/lib/api-client";
import { useFinance } from "@/context/FinanceContext";
import { formatDateTime } from "@/lib/mock-bank-sync";

const defaultTransactions = [
  {
    id: 1,
    merchant: "Artisan Kitchen & Bakery",
    category: "Food & Dining",
    date: "2024-03-24",
    amount: -1240.0,
    type: "expense",
    language: "Reference: #88219",
  },
];

function formatDisplayDate(value: string) {
  if (/^\d{4}-\d{2}-\d{2}\s{3}\d{2}:\d{2}$/.test(value)) {
    return value;
  }
  return formatDateTime(value);
}

function iconForCategory(category: string) {
  const value = category.toLowerCase();
  if (value.includes("food")) return { Icon: UtensilsCrossed, tone: "text-[#a88cfb] bg-[#10182E]" };
  if (value.includes("shop")) return { Icon: ShoppingBag, tone: "text-[#A897FF] bg-[#10182E]" };
  return { Icon: CarFront, tone: "text-[#ffa5d9] bg-[#10182E]" };
}

function pillTone(category: string) {
  const value = category.toLowerCase();
  if (value.includes("food")) return "bg-[#a88cfb]/10 text-[#a88cfb]";
  if (value.includes("shop")) return "bg-[#A897FF]/10 text-[#A897FF]";
  return "bg-[#ffa5d9]/10 text-[#ffa5d9]";
}

export default function TransactionHistory({ dataOverride }: { dataOverride?: TransactionItem[] }) {
  const { transactions } = useFinance();
  const [liveTransactions, setLiveTransactions] = useState<TransactionItem[] | null>(null);
  const txs = useMemo(
    () => liveTransactions ?? (transactions.length > 0 ? transactions : dataOverride && dataOverride.length > 0 ? dataOverride : defaultTransactions),
    [dataOverride, liveTransactions, transactions],
  );

  useEffect(() => {
    function handleRealtimeUpdate(event: Event) {
      const detail = (event as CustomEvent).detail;
      const allTransactions = detail?.data?.allTransactions;
      if (Array.isArray(allTransactions) && allTransactions.length > 0) {
        setLiveTransactions(allTransactions);
      }
    }

    window.addEventListener("smartspend:ws-update", handleRealtimeUpdate);
    return () => window.removeEventListener("smartspend:ws-update", handleRealtimeUpdate);
  }, []);

  return (
    <div className="glass-card flex flex-col overflow-hidden rounded-[2rem]">
      <div className="shrink-0 flex items-center justify-between p-8">
        <h3 className="text-lg font-bold text-[#F4F6FF]">Transaction History</h3>

        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#B7BDD9]" />
            <input
              type="text"
              placeholder="Filter descriptions..."
              className="rounded-full border-none bg-[#10182E] py-1.5 pl-8 pr-4 text-xs text-[#F4F6FF] outline-none focus:ring-1 focus:ring-[#A897FF]/50"
            />
          </div>
          <Link href="/transactions" className="text-sm font-semibold text-[#A897FF]">
            View All
          </Link>
        </div>
      </div>

      <div className="flex-1 min-h-0 max-h-[280px] overflow-y-auto custom-scrollbar">
        <table className="w-full border-collapse text-left">
          <thead className="bg-[#10182E]/50 text-[10px] uppercase tracking-widest text-[#B7BDD9]">
            <tr>
              <th className="px-8 py-4">Description</th>
              <th className="px-8 py-4">Category</th>
              <th className="px-8 py-4">Date</th>
              <th className="px-8 py-4 text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[rgba(255,255,255,0.05)]/10">
            {txs.map((tx, index) => {
              const { Icon, tone } = iconForCategory(tx.category);
              const value = Math.abs(Number(tx.amount || 0));
              const isExpense = tx.type === "expense" || Number(tx.amount) < 0;
              const amountClass = isExpense ? "text-rose-300" : "text-emerald-300";
              return (
                <tr key={tx.id ?? `${tx.merchant}-${index}`} className="group transition-all hover:bg-[#10182E]/30">
                  <td className="px-8 py-5">
                    <div className="flex items-center gap-3">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-full ${tone}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-[#F4F6FF]">{tx.merchant}</p>
                        <p className="text-[10px] text-[#B7BDD9]">{tx.language || "Statement import"}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-5">
                    <span className={`rounded-full px-3 py-1 text-[10px] font-bold ${pillTone(tx.category)}`}>{tx.category}</span>
                  </td>
                  <td className="px-8 py-5 text-sm text-[#B7BDD9]">{formatDisplayDate(tx.date)}</td>
                  <td className={`px-8 py-5 text-right font-bold ${amountClass}`}>
                    {formatCurrency(value)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatCurrency(value: number) {
  return `Rs${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
