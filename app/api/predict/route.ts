import { proxyBackend } from "@/lib/backend-proxy";

export async function POST(request: Request) {
  return proxyBackend("/predict/", {
    method: "POST",
    contentType: "application/json",
    body: JSON.stringify(await request.json().catch(() => ({}))),
    timeoutMessage: "Prediction service unavailable",
  });
}
