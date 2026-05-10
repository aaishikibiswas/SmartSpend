import { proxyBackend } from "@/lib/backend-proxy";

export async function GET() {
  return proxyBackend("/subscriptions/");
}

export async function POST(request: Request) {
  return proxyBackend("/subscriptions/", {
    method: "POST",
    contentType: "application/json",
    body: await request.text(),
  });
}


