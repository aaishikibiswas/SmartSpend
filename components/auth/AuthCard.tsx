"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, LoaderCircle } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { apiClient } from "@/lib/api-client";

type Mode = "login" | "register";

export default function AuthCard({ mode }: { mode: Mode }) {
  const router = useRouter();
  const { setUser } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isLogin = mode === "login";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = isLogin
        ? await apiClient.login({ email: form.email, password: form.password })
        : await apiClient.register(form);

      setUser(response.data.user);
      router.push("/");
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Something went wrong.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="rounded-[32px] border border-[rgba(255,255,255,0.05)] bg-[#0b1325]/95 p-8 shadow-[0_30px_90px_rgba(1,6,18,0.5)] backdrop-blur-xl">
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#A897FF]">SmartSpend Identity</p>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-[#F4F6FF]">{isLogin ? "Sign in to your profile" : "Create your SmartSpend profile"}</h1>
        <p className="mt-2 text-sm text-[#B7BDD9]">
          {isLogin
            ? "Use your account to sync your dashboard, profile card, and financial workspace."
            : "Create a secure account so your profile and dashboard identity stay connected."}
        </p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        {!isLogin ? (
          <label className="block">
            <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-[#9aa3c7]">Full Name</span>
            <input
              value={form.full_name}
              onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
              required
              className="w-full rounded-2xl border border-[rgba(255,255,255,0.05)] bg-[#121c34] px-4 py-3 text-sm text-[#F4F6FF] outline-none transition focus:border-[#7277ff]"
              placeholder="Aaline Roy"
            />
          </label>
        ) : null}

        <label className="block">
          <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-[#9aa3c7]">Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            required
            className="w-full rounded-2xl border border-[rgba(255,255,255,0.05)] bg-[#121c34] px-4 py-3 text-sm text-[#F4F6FF] outline-none transition focus:border-[#7277ff]"
            placeholder="you@smartspend.ai"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-[#9aa3c7]">Password</span>
          <input
            type="password"
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            required
            minLength={8}
            className="w-full rounded-2xl border border-[rgba(255,255,255,0.05)] bg-[#121c34] px-4 py-3 text-sm text-[#F4F6FF] outline-none transition focus:border-[#7277ff]"
            placeholder="Minimum 8 characters"
          />
        </label>

        {error ? <p className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</p> : null}

        <button
          type="submit"
          disabled={isSubmitting}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-br from-[#A897FF] to-[#6063ee] px-5 py-3.5 text-sm font-bold text-[#0f00a4] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
          {isLogin ? "Sign In" : "Create Account"}
        </button>
      </form>

      <p className="mt-6 text-sm text-[#B7BDD9]">
        {isLogin ? "Need an account?" : "Already have an account?"}{" "}
        <Link href={isLogin ? "/register" : "/login"} className="font-semibold text-[#A897FF] hover:underline">
          {isLogin ? "Register here" : "Sign in"}
        </Link>
      </p>

      {isLogin ? (
        <div className="mt-6 rounded-2xl border border-[rgba(255,255,255,0.05)] bg-[#10182E] px-4 py-3 text-xs text-[#B7BDD9]">
          Demo account: <span className="font-semibold text-[#F4F6FF]">adaline@smartspend.ai</span> /{" "}
          <span className="font-semibold text-[#F4F6FF]">SmartSpend@123</span>
        </div>
      ) : null}
    </div>
  );
}
