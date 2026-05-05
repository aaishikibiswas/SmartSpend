import { BACKEND_API_BASE as BACKEND_BASE } from "@/lib/backend-config";

export async function POST(request: Request) {
  let timeout: ReturnType<typeof setTimeout> | undefined;
  try {
    const body = await request.json().catch(() => ({}));
    const controller = new AbortController();
    // INCREASED TIMEOUT: From 20s to 60s for heavy ML models
    timeout = setTimeout(() => controller.abort(), 60000);

    const response = await fetch(`${BACKEND_BASE}/predict/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: controller.signal,
    });

    if (!response.ok) {
      return Response.json({ error: "Prediction failed" }, { status: response.status });
    }

    const data = await response.json().catch(() => null);
    if (!data) {
      return Response.json({ error: "Prediction failed" }, { status: 502 });
    }

    return Response.json(data);
  } catch (error) {
    console.error("Predict API error:", error);
    if (error instanceof Error && error.name === "AbortError") {
      return Response.json({ error: "Prediction timed out" }, { status: 504 });
    }
    return Response.json({ error: "Prediction service unavailable" }, { status: 503 });
  } finally {
    if (timeout) {
      clearTimeout(timeout);
    }
  }
}
