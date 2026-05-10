"use client";

import { useEffect, useRef, useState } from "react";
import { BellRing, CheckCircle2, TriangleAlert, X } from "lucide-react";
import type { AlertItem, TransactionItem } from "@/lib/api-client";

type Notification = {
  id: number;
  title: string;
  message: string;
  tone: "info" | "success" | "warning";
};

function stylesFor(tone: Notification["tone"]) {
  if (tone === "warning") {
    return {
      icon: TriangleAlert,
      shell: "border-[#ff6e84]/40 bg-[#1d1322]",
      badge: "bg-[#ff6e84]/15 text-[#ff8ca0]",
    };
  }
  if (tone === "success") {
    return {
      icon: CheckCircle2,
      shell: "border-[#77f0c1]/30 bg-[#10211d]",
      badge: "bg-[#77f0c1]/15 text-[#77f0c1]",
    };
  }
  return {
    icon: BellRing,
    shell: "border-[#8e8cff]/30 bg-[#121a2d]",
    badge: "bg-[#8e8cff]/15 text-[#b2b1ff]",
  };
}

export default function LiveNotificationCenter() {
  const [items, setItems] = useState<Notification[]>([]);
  const bufferRef = useRef<TransactionItem[]>([]);
  const seenAlertsRef = useRef<Set<string>>(new Set());
  const flushTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const push = (item: Omit<Notification, "id"> & { originalId?: number }) => {
      if (item.originalId) {
        if (seenAlertsRef.current.has(item.originalId.toString())) return;
        seenAlertsRef.current.add(item.originalId.toString());
      }
      const id = Date.now() + Math.floor(Math.random() * 1000);
      setItems((current) => [{ id, ...item }, ...current].slice(0, 3));
      
      // Auto-dismiss after 2.5 seconds
      setTimeout(() => {
        setItems((current) => current.filter((i) => i.id !== id));
      }, 2500);
    };

    const flushTransactions = () => {
      const batch = bufferRef.current;
      bufferRef.current = [];
      flushTimerRef.current = null;
      if (batch.length === 0) return;

      if (batch.length === 1) {
        const transaction = batch[0];
        push({
          title: "New Transaction Synced",
          message: `${transaction.merchant} for Rs. ${Math.abs(Number(transaction.amount || 0)).toLocaleString()} is now reflected on your dashboard.`,
          tone: "success",
        });
        return;
      }

      push({
        title: "Multiple Transactions Processed",
        message: `${batch.length} transactions were streamed into SmartSpend and your dashboard is refreshing in real time.`,
        tone: "success",
      });
    };

    const onTransaction = (event: Event) => {
      const detail = (event as CustomEvent).detail as { data?: { transaction?: TransactionItem } } | undefined;
      const transaction = detail?.data?.transaction;
      if (!transaction) return;
      bufferRef.current.push(transaction);
      if (flushTimerRef.current) {
        window.clearTimeout(flushTimerRef.current);
      }
      flushTimerRef.current = window.setTimeout(flushTransactions, 900);
    };

    const onAlert = (event: Event) => {
      const detail = (event as CustomEvent).detail as { data?: { latest?: AlertItem } } | undefined;
      const latest = detail?.data?.latest;
      if (!latest) return;
      push({
        title: latest.title,
        message: latest.message,
        tone: "warning",
        originalId: latest.id,
      });
    };

    window.addEventListener("smartspend:live-new_transaction", onTransaction as EventListener);
    window.addEventListener("smartspend:live-alert_trigger", onAlert as EventListener);
    window.addEventListener("smartspend:ws-new_transaction", onTransaction as EventListener);
    window.addEventListener("smartspend:ws-alert_trigger", onAlert as EventListener);

    return () => {
      if (flushTimerRef.current) {
        window.clearTimeout(flushTimerRef.current);
      }
      window.removeEventListener("smartspend:live-new_transaction", onTransaction as EventListener);
      window.removeEventListener("smartspend:live-alert_trigger", onAlert as EventListener);
      window.removeEventListener("smartspend:ws-new_transaction", onTransaction as EventListener);
      window.removeEventListener("smartspend:ws-alert_trigger", onAlert as EventListener);
    };
  }, []);

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="absolute right-0 top-[calc(100%+12px)] z-[70] flex w-[320px] flex-col gap-3 pointer-events-none">
      {items.map((item) => {
        const styles = stylesFor(item.tone);
        const Icon = styles.icon;
        return (
          <div key={item.id} className={`pointer-events-auto flex items-center justify-between gap-3.5 rounded-2xl border px-4 py-3 shadow-2xl backdrop-blur-xl transition-all duration-500 animate-in fade-in slide-in-from-top-4 ${styles.shell}`}>
            <div className="flex items-center gap-3.5 min-w-0">
              <div className={`shrink-0 rounded-xl p-2 ${styles.badge} flex items-center justify-center`}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex flex-col justify-center">
                <p className="truncate text-[12px] font-bold text-[#edf2ff] leading-none mb-[1px]">{item.title}</p>
                {item.message && (
                  <p className="truncate text-[10px] font-medium text-[#a3aac4] mt-1.5 leading-tight">{item.message}</p>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setItems((current) => current.filter((currentItem) => currentItem.id !== item.id))}
              className="ml-2 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-[#9da8cb] hover:text-white hover:bg-white/10 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
