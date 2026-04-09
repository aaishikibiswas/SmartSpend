"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

function getWebSocketUrl(token: string) {
  const configuredBase = process.env.NEXT_PUBLIC_BACKEND_WS_BASE?.replace(/\/+$/, "");

  if (configuredBase) {
    return `${configuredBase}/ws?token=${encodeURIComponent(token)}`;
  }

  if (typeof window === "undefined") {
    return `ws://127.0.0.1:8001/ws?token=${encodeURIComponent(token)}`;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host || "127.0.0.1:3001";
  return `${protocol}//${host}/ws?token=${encodeURIComponent(token)}`;
}

export default function DashboardLiveSocket() {
  const router = useRouter();

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimer: number | null = null;
    let refreshTimer: number | null = null;
    let disposed = false;

    const connect = async () => {
      let token = "";
      try {
        const response = await fetch("/api/auth/ws-token", {
          cache: "no-store",
        });
        if (!response.ok) {
          return;
        }
        const payload = await response.json();
        token = payload?.data?.token || "";
      } catch (error) {
        console.error("WebSocket token fetch failed", error);
        return;
      }

      if (!token) {
        return;
      }

      socket = new WebSocket(getWebSocketUrl(token));

      socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          window.dispatchEvent(new CustomEvent("smartspend:ws-update", { detail: message }));
          if (message?.type) {
            window.dispatchEvent(new CustomEvent(`smartspend:ws-${message.type}`, { detail: message }));
          }

          if (message?.type === "update" || message?.type === "new_transaction" || message?.type === "alert_trigger" || message?.type === "prediction_update") {
            if (refreshTimer) window.clearTimeout(refreshTimer);
            refreshTimer = window.setTimeout(() => {
              router.refresh();
            }, 250);
          }
        } catch (error) {
          console.error("WebSocket message parse failed", error);
        }
      };

      socket.onclose = () => {
        if (!disposed) {
          reconnectTimer = window.setTimeout(() => {
            void connect();
          }, 1500);
        }
      };

      socket.onerror = () => {
        socket?.close();
      };
    };

    void connect();

    return () => {
      disposed = true;
      if (refreshTimer) window.clearTimeout(refreshTimer);
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [router]);

  return null;
}
