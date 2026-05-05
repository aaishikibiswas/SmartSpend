import "server-only";

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}

const fallbackApiBase = "http://127.0.0.1:8001";

const rawBackendBase = trimTrailingSlash(
  process.env.BACKEND_API_BASE || process.env.NEXT_PUBLIC_BACKEND_API_BASE || fallbackApiBase,
);

export const BACKEND_API_BASE = rawBackendBase.endsWith("/api") ? rawBackendBase : `${rawBackendBase}/api`;

const configuredWsBase =
  process.env.NEXT_PUBLIC_BACKEND_WS_BASE ||
  process.env.BACKEND_WS_BASE ||
  rawBackendBase.replace(/\/api$/, "").replace(/^http:/, "ws:").replace(/^https:/, "wss:");

export const BACKEND_WS_BASE = trimTrailingSlash(configuredWsBase);
export const APP_URL = trimTrailingSlash(
  process.env.NEXT_PUBLIC_APP_URL || process.env.APP_URL || "http://127.0.0.1:3001",
);

export function shouldUseSecureCookies() {
  return APP_URL.startsWith("https://");
}
