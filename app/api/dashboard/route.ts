import { proxyBackend } from "@/lib/backend-proxy";

export async function GET() {
  return proxyBackend("/dashboard/", { timeoutMessage: "Dashboard backend unavailable" });
}

