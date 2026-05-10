import { proxyBackend } from "@/lib/backend-proxy";

export async function POST(request: Request) {
  return proxyBackend("/dashboard/smart-advice", {
    method: "POST",
    contentType: "application/json",
    body: await request.text(),
    timeoutMessage: "Failed to fetch smart advice",
  });
}
