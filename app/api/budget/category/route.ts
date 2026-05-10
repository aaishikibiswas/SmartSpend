import { proxyBackend } from "@/lib/backend-proxy";

export async function GET() {
  return proxyBackend("/budget/category");
}

export async function POST(request: Request) {
  return proxyBackend("/budget/category", {
    method: "POST",
    contentType: "application/json",
    body: await request.text(),
  });
}

