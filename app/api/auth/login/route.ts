import { NextResponse } from "next/server";
import { BACKEND_BASE, SESSION_COOKIE } from "@/lib/auth-session";
import { shouldUseSecureCookies } from "@/lib/backend-config";

export async function POST(request: Request) {
  const payload = await request.json();

  const response = await fetch(`${BACKEND_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    return NextResponse.json(
      { message: body?.detail || body?.message || "Login failed." },
      { status: response.status },
    );
  }

  const sessionToken = body?.data?.sessionToken;
  const nextResponse = NextResponse.json(body, { status: response.status });

  if (sessionToken) {
    nextResponse.cookies.set(SESSION_COOKIE, sessionToken, {
      httpOnly: true,
      sameSite: "lax",
      secure: shouldUseSecureCookies(),
      path: "/",
      maxAge: 60 * 60 * 24 * 7,
    });
  }

  return nextResponse;
}
