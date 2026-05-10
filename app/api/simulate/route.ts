import { proxyBackend } from "@/lib/backend-proxy";

export async function POST(request: Request) {
  return proxyBackend("/simulate/", {
    method: "POST",
    contentType: "application/json",
    body: await request.text(),
  });
}

