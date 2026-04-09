import "server-only";

import { cookies } from "next/headers";
import type { AuthUser } from "@/lib/auth-types";
import { BACKEND_API_BASE } from "@/lib/backend-config";

export const SESSION_COOKIE = "smartspend_session";
export const BACKEND_BASE = BACKEND_API_BASE;

export async function getSessionToken() {
  return (await cookies()).get(SESSION_COOKIE)?.value || "";
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  const token = await getSessionToken();
  if (!token) return null;

  try {
    const response = await fetch(`${BACKEND_BASE}/auth/me`, {
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) return null;
    const payload = await response.json();
    return payload.data as AuthUser;
  } catch {
    return null;
  }
}
