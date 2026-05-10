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
    const response = await fetch(`${BACKEND_BASE}${path}`, {
      method: options.method || "GET",
      headers,
      body: options.body ?? null,
      cache: "no-store",
    });

    const body = await response.text();
    return new Response(body, {
      status: response.status,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json(
      {
        status: 503,
        data: null,
        message: options.timeoutMessage || "Backend unavailable",
      },
      { status: 503 },
    );
  }
}
