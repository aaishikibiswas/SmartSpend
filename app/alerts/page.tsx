"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, Suspense } from "react";
import { AlertTriangle, Receipt, Copy, BellRing, Lightbulb } from "lucide-react";
import { apiClient, type AlertItem } from "@/lib/api-client";

function AlertsContent() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const searchParams = useSearchParams();
  const focusId = searchParams.get("focus");
  const alertRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    async function load() {
      try {
        const res = await apiClient.getAlerts();
        setAlerts(res.data);
      } catch (error) {
        console.error(error);
        setAlerts([]);
      }
    }

    load();
  }, []);

  useEffect(() => {
    if (focusId && alerts.length > 0) {
      const el = alertRefs.current[focusId];
      if (el) {
        // Delay slightly to ensure layout is stable
        setTimeout(() => {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          el.classList.add("focus-highlight");
          setTimeout(() => {
            el.classList.remove("focus-highlight");
          }, 3000);
        }, 100);
      }
    }
  }, [focusId, alerts]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Smart Alerts</h1>
        <div className="flex gap-2">
          <Link href="/upload" className="text-sm font-medium text-gray-400 hover:text-white px-4 py-2 transition-colors">
            Import Fresh Data
          </Link>
          <Link href="/settings" className="flex items-center gap-2 bg-[#10182E] border border-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.05)] text-white px-4 py-2 rounded-xl transition-colors">
            <BellRing className="w-4 h-4" /> Manage Notifications
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 flex flex-col gap-4">
          <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest pl-2">Recent Alerts</h2>

          {alerts.map((alert) => (
            <div 
              key={alert.id} 
              ref={(el) => (alertRefs.current[alert.id] = el)}
              className={`glass-card p-5 border-l-2 ${alert.type === "breach" ? "border-l-rose-500" : alert.type === "duplicate" ? "border-l-[#8BE2E8]" : "border-l-blue-500"} flex gap-4 hover:bg-white/5 transition-all duration-500 cursor-pointer`}
            >
              <div className={`p-3 rounded-xl h-fit ${alert.type === "breach" ? "bg-rose-500/10" : alert.type === "duplicate" ? "bg-[#8BE2E8]/10" : "bg-blue-500/10"}`}>
                {alert.type === "breach" ? <AlertTriangle className="w-6 h-6 text-rose-500" /> : alert.type === "duplicate" ? <Copy className="w-6 h-6 text-[#8BE2E8]" /> : <Receipt className="w-6 h-6 text-blue-500" />}
              </div>
              <div className="flex-1">
                <h4 className="text-base font-bold text-white mb-1">{alert.title}</h4>
                <p className="text-sm text-gray-400 leading-relaxed mb-3">{alert.message}</p>
              </div>
            </div>
          ))}

          {alerts.length === 0 ? <p className="text-gray-500 ml-2">No new alerts.</p> : null}
        </div>

        <div>
          <div className="p-6 bg-gradient-to-b from-[#8BE2E8]/10 to-[#10182E]/50 border border-[#8BE2E8]/20 rounded-2xl sticky top-8">
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="w-5 h-5 text-[#8BE2E8]" />
              <h3 className="font-bold text-white text-lg">Next Action</h3>
            </div>
            <p className="text-sm text-gray-400 leading-relaxed mb-4">Upload another statement or review your budget settings to respond to the latest backend-generated alerts.</p>
            <Link href="/budget" className="block w-full py-2 bg-[#8BE2E8] hover:bg-[#A897FF] text-white rounded-xl text-sm font-bold shadow-[0_0_15px_rgba(139,92,246,0.2)] transition-all text-center">
              Open Budget Center
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AlertsPage() {
  return (
    <Suspense fallback={<div className="p-10 text-center text-gray-500">Loading alerts...</div>}>
      <AlertsContent />
    </Suspense>
  );
}
