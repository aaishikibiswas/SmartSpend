"use client";

import { useEffect, useRef, useState } from "react";
import { BellRing, CheckCircle2, TriangleAlert } from "lucide-react";
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
  const flushTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const dismissLater = (id: number) => {
      window.setTimeout(() => {
        setItems((current) => current.filter((item) => item.id !== id));
      }, 4200);
    };

    const push = (item: Omit<Notification, "id">) => {
      const id = Date.now() + Math.floor(Math.random() * 1000);
      setItems((current) => [{ id, ...item }, ...current].slice(0, 4));
      dismissLater(id);
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
      });
    };

    window.addEventListener("smartspend:ws-new_transaction", onTransaction as EventListener);
    window.addEventListener("smartspend:ws-alert_trigger", onAlert as EventListener);

    return () => {
      if (flushTimerRef.current) {
        window.clearTimeout(flushTimerRef.current);
      }
      window.removeEventListener("smartspend:ws-new_transaction", onTransaction as EventListener);
      window.removeEventListener("smartspend:ws-alert_trigger", onAlert as EventListener);
    };
  }, []);

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed right-5 top-24 z-[70] flex w-[340px] flex-col gap-3">
      {items.map((item) => {
        const styles = stylesFor(item.tone);
        const Icon = styles.icon;
        return (
          <div key={item.id} className={`pointer-events-auto rounded-2xl border px-4 py-3 shadow-2xl backdrop-blur-xl ${styles.shell}`}>
            <div className="flex items-start gap-3">
              <div className={`mt-0.5 rounded-xl p-2 ${styles.badge}`}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-[#edf2ff]">{item.title}</p>
                <p className="mt-1 text-xs leading-5 text-[#a8b1ce]">{item.message}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

