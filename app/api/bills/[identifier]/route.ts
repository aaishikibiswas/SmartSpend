import { proxyBackend } from "@/lib/backend-proxy";

export async function DELETE(_: Request, { params }: { params: Promise<{ identifier: string }> }) {
  const { identifier } = await params;
  return proxyBackend(`/bills/${encodeURIComponent(identifier)}`, { method: "DELETE" });
}
