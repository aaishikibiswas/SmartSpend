import { NextResponse } from "next/server";
import { BACKEND_BASE, getSessionToken } from "@/lib/auth-session";

type ProxyOptions = {
  method?: string;
  body?: BodyInit | null;
  contentType?: string;
  timeoutMessage?: string;
};

export async function proxyBackend(path: string, options: ProxyOptions = {}) {
  const token = await getSessionToken();
  if (!token) {
    return NextResponse.json({ status: 401, data: null, message: "Authentication required." }, { status: 401 });
  }

  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token}`);
  if (options.contentType) {
    headers.set("Content-Type", options.contentType);
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(`${BACKEND_BASE}${path}`, {
      method: options.method || "GET",
      headers,
      body: options.body ?? null,
      cache: "no-store",
      signal: controller.signal,
    });

    const body = await response.text();
    return new Response(body, {
      status: response.status,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  } catch (err: any) {
    console.warn(`[Backend Proxy] Request to ${path} failed:`, err?.message || err);
    
    const isAbort = err?.name === "AbortError" || err?.message === "aborted";
    const status = isAbort ? 504 : 503;
    const message = isAbort 
      ? (options.timeoutMessage || "Backend request timed out")
      : "Backend service temporarily unavailable";

    return NextResponse.json(
      {
        status,
        data: null,
        message,
        error: err?.code || err?.name || "UNKNOWN_ERROR"
      },
      { status },
    );
  } finally {
    if (timeoutId) clearTimeout(timeoutId);
  }
}
