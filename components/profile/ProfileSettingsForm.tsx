"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Save } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { apiClient, type AuthUser } from "@/lib/api-client";

export default function ProfileSettingsForm({ initialUser }: { initialUser: AuthUser }) {
  const router = useRouter();
  const { setUser, logout } = useAuth();
  const [fullName, setFullName] = useState(initialUser.full_name);
  const [plan, setPlan] = useState(initialUser.plan);
  const [status, setStatus] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("");
    setIsSaving(true);
    try {
      const response = await apiClient.updateProfile({ full_name: fullName, plan });
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
    <form onSubmit={handleSubmit} className="rounded-[26px] border border-[#27314d] bg-[#10192d] p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-[#dee5ff]">Profile Settings</h2>
          <p className="mt-1 text-sm text-[#a3aac4]">Edit your name and plan while keeping your session active across SmartSpend.</p>
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
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D8AB5]">Full Name</span>
          <input
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            className="h-11 w-full rounded-2xl border border-white/10 bg-[#141f38] px-4 text-sm text-[#dee5ff] outline-none focus:border-[#8B7DFF]"
          />
        </label>
        <label className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-[0.22em] text-[#7D8AB5]">Plan</span>
          <input
            value={plan}
            onChange={(event) => setPlan(event.target.value)}
            className="h-11 w-full rounded-2xl border border-white/10 bg-[#141f38] px-4 text-sm text-[#dee5ff] outline-none focus:border-[#8B7DFF]"
          />
        </label>
      </div>

      {status ? <p className="mt-4 text-sm text-[#b8c2e7]">{status}</p> : null}

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => router.push("/login")}
          className="rounded-xl border border-white/10 bg-[#141f38] px-4 py-2 text-sm font-semibold text-[#dee5ff] transition hover:bg-[#1a2746]"
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

