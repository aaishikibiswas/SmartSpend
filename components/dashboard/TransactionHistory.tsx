"use client";

import { CarFront, Search, ShoppingBag, UtensilsCrossed } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { type TransactionItem } from "@/lib/api-client";

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
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function iconForCategory(category: string) {
  const value = category.toLowerCase();
  if (value.includes("food")) return { Icon: UtensilsCrossed, tone: "text-[#a88cfb] bg-[#192540]" };
  if (value.includes("shop")) return { Icon: ShoppingBag, tone: "text-[#a3a6ff] bg-[#192540]" };
  return { Icon: CarFront, tone: "text-[#ffa5d9] bg-[#192540]" };
}

function pillTone(category: string) {
  const value = category.toLowerCase();
  if (value.includes("food")) return "bg-[#a88cfb]/10 text-[#a88cfb]";
  if (value.includes("shop")) return "bg-[#a3a6ff]/10 text-[#a3a6ff]";
  return "bg-[#ffa5d9]/10 text-[#ffa5d9]";
}

export default function TransactionHistory({ dataOverride }: { dataOverride?: TransactionItem[] }) {
  const [liveTransactions, setLiveTransactions] = useState<TransactionItem[] | null>(null);
  const txs = useMemo(
    () => liveTransactions ?? (dataOverride && dataOverride.length > 0 ? dataOverride : defaultTransactions).slice(0, 3),
    [dataOverride, liveTransactions],
  );

  useEffect(() => {
    function handleRealtimeUpdate(event: Event) {
      const detail = (event as CustomEvent).detail;
      const recentTransactions = detail?.data?.recentTransactions;
      if (Array.isArray(recentTransactions) && recentTransactions.length > 0) {
        setLiveTransactions(recentTransactions.slice(0, 3));
      }
    }

    window.addEventListener("smartspend:ws-update", handleRealtimeUpdate);
    return () => window.removeEventListener("smartspend:ws-update", handleRealtimeUpdate);
  }, []);

  return (
    <div className="glass-card overflow-hidden rounded-[2rem]">
      <div className="flex items-center justify-between p-8">
        <h3 className="text-lg font-bold text-[#dee5ff]">Transaction History</h3>

        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#a3aac4]" />
            <input
              type="text"
              placeholder="Filter descriptions..."
              className="rounded-full border-none bg-[#192540] py-1.5 pl-8 pr-4 text-xs text-[#dee5ff] outline-none focus:ring-1 focus:ring-[#a3a6ff]/50"
            />
          </div>
          <Link href="/transactions" className="text-sm font-semibold text-[#a3a6ff]">
            View All
          </Link>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead className="bg-[#091328]/50 text-[10px] uppercase tracking-widest text-[#a3aac4]">
            <tr>
              <th className="px-8 py-4">Description</th>
              <th className="px-8 py-4">Category</th>
              <th className="px-8 py-4">Date</th>
              <th className="px-8 py-4 text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#40485d]/10">
            {txs.map((tx, index) => {
              const { Icon, tone } = iconForCategory(tx.category);
              return (
                <tr key={tx.id ?? `${tx.merchant}-${index}`} className="group transition-all hover:bg-[#141f38]/30">
                  <td className="px-8 py-5">
                    <div className="flex items-center gap-3">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-full ${tone}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-[#dee5ff]">{tx.merchant}</p>
                        <p className="text-[10px] text-[#a3aac4]">{tx.language || "Statement import"}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-5">
                    <span className={`rounded-full px-3 py-1 text-[10px] font-bold ${pillTone(tx.category)}`}>{tx.category}</span>
                  </td>
                  <td className="px-8 py-5 text-sm text-[#a3aac4]">{formatDisplayDate(tx.date)}</td>
                  <td className="px-8 py-5 text-right font-bold text-[#dee5ff]">- {formatCurrency(Math.abs(tx.amount))}</td>
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
