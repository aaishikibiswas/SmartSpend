"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, Receipt, Copy, BellRing, Lightbulb } from "lucide-react";
import { apiClient, type AlertItem } from "@/lib/api-client";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

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

  return (
    <div className="flex flex-col gap-6">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Smart Alerts</h1>
        <div className="flex gap-2">
          <Link href="/upload" className="text-sm font-medium text-gray-400 hover:text-white px-4 py-2 transition-colors">
            Import Fresh Data
          </Link>
          <Link href="/settings" className="flex items-center gap-2 bg-[#1A2035] border border-[#2A324A] hover:bg-[#2A324A] text-white px-4 py-2 rounded-xl transition-colors">
            <BellRing className="w-4 h-4" /> Manage Notifications
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 flex flex-col gap-4">
          <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest pl-2">Recent Alerts</h2>

          {alerts.map((alert) => (
            <div key={alert.id} className={`glass-card p-5 border-l-2 ${alert.type === "breach" ? "border-l-rose-500" : alert.type === "duplicate" ? "border-l-[#8B5CF6]" : "border-l-blue-500"} flex gap-4 hover:bg-white/5 transition-colors cursor-pointer`}>
              <div className={`p-3 rounded-xl h-fit ${alert.type === "breach" ? "bg-rose-500/10" : alert.type === "duplicate" ? "bg-[#8B5CF6]/10" : "bg-blue-500/10"}`}>
                {alert.type === "breach" ? <AlertTriangle className="w-6 h-6 text-rose-500" /> : alert.type === "duplicate" ? <Copy className="w-6 h-6 text-[#8B5CF6]" /> : <Receipt className="w-6 h-6 text-blue-500" />}
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
          <div className="p-6 bg-gradient-to-b from-[#8B5CF6]/10 to-[#1A2035]/50 border border-[#8B5CF6]/20 rounded-2xl sticky top-8">
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="w-5 h-5 text-[#8B5CF6]" />
              <h3 className="font-bold text-white text-lg">Next Action</h3>
            </div>
            <p className="text-sm text-gray-400 leading-relaxed mb-4">Upload another statement or review your budget settings to respond to the latest backend-generated alerts.</p>
            <Link href="/budget" className="block w-full py-2 bg-[#8B5CF6] hover:bg-[#A78BFA] text-white rounded-xl text-sm font-bold shadow-[0_0_15px_rgba(139,92,246,0.2)] transition-all text-center">
              Open Budget Center
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
