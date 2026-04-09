import { BACKEND_API_BASE as BACKEND_BASE } from "@/lib/backend-config";

export async function GET() {
  const response = await fetch(`${BACKEND_BASE}/expense-split/`, {
    cache: "no-store",
  });
  const body = await response.text();
  return new Response(body, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}


