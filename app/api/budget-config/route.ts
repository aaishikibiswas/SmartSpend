import { proxyBackend } from "@/lib/backend-proxy";

export async function GET() {
  return proxyBackend("/budget/snapshot");
}

export async function PUT(request: Request) {
  return proxyBackend("/budget/global", {
    method: "POST",
    contentType: "application/json",
    body: await request.text(),
  });
}

