"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Filter, Plus } from "lucide-react";
import { apiClient, type TransactionCreatePayload, type TransactionItem } from "@/lib/api-client";

const categoryOptions = ["Food", "Transport", "Shopping", "Entertainment", "Health", "Housing", "Income", "Other"];

const initialForm: TransactionCreatePayload = {
  date: new Date().toISOString().slice(0, 10),
  merchant: "",
  category: "Other",
  amount: 0,
};

export default function TransactionsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("All");
  const [allTransactions, setAllTransactions] = useState<TransactionItem[]>([]);
  const [form, setForm] = useState<TransactionCreatePayload>(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  async function loadTransactions() {
    try {
      const res = await apiClient.getDashboardData();
      setAllTransactions(res.data.allTransactions);
    } catch (error) {
      console.error(error);
      setAllTransactions([]);
    }
  }

  useEffect(() => {
    loadTransactions();
  }, []);

  const filtered = allTransactions.filter((t) => {
    const matchesSearch = t.merchant.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === "All" || (filterType === "Income" && t.type === "income") || (filterType === "Expense" && t.type === "expense");
    return matchesSearch && matchesType;
  });

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");

    try {
      await apiClient.addTransaction({
        ...form,
        amount: Number(form.amount),
      });
      await loadTransactions();
      setForm(initialForm);
      setMessage("Transaction added successfully.");
    } catch (error) {
      console.error(error);
      setMessage(error instanceof Error ? error.message : "Failed to add transaction.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Transactions</h1>
        <Link href="/upload" className="flex items-center gap-2 bg-[#1A2035] hover:bg-[#2A324A] text-white px-4 py-2 rounded-xl transition-colors border border-[#2A324A]">
          Import Statement
        </Link>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.9fr)] gap-6">
        <div className="glass-card p-6">
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search transactions..."
                className="w-full bg-[#1A2035] border border-[#2A324A] text-white text-sm rounded-xl pl-10 pr-4 py-2.5 outline-none focus:border-[#8B5CF6] transition-colors"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className="flex gap-2 flex-wrap">
              {["All", "Income", "Expense"].map((type) => (
                <button
                  key={type}
                  onClick={() => setFilterType(type)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors border ${
                    filterType === type ? "bg-[#8B5CF6] text-white border-[#8B5CF6]" : "bg-[#1A2035] text-gray-400 border-[#2A324A] hover:text-white"
                  }`}
                >
                  {type}
                </button>
              ))}
              <Link href="/budget" className="flex items-center gap-2 px-4 py-2 bg-[#1A2035] border border-[#2A324A] text-gray-400 hover:text-white rounded-xl text-sm transition-colors">
                <Filter className="w-4 h-4" /> Budget
              </Link>
            </div>
          </div>

          <div className="w-full overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-400">
              <thead className="text-xs uppercase bg-[#1A2035]/50 font-semibold border-b border-white/5">
                <tr>
                  <th className="px-4 py-4 rounded-tl-lg">Date</th>
                  <th className="px-4 py-4">Merchant</th>
                  <th className="px-4 py-4">Category</th>
                  <th className="px-4 py-4 text-right rounded-tr-lg">Amount</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((tx, index) => (
                  <tr key={`${tx.id ?? index}-${tx.merchant}`} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-4 py-4">{tx.date}</td>
                    <td className="px-4 py-4 font-bold text-white">{tx.merchant}</td>
                    <td className="px-4 py-4">
                      <span className="bg-[#1A2035] text-xs px-2.5 py-1 rounded-md border border-[#2A324A]">{tx.category}</span>
                    </td>
                    <td className={`px-4 py-4 text-right font-bold ${tx.type === "income" ? "text-emerald-400" : "text-white"}`}>
                      {tx.type === "income" ? "+" : "-"} Rs. {Math.abs(tx.amount).toLocaleString()}
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                      No transactions found yet. <Link href="/upload" className="text-[#8B5CF6]">Upload a statement</Link>.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="glass-card p-6 flex flex-col gap-4 h-fit">
          <div className="flex items-center gap-2">
            <Plus className="w-5 h-5 text-[#8B5CF6]" />
            <h2 className="text-xl font-bold text-white">Add New Transaction</h2>
          </div>

          <label className="text-sm text-gray-400">
            Date
            <input
              type="date"
              value={form.date}
              onChange={(e) => setForm((prev) => ({ ...prev, date: e.target.value }))}
              className="mt-2 w-full bg-[#1A2035] border border-[#2A324A] text-white rounded-xl px-4 py-2.5 outline-none focus:border-[#8B5CF6]"
            />
          </label>

          <label className="text-sm text-gray-400">
            Merchant / Description
            <input
              type="text"
              value={form.merchant}
              onChange={(e) => setForm((prev) => ({ ...prev, merchant: e.target.value }))}
              className="mt-2 w-full bg-[#1A2035] border border-[#2A324A] text-white rounded-xl px-4 py-2.5 outline-none focus:border-[#8B5CF6]"
              placeholder="Enter merchant name"
              required
            />
          </label>

          <label className="text-sm text-gray-400">
            Category
            <select
              value={form.category}
              onChange={(e) => setForm((prev) => ({ ...prev, category: e.target.value }))}
              className="mt-2 w-full bg-[#1A2035] border border-[#2A324A] text-white rounded-xl px-4 py-2.5 outline-none focus:border-[#8B5CF6]"
            >
              {categoryOptions.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-gray-400">
            Amount
            <input
              type="number"
              step="0.01"
              value={form.amount}
              onChange={(e) => setForm((prev) => ({ ...prev, amount: Number(e.target.value) }))}
              className="mt-2 w-full bg-[#1A2035] border border-[#2A324A] text-white rounded-xl px-4 py-2.5 outline-none focus:border-[#8B5CF6]"
              placeholder="Use negative for expense, positive for income"
              required
            />
          </label>

          {message ? <p className="text-sm text-gray-300">{message}</p> : null}

          <button
            type="submit"
            disabled={submitting}
            className="mt-2 rounded-xl bg-[#8B5CF6] px-4 py-3 font-bold text-white transition-all hover:bg-[#A78BFA] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Saving..." : "Add Transaction"}
          </button>
        </form>
      </div>
    </div>
  );
}
