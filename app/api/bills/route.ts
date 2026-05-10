import { proxyBackend } from "@/lib/backend-proxy";

export async function GET() {
  return proxyBackend("/bills/");
}

export async function POST(request: Request) {
  return proxyBackend("/bills/", {
    method: "POST",
    contentType: "application/json",
    body: await request.text(),
  });
}

