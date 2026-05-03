import { BACKEND_API_BASE as BACKEND_BASE } from "@/lib/backend-config";

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_BASE}/dashboard/`, {
      cache: "no-store",
    });

    const body = await response.text();

    return new Response(body, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return Response.json(
      {
        status: 503,
        data: null,
        message: "Dashboard backend unavailable",
      },
      { status: 503 },
    );
  }
}

