import { proxyBackend } from "@/lib/backend-proxy";

export async function GET() {
  const res = await proxyBackend("/auth/me");
  
  // If proxy returns a failure (e.g. backend down), return demo profile for GET
  if (res.status >= 400 && res.status !== 401) {
    return NextResponse.json({ 
      id: 1, 
      full_name: "Demo User", 
      email: "demo@smartspend.ai",
      plan: "Pro Plan (Local Fallback)"
    });
  }
  
  return res;
}

export async function PUT(request: Request) {
  return proxyBackend("/auth/me", {
    method: "PUT",
    contentType: "application/json",
    body: await request.text(),
  });
}
