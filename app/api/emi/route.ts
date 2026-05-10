import { proxyBackend } from "@/lib/backend-proxy";

export async function GET() {
  return proxyBackend("/emi/");
}

export async function POST(request: Request) {
  return proxyBackend("/emi/", {
    method: "POST",
    contentType: "application/json",
    body: await request.text(),
  });
}


