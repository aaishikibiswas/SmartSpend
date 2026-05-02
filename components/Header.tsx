"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import { Bell, BrainCircuit, CalendarDays, Download, ListFilter, Search, Settings, Upload } from "lucide-react";

function formatRange(now: Date) {
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  const format = (value: Date) =>
    value.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  return `${format(start)} - ${format(end)}`;
}

export default function Header({ financialPersonality }: { financialPersonality: string }) {
  const { user, logout } = useAuth();
  const firstName = user?.full_name?.split(" ")[0] || "there";
  const [now, setNow] = useState<Date | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => {
    const syncClock = () => setNow(new Date());
    syncClock();
    const timer = window.setInterval(syncClock, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const liveRange = now ? formatRange(now) : "Loading current month...";
  const liveStamp =
    now?.toLocaleString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }) || "Syncing local time...";

  return (
    <>
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-[#dee5ff]/10 bg-[#060e20]/80 px-8 shadow-xl shadow-black/20 backdrop-blur-xl">
        <div className="flex flex-1 items-center gap-6">
          <h2 className="hidden text-lg font-bold text-[#dee5ff] md:block">SmartSpend Analytics</h2>
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a3aac4]" />
            <input
              type="text"
              placeholder="Search analytics, goals, or AI help..."
              className="w-full rounded-full border-none bg-[#192540] py-2 pl-10 pr-4 text-sm text-[#dee5ff] placeholder:text-[#a3aac4]/50 outline-none focus:ring-1 focus:ring-[#6366f1]/50"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden gap-2 md:flex">
            <button className="flex items-center gap-1 rounded-full border border-[#40485d]/30 bg-[#141f38] px-3 py-1 text-[10px] font-bold transition-colors hover:bg-[#192540]">
              <Download className="h-3.5 w-3.5" />
              CSV
            </button>
            <button className="flex items-center gap-1 rounded-full border border-[#40485d]/30 bg-[#141f38] px-3 py-1 text-[10px] font-bold transition-colors hover:bg-[#192540]">
              <Download className="h-3.5 w-3.5" />
              PDF
            </button>
          </div>

          <div className="mx-2 hidden h-8 w-px bg-[#40485d]/30 md:block" />

          <Link
            href="/settings"
            aria-label="Open settings"
            className="rounded-full p-2 transition-all hover:bg-[#192540] focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50"
          >
            <Settings className="h-5 w-5 text-[#a3aac4]" />
          </Link>

          <button className="relative rounded-full p-2 transition-all hover:bg-[#192540]">
            <Bell className="h-5 w-5 text-[#a3aac4]" />
            <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-[#ff6e84]" />
          </button>

          <div className="relative">
            <button 
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="relative rounded-full transition-all focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50"
            >
              <img
                src={`https://i.pravatar.cc/150?u=${user?.avatar_seed || "guest"}`}
                alt="User profile"
                width={32}
                height={32}
                className="h-8 w-8 rounded-full border border-[#a3a6ff]/20"
              />
            </button>
            
            {isProfileOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-2xl border border-[#27314d] bg-[#10192d] p-4 shadow-xl backdrop-blur-xl">
                <div className="mb-3 border-b border-[#27314d] pb-3">
                  <p className="font-bold text-[#dee5ff]">{user?.full_name || "Guest User"}</p>
                  <p className="text-xs text-[#a3aac4]">{user?.email || "No email"}</p>
                </div>
                <div className="space-y-2 text-sm text-[#dee5ff]">
                  <div className="flex justify-between">
                    <span className="text-[#a3aac4]">Plan</span>
                    <span>{user?.plan || "Pro Plan"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#a3aac4]">Currency</span>
                    <span>{user?.preferred_currency || "INR"}</span>
                  </div>
                </div>
                <div className="mt-4 flex flex-col gap-2 pt-2 border-t border-[#27314d]">
                  <Link 
                    href="/profile" 
                    onClick={() => setIsProfileOpen(false)}
                    className="block rounded-lg px-3 py-2 text-center text-sm font-medium text-[#dee5ff] hover:bg-[#192540]"
                  >
                    View Full Profile
                  </Link>
                  <button
                    type="button"
                    onClick={() => void logout()}
                    className="block rounded-lg px-3 py-2 text-center text-sm font-medium text-[#ff6e84] hover:bg-[#192540]"
                  >
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-4 border-b border-[#40485d]/10 bg-[#091328]/50 px-8 py-4">
        <div className="flex items-center gap-2 rounded-xl border border-[#40485d]/20 bg-[#141f38] px-4 py-2">
          <CalendarDays className="h-4 w-4 text-[#a3aac4]" />
          <span className="text-xs font-semibold text-[#dee5ff]">{liveRange}</span>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-[#40485d]/20 bg-[#141f38] px-4 py-2">
          <BrainCircuit className="h-4 w-4 text-[#a3a6ff]" />
          <div>
            <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#7D8AB5]">Financial Personality</p>
            <p className="text-xs font-semibold text-[#dee5ff]">{financialPersonality}</p>
          </div>
        </div>
        <button className="ml-auto flex items-center gap-1 text-xs font-bold text-[#a3a6ff] hover:underline">
          <ListFilter className="h-4 w-4" />
          {liveStamp}
        </button>
      </div>

      <section className="flex flex-col items-start justify-between gap-4 px-8 pb-2 pt-8 md:flex-row md:items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-[#dee5ff] md:text-4xl">Welcome back, {firstName}!</h1>
          <p className="mt-2 font-medium text-[#a3aac4]">Your AI finance assistant has fresh budget, alert, and forecast insights today.</p>
        </div>

        <Link
          href="/upload"
          className="flex items-center gap-2 rounded-full bg-gradient-to-br from-[#a3a6ff] to-[#6063ee] px-6 py-3 font-bold text-[#0f00a4] shadow-lg transition-all hover:opacity-90"
        >
          <Upload className="h-4 w-4" />
          Upload Statement
        </Link>
      </section>
    </>
  );
}
