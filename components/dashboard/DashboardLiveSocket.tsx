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

function getEventSourceUrl(token: string) {
  const configuredBase = process.env.NEXT_PUBLIC_BACKEND_API_BASE?.replace(/\/+$/, "");

  if (configuredBase) {
    return `${configuredBase}/sse?token=${encodeURIComponent(token)}`;
  }

  if (typeof window === "undefined") {
    return `http://127.0.0.1:8001/sse?token=${encodeURIComponent(token)}`;
  }

  if (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") {
    return `http://127.0.0.1:8001/sse?token=${encodeURIComponent(token)}`;
  }

  return `${window.location.origin.replace(/\/+$/, "")}/sse?token=${encodeURIComponent(token)}`;
}

export default function DashboardLiveSocket() {
  const router = useRouter();

  useEffect(() => {
    let socket: WebSocket | null = null;
    let eventSource: EventSource | null = null;
    let reconnectTimer: number | null = null;
    let refreshTimer: number | null = null;
    let disposed = false;
    let usingFallbackSocket = false;

    const handleMessage = (message: Record<string, unknown>, transport: "sse" | "ws") => {
      window.dispatchEvent(new CustomEvent("smartspend:live-update", { detail: { ...message, transport } }));
      if (message?.type && typeof message.type === "string") {
        window.dispatchEvent(new CustomEvent(`smartspend:live-${message.type}`, { detail: { ...message, transport } }));
        window.dispatchEvent(new CustomEvent(`smartspend:ws-${message.type}`, { detail: { ...message, transport } }));
      }

      if (message?.type === "update" || message?.type === "new_transaction" || message?.type === "alert_trigger" || message?.type === "prediction_update") {
        if (refreshTimer) window.clearTimeout(refreshTimer);
        refreshTimer = window.setTimeout(() => {
          router.refresh();
        }, 250);
      }
    };

    const connectWebSocket = (token: string) => {
      usingFallbackSocket = true;
      socket = new WebSocket(getWebSocketUrl(token));

      socket.onmessage = (event) => {
        try {
          handleMessage(JSON.parse(event.data), "ws");
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

      try {
        eventSource = new EventSource(getEventSourceUrl(token));
        usingFallbackSocket = false;

        eventSource.onmessage = (event) => {
          try {
            handleMessage(JSON.parse(event.data), "sse");
          } catch (error) {
            console.error("SSE message parse failed", error);
          }
        };

        for (const eventName of ["snapshot", "update", "new_transaction", "alert_trigger", "prediction_update"]) {
          eventSource.addEventListener(eventName, (event) => {
            try {
              handleMessage(JSON.parse((event as MessageEvent).data), "sse");
            } catch (error) {
              console.error(`SSE ${eventName} parse failed`, error);
            }
          });
        }

        eventSource.onerror = () => {
          eventSource?.close();
          eventSource = null;
          if (!disposed && !usingFallbackSocket) {
            connectWebSocket(token);
          }
        };
      } catch (error) {
        console.error("SSE connection failed, falling back to WebSocket", error);
        connectWebSocket(token);
      }
    };

    void connect();

    return () => {
      disposed = true;
      if (refreshTimer) window.clearTimeout(refreshTimer);
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      eventSource?.close();
      socket?.close();
    };
  }, [router]);

  return null;
}
