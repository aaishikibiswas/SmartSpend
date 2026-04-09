import { BACKEND_API_BASE as BACKEND_BASE } from "@/lib/backend-config";

export async function DELETE(_: Request, { params }: { params: Promise<{ identifier: string }> }) {
  const { identifier } = await params;
  const response = await fetch(`${BACKEND_BASE}/bills/${encodeURIComponent(identifier)}`, {
    method: "DELETE",
    cache: "no-store",
  });
  const body = await response.text();
  return new Response(body, {
    status: response.status,
    headers: { "Content-Type": "application/json" },
  });
}
