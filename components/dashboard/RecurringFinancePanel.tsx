"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import { apiClient, type EmiItem, type EmiSummary, type SubscriptionCreatePayload, type SubscriptionItem } from "@/lib/api-client";

type EmiForm = {
  name: string;
  total_amount: string;
  monthly_emi: string;
  remaining_months: string;
  interest_rate: string;
  due_date: string;
};

const INITIAL_EMI_FORM: EmiForm = {
  name: "",
  total_amount: "",
  monthly_emi: "",
  remaining_months: "",
  interest_rate: "",
  due_date: "",
};

type SubscriptionForm = {
  name: string;
  monthly_cost: string;
  frequency: string;
  last_charge_date: string;
  next_due_date: string;
};

const INITIAL_SUBSCRIPTION_FORM: SubscriptionForm = {
  name: "",
  monthly_cost: "",
  frequency: "Monthly",
  last_charge_date: "",
  next_due_date: "",
};

export default function RecurringFinancePanel({
  subscriptions: initialSubscriptions,
  emiSummary: initialEmiSummary,
}: {
  subscriptions: SubscriptionItem[];
  emiSummary: EmiSummary;
}) {
  const [subscriptions, setSubscriptions] = useState(initialSubscriptions);
  const [emiSummary, setEmiSummary] = useState(initialEmiSummary);
  const [form, setForm] = useState<EmiForm>(INITIAL_EMI_FORM);
  const [subscriptionForm, setSubscriptionForm] = useState<SubscriptionForm>(INITIAL_SUBSCRIPTION_FORM);
  const [error, setError] = useState("");
  const [busyKey, setBusyKey] = useState("");

  useEffect(() => {
    const onUpdate = (event: Event) => {
      const detail = (event as CustomEvent).detail as {
        data?: { subscriptions?: SubscriptionItem[]; emi?: EmiSummary };
      };
      if (detail?.data?.subscriptions) {
        setSubscriptions(detail.data.subscriptions);
      }
      if (detail?.data?.emi) {
        setEmiSummary(detail.data.emi);
      }
    };
    window.addEventListener("smartspend:ws-update", onUpdate as EventListener);
    return () => window.removeEventListener("smartspend:ws-update", onUpdate as EventListener);
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      const response = await apiClient.addEmi({
        name: form.name,
        total_amount: Number(form.total_amount),
        monthly_emi: Number(form.monthly_emi),
        remaining_months: Number(form.remaining_months),
        interest_rate: Number(form.interest_rate || 0),
        due_date: form.due_date,
      });
      const nextItem = response.data as EmiItem;
      setEmiSummary((current) => ({
        items: [...current.items, nextItem],
        monthly_load: round2(current.monthly_load + Number(nextItem.monthly_emi)),
        remaining_liability: round2(current.remaining_liability + Number(nextItem.monthly_emi) * Number(nextItem.remaining_months)),
      }));
      setForm(INITIAL_EMI_FORM);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to add EMI right now.");
    }
  }

  async function handleAddSubscription(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const payload: SubscriptionCreatePayload = {
      name: subscriptionForm.name.trim(),
      monthly_cost: Number(subscriptionForm.monthly_cost),
      frequency: subscriptionForm.frequency,
      last_charge_date: subscriptionForm.last_charge_date.trim(),
      next_due_date: subscriptionForm.next_due_date.trim(),
    };

    if (!payload.name || !payload.last_charge_date || !payload.next_due_date || !Number.isFinite(payload.monthly_cost) || payload.monthly_cost <= 0) {
      setError("Enter a valid subscription name, dates, and monthly cost.");
      return;
    }

    setBusyKey("subscription-add");
    try {
      const response = await apiClient.addSubscription(payload);
      setSubscriptions((current) => {
        const next = [...current, response.data];
        return next.sort((left, right) => right.monthly_cost - left.monthly_cost);
      });
      setSubscriptionForm(INITIAL_SUBSCRIPTION_FORM);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to add subscription right now.");
    } finally {
      setBusyKey("");
    }
  }

  async function handleRemoveSubscription(name: string) {
    setError("");
    setBusyKey(`sub-${name}`);
    try {
      await apiClient.deleteSubscription(name);
      setSubscriptions((current) => current.filter((item) => item.name !== name));
    } catch (removeError) {
      setError(removeError instanceof Error ? removeError.message : "Unable to remove subscription right now.");
    } finally {
      setBusyKey("");
    }
  }

  async function handleRemoveEmi(identifier: string | number) {
    setError("");
    setBusyKey(`emi-${identifier}`);
    try {
      await apiClient.deleteEmi(identifier);
      setEmiSummary((current) => {
        const nextItems = current.items.filter((item) => String(item.id) !== String(identifier) && item.name !== String(identifier));
        return {
          items: nextItems,
          monthly_load: round2(nextItems.reduce((sum, item) => sum + Number(item.monthly_emi), 0)),
          remaining_liability: round2(nextItems.reduce((sum, item) => sum + Number(item.monthly_emi) * Number(item.remaining_months), 0)),
        };
      });
    } catch (removeError) {
      setError(removeError instanceof Error ? removeError.message : "Unable to remove EMI right now.");
    } finally {
      setBusyKey("");
    }
  }

  return (
    <section className="glass-card panel-shell rounded-[28px] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D8AB5]">Recurring Payments & Liabilities</p>
          <h3 className="mt-1.5 text-[16px] font-bold text-white">Subscriptions and EMI load</h3>
        </div>
        <div className="rounded-2xl border border-white/8 bg-white/5 px-3 py-2 text-right">
          <p className="text-[10px] uppercase tracking-[0.22em] text-[#7D8AB5]">Monthly Fixed Load</p>
          <p className="mt-1 text-sm font-bold text-[#edf2ff]">Rs. {round2(emiSummary.monthly_load + subscriptions.reduce((sum, item) => sum + item.monthly_cost, 0)).toLocaleString()}</p>
        </div>
      </div>

      <div className="mt-5 grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D8AB5]">Subscriptions</p>
          <form onSubmit={handleAddSubscription} className="grid grid-cols-2 gap-2 rounded-2xl border border-white/8 bg-white/5 p-3">
            <input value={subscriptionForm.name} onChange={(event) => setSubscriptionForm((current) => ({ ...current, name: event.target.value }))} placeholder="Subscription name" className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <input value={subscriptionForm.monthly_cost} onChange={(event) => setSubscriptionForm((current) => ({ ...current, monthly_cost: event.target.value }))} placeholder="Monthly cost" className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <select value={subscriptionForm.frequency} onChange={(event) => setSubscriptionForm((current) => ({ ...current, frequency: event.target.value }))} className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none">
              <option value="Monthly">Monthly</option>
              <option value="Weekly">Weekly</option>
            </select>
            <input value={subscriptionForm.last_charge_date} onChange={(event) => setSubscriptionForm((current) => ({ ...current, last_charge_date: event.target.value }))} placeholder="Last charge date" className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <input value={subscriptionForm.next_due_date} onChange={(event) => setSubscriptionForm((current) => ({ ...current, next_due_date: event.target.value }))} placeholder="Next due date" className="col-span-2 h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <button type="submit" disabled={busyKey === "subscription-add"} className="col-span-2 inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-[#7B6CF6] text-sm font-semibold text-white transition hover:bg-[#8B7DFF] disabled:cursor-not-allowed disabled:opacity-60">
              <Plus className="h-4 w-4" />
              Add Subscription
            </button>
          </form>
          {subscriptions.length === 0 ? <div className="rounded-2xl border border-white/8 bg-white/5 p-4 text-sm text-[#9eabc7]">No recurring subscriptions detected yet.</div> : null}
          {subscriptions.slice(0, 4).map((item) => (
            <div key={`${item.name}-${item.next_due_date}`} className="rounded-2xl border border-white/8 bg-white/5 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-[#edf2ff]">{item.name}</p>
                  <p className="mt-1 text-xs text-[#9eabc7]">{item.frequency} recurring charge {item.source === "auto" ? "(Auto-detected)" : "(Manual)"}</p>
                </div>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-bold text-[#b9b7ff]">Rs. {item.monthly_cost.toLocaleString()}</p>
                  <button
                    type="button"
                    onClick={() => void handleRemoveSubscription(item.name)}
                    disabled={busyKey === `sub-${item.name}`}
                    className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/8 bg-white/5 text-[#9da8cb] transition hover:border-rose-400/50 hover:text-rose-300 disabled:cursor-not-allowed disabled:opacity-50"
                    aria-label={`Remove ${item.name}`}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between text-[11px] text-[#8390b1]">
                <span>Last: {item.last_charge_date}</span>
                <span>Next: {item.next_due_date}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D8AB5]">EMI Management</p>
          <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-2 rounded-2xl border border-white/8 bg-white/5 p-3">
            <input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="EMI name" className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <input value={form.due_date} onChange={(event) => setForm((current) => ({ ...current, due_date: event.target.value }))} placeholder="2026-04-18" className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <input value={form.total_amount} onChange={(event) => setForm((current) => ({ ...current, total_amount: event.target.value }))} placeholder="Total amount" className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <input value={form.monthly_emi} onChange={(event) => setForm((current) => ({ ...current, monthly_emi: event.target.value }))} placeholder="Monthly EMI" className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <input value={form.remaining_months} onChange={(event) => setForm((current) => ({ ...current, remaining_months: event.target.value }))} placeholder="Remaining months" className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <input value={form.interest_rate} onChange={(event) => setForm((current) => ({ ...current, interest_rate: event.target.value }))} placeholder="Interest %" className="h-10 rounded-xl border border-white/8 bg-[#141f38] px-3 text-sm text-[#edf2ff] outline-none placeholder:text-[#6D769B]" />
            <button type="submit" className="col-span-2 h-10 rounded-xl bg-[#7B6CF6] text-sm font-semibold text-white transition hover:bg-[#8B7DFF]">Add EMI</button>
          </form>
          {error ? <p className="text-xs text-rose-300">{error}</p> : null}
          {emiSummary.items.slice(0, 4).map((item) => (
            <div key={item.id} className="rounded-2xl border border-white/8 bg-white/5 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-[#edf2ff]">{item.name}</p>
                  <p className="mt-1 text-xs text-[#9eabc7]">{item.remaining_months} months remaining {item.source === "auto" ? "(Auto-detected)" : "(Manual)"}</p>
                </div>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-bold text-[#ffcb82]">Rs. {item.monthly_emi.toLocaleString()}</p>
                  <button
                    type="button"
                    onClick={() => void handleRemoveEmi(item.id)}
                    disabled={busyKey === `emi-${item.id}`}
                    className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/8 bg-white/5 text-[#9da8cb] transition hover:border-rose-400/50 hover:text-rose-300 disabled:cursor-not-allowed disabled:opacity-50"
                    aria-label={`Remove ${item.name}`}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between text-[11px] text-[#8390b1]">
                <span>Due: {item.due_date}</span>
                <span>Rate: {item.interest_rate || 0}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function round2(value: number) {
  return Math.round(value * 100) / 100;
}
