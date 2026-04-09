import { BACKEND_API_BASE as BACKEND_BASE } from "@/lib/backend-config";

export async function POST(request: Request) {
  const formData = await request.formData();

  const response = await fetch(`${BACKEND_BASE}/upload/`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  });

  const body = await response.text();

  return new Response(body, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}

