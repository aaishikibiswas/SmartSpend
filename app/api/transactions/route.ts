import { BACKEND_API_BASE as BACKEND_BASE } from "@/lib/backend-config";

export async function POST(request: Request) {
  const payload = await request.text();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${BACKEND_BASE}/transactions/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
      cache: "no-store",
      signal: controller.signal,
    });

    const body = await response.text();

    return new Response(body, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Fetch to backend failed:", error);
    return Response.json(
      {
        status: 503,
        data: null,
        message: "Transaction service temporarily unavailable. Please retry in a few seconds.",
      },
      { status: 503 },
    );
  } finally {
    clearTimeout(timeout);
  }
}

