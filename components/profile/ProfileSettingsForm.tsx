"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Save } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { apiClient, type AuthUser } from "@/lib/api-client";

export default function ProfileSettingsForm({ initialUser }: { initialUser: AuthUser }) {
  const router = useRouter();
  const { setUser, logout, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(initialUser.full_name);
  const [plan, setPlan] = useState(initialUser.plan);
  const [preferredCurrency, setPreferredCurrency] = useState(initialUser.preferred_currency || "INR");
  const [timezone, setTimezone] = useState(initialUser.timezone || "Asia/Kolkata");
  const [city, setCity] = useState(initialUser.city || "");
  const [occupation, setOccupation] = useState(initialUser.occupation || "");
  const [status, setStatus] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("");
    setIsSaving(true);
    try {
      const response = await apiClient.updateProfile({
        full_name: fullName,
        plan,
        preferred_currency: preferredCurrency,
        timezone,
        city,
        occupation,
      });
      setUser(response.data);
      setStatus("Profile updated successfully.");
      router.refresh();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to update profile right now.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-[26px] border border-[rgba(255,255,255,0.05)] bg-[#10182E] p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-[#F4F6FF]">Profile Settings</h2>
          <p className="mt-1 text-sm text-[#B7BDD9]">Edit your name and plan while keeping your session active across SmartSpend.</p>
        </div>
        <button
          type="submit"
          disabled={isSaving}
          className="inline-flex items-center gap-2 rounded-xl bg-[#7B6CF6] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#8B7DFF] disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Save className="h-4 w-4" />
          {isSaving ? "Saving..." : "Save"}
        </button>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <label className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D839E]">Full Name</span>
          <input
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            className="h-11 w-full rounded-2xl border border-white/10 bg-[#10182E] px-4 text-sm text-[#F4F6FF] outline-none focus:border-[#8B7DFF]"
          />
        </label>
        <label className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D839E]">Email</span>
          <input
            value={initialUser.email}
            readOnly
            className="h-11 w-full rounded-2xl border border-white/10 bg-[#0f172b] px-4 text-sm text-[#8f9cc0] outline-none"
          />
        </label>
        <label className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D839E]">Plan</span>
          <input
            value={plan}
            onChange={(event) => setPlan(event.target.value)}
            className="h-11 w-full rounded-2xl border border-white/10 bg-[#10182E] px-4 text-sm text-[#F4F6FF] outline-none focus:border-[#8B7DFF]"
          />
        </label>
        <label className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D839E]">Preferred Currency</span>
          <select
            value={preferredCurrency}
            onChange={(event) => setPreferredCurrency(event.target.value)}
            className="h-11 w-full rounded-2xl border border-white/10 bg-[#10182E] px-4 text-sm text-[#F4F6FF] outline-none focus:border-[#8B7DFF]"
          >
            <option value="INR">INR - Indian Rupee</option>
            <option value="USD">USD - US Dollar</option>
            <option value="EUR">EUR - Euro</option>
            <option value="GBP">GBP - British Pound</option>
          </select>
        </label>
        <label className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D839E]">Timezone</span>
          <input
            value={timezone}
            onChange={(event) => setTimezone(event.target.value)}
            className="h-11 w-full rounded-2xl border border-white/10 bg-[#10182E] px-4 text-sm text-[#F4F6FF] outline-none focus:border-[#8B7DFF]"
          />
        </label>
        <label className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D839E]">City</span>
          <input
            value={city}
            onChange={(event) => setCity(event.target.value)}
            className="h-11 w-full rounded-2xl border border-white/10 bg-[#10182E] px-4 text-sm text-[#F4F6FF] outline-none focus:border-[#8B7DFF]"
          />
        </label>
        <label className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D839E]">Occupation</span>
          <input
            value={occupation}
            onChange={(event) => setOccupation(event.target.value)}
            className="h-11 w-full rounded-2xl border border-white/10 bg-[#10182E] px-4 text-sm text-[#F4F6FF] outline-none focus:border-[#8B7DFF]"
          />
        </label>
      </div>

      {status ? <p className="mt-4 text-sm text-[#b8c2e7]">{status}</p> : null}

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => void refreshUser()}
          className="rounded-xl border border-white/10 bg-[#10182E] px-4 py-2 text-sm font-semibold text-[#F4F6FF] transition hover:bg-[#1a2746]"
        >
          Refresh Profile
        </button>
        <button
          type="button"
          onClick={() => router.push("/login")}
          className="rounded-xl border border-white/10 bg-[#10182E] px-4 py-2 text-sm font-semibold text-[#F4F6FF] transition hover:bg-[#1a2746]"
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => void logout()}
          className="rounded-xl border border-[#ff6e84]/20 bg-[#21131c] px-4 py-2 text-sm font-semibold text-[#ffd6dc] transition hover:bg-[#2a1723]"
        >
          Log Out
        </button>
      </div>
    </form>
  );
}
