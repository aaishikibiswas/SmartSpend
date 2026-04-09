"use client";

import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, X, Zap } from "lucide-react";
import { apiClient, type BillItem } from "@/lib/api-client";

type FormState = {
  name: string;
  amount: string;
  due: string;
};

const INITIAL_FORM: FormState = {
  name: "",
  amount: "",
  due: "",
};

function sortBills(items: BillItem[]) {
  return [...items].sort((left, right) => left.id - right.id);
}

export default function BillReminders() {
  const router = useRouter();
  const [bills, setBills] = useState<BillItem[]>([]);
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [removingId, setRemovingId] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const res = await apiClient.getBills();
        setBills(sortBills(res.data));
      } catch (loadError) {
        console.error(loadError);
        setBills([]);
      }
    }

    load();
  }, []);

  useEffect(() => {
    const handleUpdate = (event: Event) => {
      const detail = (event as CustomEvent).detail as { data?: { bills?: BillItem[] } } | undefined;
      const nextBills = detail?.data?.bills;
      if (Array.isArray(nextBills)) {
        setBills(sortBills(nextBills));
      }
    };

    window.addEventListener("smartspend:ws-update", handleUpdate as EventListener);
    return () => window.removeEventListener("smartspend:ws-update", handleUpdate as EventListener);
  }, []);

  const actionLabel = useMemo(() => `${bills.length} Action Items`, [bills.length]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const name = form.name.trim();
    const due = form.due.trim();
    const amount = Number(form.amount);

    if (!name || !due || !Number.isFinite(amount) || amount <= 0) {
      setError("Enter a bill name, due note, and a valid amount.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await apiClient.addBill({
        name,
        due,
        amount,
        icon: "Zap",
        color: amount >= 5000 ? "red" : "blue",
      });

      setBills((current) => sortBills([...current, response.data]));
      setForm(INITIAL_FORM);
      router.refresh();
    } catch (submitError) {
      console.error(submitError);
      setError(submitError instanceof Error ? submitError.message : "Unable to add bill right now.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleRemoveBill(identifier: number) {
    setError("");
    setRemovingId(identifier);
    try {
      await apiClient.deleteBill(identifier);
      setBills((current) => current.filter((bill) => bill.id !== identifier));
      router.refresh();
    } catch (removeError) {
      console.error(removeError);
      setError(removeError instanceof Error ? removeError.message : "Unable to remove bill right now.");
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <div className="glass-card panel-shell flex min-h-[250px] flex-col items-stretch p-5">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D8AB5]">Action Queue</p>
          <h3 className="mt-1.5 text-[15px] font-bold text-white">Bill Reminders</h3>
        </div>
        <span className="rounded-md bg-rose-500/10 px-2 py-1 text-[10px] font-semibold text-rose-400">{actionLabel}</span>
      </div>

      <form onSubmit={handleSubmit} className="mb-4 grid grid-cols-[minmax(0,1.2fr)_110px_110px_44px] gap-2">
        <input
          value={form.name}
          onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
          placeholder="Bill name"
          className="h-10 rounded-xl border border-white/8 bg-white/5 px-3 text-[12px] text-white outline-none placeholder:text-[#6D769B] focus:border-violet-400/60"
        />
        <input
          value={form.amount}
          onChange={(event) => setForm((current) => ({ ...current, amount: event.target.value }))}
          placeholder="Amount"
          inputMode="decimal"
          className="h-10 rounded-xl border border-white/8 bg-white/5 px-3 text-[12px] text-white outline-none placeholder:text-[#6D769B] focus:border-violet-400/60"
        />
        <input
          value={form.due}
          onChange={(event) => setForm((current) => ({ ...current, due: event.target.value }))}
          placeholder="Due in 3 days"
          className="h-10 rounded-xl border border-white/8 bg-white/5 px-3 text-[12px] text-white outline-none placeholder:text-[#6D769B] focus:border-violet-400/60"
        />
        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex h-10 items-center justify-center rounded-xl bg-[#7B6CF6] text-white transition hover:bg-[#8B7DFF] disabled:cursor-not-allowed disabled:opacity-60"
          aria-label="Add bill reminder"
        >
          <Plus className="h-4 w-4" />
        </button>
      </form>

      {error ? <p className="mb-3 text-[11px] font-medium text-rose-300">{error}</p> : null}

      <div className="flex flex-col gap-3">
        {bills.map((bill) => (
          <div key={bill.id} className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 p-3 transition-colors hover:bg-white/10">
            <div className="flex items-center gap-3">
              <div className={`rounded-lg bg-white/5 p-2 ${bill.color === "red" ? "text-red-400" : "text-blue-400"}`}>
                <Zap className="h-4 w-4" />
              </div>
              <div>
                <p className="text-[13px] font-bold text-white">{bill.name}</p>
                <p className={`text-[11px] ${bill.color === "red" ? "font-semibold text-rose-400" : "text-gray-400"}`}>{bill.due}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <p className="text-[13px] font-bold text-white">Rs. {bill.amount}</p>
              <button
                type="button"
                onClick={() => void handleRemoveBill(bill.id)}
                disabled={removingId === bill.id}
                className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/8 bg-white/5 text-[#9da8cb] transition hover:border-rose-400/50 hover:text-rose-300 disabled:cursor-not-allowed disabled:opacity-50"
                aria-label={`Remove ${bill.name}`}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
