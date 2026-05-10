import { proxyBackend } from "@/lib/backend-proxy";

export async function DELETE(_: Request, { params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  return proxyBackend(`/subscriptions/${encodeURIComponent(name)}`, { method: "DELETE" });
}
