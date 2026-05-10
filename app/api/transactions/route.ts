import { proxyBackend } from "@/lib/backend-proxy";

export async function POST(request: Request) {
  return proxyBackend("/transactions/", {
    method: "POST",
    contentType: "application/json",
    body: await request.text(),
    timeoutMessage: "Transaction service temporarily unavailable. Please retry in a few seconds.",
  });
}

