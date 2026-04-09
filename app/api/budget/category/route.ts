import { BACKEND_API_BASE as BACKEND_BASE } from "@/lib/backend-config";

export async function GET() {
  const response = await fetch(`${BACKEND_BASE}/budget/category`, {
    cache: "no-store",
  });

  const body = await response.text();
  return new Response(body, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}

export async function POST(request: Request) {
  const payload = await request.text();

  const response = await fetch(`${BACKEND_BASE}/budget/category`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
    cache: "no-store",
  });

  const body = await response.text();
  return new Response(body, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}

