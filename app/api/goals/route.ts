import { proxyBackend } from "@/lib/backend-proxy";

export async function GET() {
  return proxyBackend("/goals/");
}

export async function POST(request: Request) {
  return proxyBackend("/goals/", {
    method: "POST",
    contentType: "application/json",
    body: await request.text(),
  });
}

