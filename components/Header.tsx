"use client";

import Link from "next/link";
import { jsPDF } from "jspdf";
import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import AICatAssistant from "@/components/AICatAssistant";
import { useAuth } from "@/components/auth/AuthProvider";
import { useFinance } from "@/context/FinanceContext";
import { apiClient, type AlertItem } from "@/lib/api-client";
import { Bell, BrainCircuit, CalendarDays, Download, ListFilter, Settings, Upload, AlertTriangle, Copy, Receipt, X } from "lucide-react";
import dynamic from "next/dynamic";

const LiveNotificationCenter = dynamic(() => import("./dashboard/LiveNotificationCenter"), { ssr: false });

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

export default function Header() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { transactions, syncOn, setSyncOn, financialPersonality } = useFinance();
  const firstName = user?.full_name?.split(" ")[0] || "there";
  const [now, setNow] = useState<Date | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isAlertsOpen, setIsAlertsOpen] = useState(false);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [unreadAlerts, setUnreadAlerts] = useState(0);
  const [isAlertAnimating, setIsAlertAnimating] = useState(false);
  const animationTimerRef = useRef<number | null>(null);
  const isDashboard = pathname === "/" || pathname === "/dashboard" || pathname === "/dashboard/";

  useEffect(() => {
    async function loadAlerts() {
      try {
        const res = await apiClient.getAlerts();
        setAlerts(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        console.error(err);
        setAlerts([]);
      }
    }
    loadAlerts();

    const handleWsUpdate = (event: Event) => {
      const detail = (event as CustomEvent).detail;
      
      if (detail?.type === 'alert_trigger' || detail?.type === 'live-alert') {
        const incomingAlerts = Array.isArray(detail?.data?.alerts) ? detail.data.alerts : [];
        if (incomingAlerts.length > 0) {
          setAlerts((current) => {
            const existingIds = new Set(current.map(a => a.id));
            const newAlerts = incomingAlerts.filter((a: AlertItem) => !existingIds.has(a.id));
            return [...newAlerts, ...current].slice(0, 20);
          });
        }
        
        const increment = detail?.data?.latest ? 1 : Math.max(1, incomingAlerts.length ? Math.min(incomingAlerts.length, 5) : 1);
        setUnreadAlerts((current) => Math.min(99, current + increment));
        setIsAlertAnimating(true);
        if (animationTimerRef.current) window.clearTimeout(animationTimerRef.current);
        animationTimerRef.current = window.setTimeout(() => setIsAlertAnimating(false), 1500);
      }

      if (detail?.data?.alerts && Array.isArray(detail.data.alerts)) {
        setAlerts(detail.data.alerts);
      } else if (detail?.type === 'alert_trigger' && detail?.data?.alerts) {
        setAlerts(detail.data.alerts);
      }
    };
    
    window.addEventListener("smartspend:ws-update", handleWsUpdate);
    window.addEventListener("smartspend:ws-alert_trigger", handleWsUpdate);
    window.addEventListener("smartspend:ws-snapshot", handleWsUpdate);
    
    return () => {
      if (animationTimerRef.current) window.clearTimeout(animationTimerRef.current);
      window.removeEventListener("smartspend:ws-update", handleWsUpdate);
      window.removeEventListener("smartspend:ws-alert_trigger", handleWsUpdate);
      window.removeEventListener("smartspend:ws-snapshot", handleWsUpdate);
    };
  }, []);

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

  const exportRows = transactions.map((tx) => ({
    Date: tx.date,
    Name: tx.merchant,
    Category: tx.category,
    Amount: tx.amount,
    Type: tx.type,
    Source: tx.source || "uploaded",
  }));

  const exportCSV = () => {
    if (!exportRows.length) return;
    const headers = Object.keys(exportRows[0]) as Array<keyof (typeof exportRows)[number]>;
    const csv = [headers.join(","), ...exportRows.map((row) => headers.map((h) => `"${String(row[h] ?? "")}"`).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "smartspend_report.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportPDF = () => {
    if (!exportRows.length) return;
    const pdf = new jsPDF();
    pdf.setFontSize(16);
    pdf.text("SmartSpend Financial Report", 10, 10);
    let y = 20;
    for (const tx of exportRows) {
      if (y > 280) {
        pdf.addPage();
        y = 20;
      }
      pdf.setFontSize(10);
      pdf.text(`${tx.Date} | ${tx.Name} | ${tx.Category} | Rs${tx.Amount} | ${tx.Type} | ${tx.Source}`, 10, y);
      y += 6;
    }
    pdf.save("smartspend_report.pdf");
  };

  return (
    <>
      <header 
        className={`sticky top-0 z-40 flex justify-between border-b transition-all duration-300 ${
          isDashboard 
            ? "h-[210px] items-start border-white/[0.03] bg-transparent px-10 pt-8" 
            : "h-16 items-center border-[#dee5ff]/10 bg-[#060e20]/80 px-8 shadow-xl shadow-black/20 backdrop-blur-xl"
        }`} 
        style={{ position: "sticky", overflow: "visible" }}
      >
        <div className="flex flex-1 items-start gap-6 pt-2">
          {/* ── Brand Logo Pill ── */}
          {isDashboard ? (
            <AICatAssistant />
          ) : (
            <Link href="/" className="flex items-center gap-3 group">
              <div className="relative h-10 w-10 overflow-hidden rounded-xl border border-white/10 bg-[#020617] shadow-lg transition-transform group-hover:scale-105">
                <img
                  src="/strict-neon-kitten.jpg"
                  alt="SmartSpend Logo"
                  className="h-full w-full object-contain p-1.5"
                />
              </div>
              <div className="hidden flex-col md:flex">
                <span className="text-sm font-bold tracking-tight text-[#dee5ff]">SmartSpend</span>
                <span className="text-[9px] font-bold uppercase tracking-wider text-[#6366f1]/80">AI Analytics</span>
              </div>
            </Link>
          )}
        </div>

        <div className={`relative flex items-center gap-4 ${isDashboard ? "pt-12" : ""}`} style={{ zIndex: 1 }}>
          <div className="hidden gap-2 md:flex">
            <button onClick={exportCSV} className="flex items-center gap-1 rounded-full border border-white/[0.08] bg-white/[0.05] px-3 py-1 text-[10px] font-bold backdrop-blur-md transition-colors hover:bg-white/[0.12]">
              <Download className="h-3.5 w-3.5" />
              CSV
            </button>
            <button onClick={exportPDF} className="flex items-center gap-1 rounded-full border border-white/[0.08] bg-white/[0.05] px-3 py-1 text-[10px] font-bold backdrop-blur-md transition-colors hover:bg-white/[0.12]">
              <Download className="h-3.5 w-3.5" />
              PDF
            </button>
            <button
              onClick={() => setSyncOn((prev) => !prev)}
              className={`rounded-full border border-white/[0.08] px-3 py-1 text-[10px] font-bold backdrop-blur-md transition-colors ${syncOn ? "bg-[#16a34a]/20 text-[#22c55e]" : "bg-white/[0.05] text-[#a3aac4]"}`}
            >
              {syncOn ? "🟢 Bank Sync ON" : "⚪ Bank Sync OFF"}
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

          <div className="relative">
            <LiveNotificationCenter />
            <button 
              onClick={() => {
                setIsAlertsOpen((open) => {
                  const nextOpen = !open;
                  if (nextOpen) setUnreadAlerts(0);
                  return nextOpen;
                });
              }}
              className={`relative rounded-full p-2 backdrop-blur-md transition-all duration-500 focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50 ${
                isAlertAnimating 
                  ? "animate-alert-bell scale-110 bg-[#ff6e84]/30 shadow-[0_0_30px_rgba(255,110,132,0.6)] ring-2 ring-[#ff6e84]/40" 
                  : "bg-white/[0.05] border border-white/[0.08] hover:bg-white/[0.12] scale-100"
              }`}
            >
              <Bell className={`h-5 w-5 transition-colors duration-500 ${isAlertAnimating ? "text-[#ff6e84]" : "text-[#a3aac4]"}`} />
              {unreadAlerts > 0 && (
                <span className={`absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#ff6e84] text-[9px] font-bold text-white shadow-[0_0_10px_rgba(255,110,132,0.8)] ${isAlertAnimating ? "animate-alert-badge" : ""}`}>
                  {unreadAlerts}
                </span>
              )}
            </button>

            {isAlertsOpen && (
              <div className="absolute right-0 mt-2 w-[340px] max-h-[480px] overflow-y-auto rounded-2xl border border-[#27314d] bg-[#10192d] shadow-2xl backdrop-blur-xl z-50 animate-in fade-in zoom-in-95 duration-200">
                <div className="sticky top-0 bg-[#10192d]/95 backdrop-blur border-b border-[#27314d] p-4 flex justify-between items-center z-10">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-[#dee5ff]">Smart Alerts</h3>
                    {unreadAlerts > 0 && <span className="flex h-2 w-2 rounded-full bg-[#ff6e84] animate-pulse" />}
                  </div>
                  {(alerts?.length || 0) > 0 && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#a3aac4]">{(alerts?.length || 0)} active</span>
                  )}
                </div>
                <div className="p-2 flex flex-col gap-1.5">
                  {!alerts || alerts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
                      <div className="mb-3 rounded-full bg-white/5 p-3 text-[#40485d]">
                        <Bell className="h-6 w-6 opacity-20" />
                      </div>
                      <p className="text-sm font-semibold text-[#dee5ff]">No new alerts</p>
                      <p className="mt-1 text-xs text-[#a3aac4]">Your financial workspace is clear and synced.</p>
                    </div>
                  ) : (
                    alerts.map((alert) => {
                      const isHigh = alert.type === "breach" || alert.title.toLowerCase().includes("warning") || alert.title.toLowerCase().includes("spike");
                      const isMedium = alert.type === "duplicate" || alert.title.toLowerCase().includes("pressure");
                      
                      return (
                        <Link 
                          href={`/alerts?focus=${alert.id}`}
                          key={alert.id} 
                          onClick={() => setIsAlertsOpen(false)}
                          className="relative flex gap-3 p-3.5 hover:bg-[#192540] rounded-xl transition-all cursor-pointer group border border-transparent hover:border-white/5"
                        >
                          <div className={`mt-0.5 rounded-full p-2 h-fit shrink-0 ${
                            isHigh ? "bg-rose-500/15 text-rose-400" : 
                            isMedium ? "bg-amber-500/15 text-amber-400" : 
                            "bg-blue-500/15 text-blue-400"
                          }`}>
                            {isHigh ? <AlertTriangle className="w-4 h-4" /> : isMedium ? <Copy className="w-4 h-4" /> : <Receipt className="w-4 h-4" />}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex justify-between items-start mb-0.5">
                              <p className="text-[13px] font-bold text-[#dee5ff] group-hover:text-white transition-colors truncate pr-4">{alert.title}</p>
                              <span className="text-[9px] font-medium text-[#6d758c] whitespace-nowrap pt-0.5">Just now</span>
                            </div>
                            <p className="text-[12px] text-[#a3aac4] leading-relaxed line-clamp-3 mb-2">{alert.message}</p>
                            <div className="flex items-center gap-3">
                              <span className={`text-[9px] font-bold uppercase tracking-wider ${
                                isHigh ? "text-rose-500/80" : 
                                isMedium ? "text-amber-500/80" : 
                                "text-blue-500/80"
                              }`}>
                                {isHigh ? "High Severity" : isMedium ? "Medium Priority" : "System Insight"}
                              </span>
                            </div>
                          </div>
                          <button 
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              setAlerts((current) => current.filter((a) => a.id !== alert.id));
                            }}
                            className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-white/10 text-[#6d758c] hover:text-white transition-all"
                            aria-label="Dismiss alert"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </Link>
                      );
                    })
                  )}
                </div>
                {(alerts?.length || 0) > 0 && (
                  <div className="sticky bottom-0 bg-[#10192d]/95 backdrop-blur border-t border-[#27314d] p-2.5">
                    <Link href="/alerts" onClick={() => setIsAlertsOpen(false)} className="flex items-center justify-center gap-2 w-full py-2.5 text-center text-[11px] font-bold uppercase tracking-widest text-[#6366f1] hover:text-[#8183f4] transition-all bg-white/[0.03] hover:bg-white/[0.06] rounded-xl">
                      Enter Alerts Center
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>

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
                className="h-8 w-8 rounded-full border border-white/20"
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

      <div className="flex flex-wrap items-center gap-4 border-b border-white/[0.03] bg-transparent px-8 py-4">
        <div className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-2 backdrop-blur-md">
          <CalendarDays className="h-4 w-4 text-[#a3aac4]" />
          <span className="text-xs font-semibold text-[#dee5ff]">{liveRange}</span>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.04] px-4 py-2 backdrop-blur-md">
          <BrainCircuit className="h-4 w-4 text-[#a3a6ff]" />
          <div>
            <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[rgba(255,255,255,0.92)]">Financial Personality</p>
            <p className="text-xs font-semibold text-[rgba(255,255,255,0.92)]">{financialPersonality}</p>
          </div>
        </div>
        <button className="ml-auto flex items-center gap-1 text-xs font-bold text-[#a3a6ff] hover:underline">
          <ListFilter className="h-4 w-4" />
          {syncOn ? "Syncing transactions every few seconds" : "Sync paused"} | {liveStamp}
        </button>
      </div>

      {isDashboard ? <section className="flex flex-col items-start justify-between gap-4 px-8 pb-2 pt-8 md:flex-row md:items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-[#dee5ff] md:text-4xl">Welcome back, {firstName}!</h1>
          <p className="mt-2 font-medium text-[#a3aac4]">Your AI finance assistant has fresh budget, alert, and forecast insights today.</p>
        </div>

        <Link
          href="/upload"
          className="cinematic-soft-glow flex items-center gap-2 rounded-full bg-gradient-to-br from-[#a3a6ff] to-[#6063ee] px-6 py-3 font-bold text-[#0f00a4] shadow-lg transition-all hover:opacity-90"
        >
          <Upload className="h-4 w-4" />
          Upload Statement
        </Link>
      </section> : null}
    </>
  );
}
