import { NextResponse } from "next/server";
import { BACKEND_BASE, SESSION_COOKIE, getSessionToken } from "@/lib/auth-session";

export async function POST() {
  const token = await getSessionToken();

  if (token) {
    await fetch(`${BACKEND_BASE}/auth/logout`, {
      method: "POST",
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).catch(() => null);
  }

  const response = NextResponse.json({ success: true });
  response.cookies.delete(SESSION_COOKIE);
  return response;
}
