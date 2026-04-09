import "server-only";

function trimTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}

const fallbackApiBase = "http://127.0.0.1:8001";

export const BACKEND_API_BASE = trimTrailingSlash(
  process.env.BACKEND_API_BASE || process.env.NEXT_PUBLIC_BACKEND_API_BASE || fallbackApiBase,
);

const configuredWsBase =
  process.env.NEXT_PUBLIC_BACKEND_WS_BASE ||
  process.env.BACKEND_WS_BASE ||
  BACKEND_API_BASE.replace(/^http:/, "ws:").replace(/^https:/, "wss:");

export const BACKEND_WS_BASE = trimTrailingSlash(configuredWsBase);
export const APP_URL = trimTrailingSlash(
  process.env.NEXT_PUBLIC_APP_URL || process.env.APP_URL || "http://127.0.0.1:3001",
);

export function shouldUseSecureCookies() {
  return APP_URL.startsWith("https://");
}
