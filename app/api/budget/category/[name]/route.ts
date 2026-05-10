import { proxyBackend } from "@/lib/backend-proxy";

export async function DELETE(_: Request, context: { params: Promise<{ name: string }> }) {
  const { name } = await context.params;
  return proxyBackend(`/budget/category/${encodeURIComponent(name)}`, { method: "DELETE" });
}
