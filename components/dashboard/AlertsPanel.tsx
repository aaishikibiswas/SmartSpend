"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Copy, CreditCard } from "lucide-react";
import { apiClient, type AlertItem } from "@/lib/api-client";

function alertIcon(type: string) {
  if (type === "breach" || type === "warning") {
    return {
      icon: AlertTriangle,
      accent: "border-[#ff6e84]",
      bg: "bg-[#ff6e84]/10",
      text: "text-[#ff6e84]",
    };
  }

  if (type === "duplicate") {
    return {
      icon: Copy,
      accent: "border-[#a88cfb]",
      bg: "bg-[#a88cfb]/10",
      text: "text-[#a88cfb]",
    };
  }

  return {
    icon: CreditCard,
    accent: "border-[#a3a6ff]",
    bg: "bg-[#a3a6ff]/10",
    text: "text-[#a3a6ff]",
  };
}

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await apiClient.getAlerts();
        setAlerts(res.data.slice(0, 3));
      } catch (error) {
        console.error(error);
        setAlerts([]);
      }
    }

    load();

    function handleBudgetUpdated() {
      void load();
    }

    window.addEventListener("smartspend:budget-updated", handleBudgetUpdated);
    function handleRealtimeUpdate(event: Event) {
      const detail = (event as CustomEvent).detail;
      if (detail?.data?.alerts) {
        setAlerts((detail.data.alerts as AlertItem[]).slice(0, 3));
      }
    }

    window.addEventListener("smartspend:ws-update", handleRealtimeUpdate);
    return () => {
      window.removeEventListener("smartspend:budget-updated", handleBudgetUpdated);
      window.removeEventListener("smartspend:ws-update", handleRealtimeUpdate);
    };
  }, []);

  return (
    <section className="space-y-4">
      <h4 className="ml-2 font-bold text-[#dee5ff]">Smart Alerts</h4>

      {alerts.length === 0 ? (
        <div className="glass-card rounded-2xl p-4 text-sm text-[#a3aac4]">No alerts yet. Upload a statement to trigger the alert engine.</div>
      ) : null}

      {alerts.map((alert) => {
        const styles = alertIcon(alert.type);
        const Icon = styles.icon;
        return (
          <div key={alert.id} className={`glass-card flex items-start gap-4 rounded-2xl border-l-4 p-4 ${styles.accent}`}>
            <div className={`rounded-lg p-2 ${styles.bg} ${styles.text}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <p className="text-xs font-bold text-[#dee5ff]">{alert.title}</p>
              <p className="mt-1 text-[11px] text-[#a3aac4]">{alert.message}</p>
              {alert.type === "duplicate" ? (
                <button className="mt-2 text-[10px] font-bold text-[#a88cfb] hover:underline">Flag as Error</button>
              ) : null}
            </div>
          </div>
        );
      })}
    </section>
  );
}
