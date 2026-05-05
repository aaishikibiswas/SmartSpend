import { BACKEND_API_BASE as BACKEND_BASE } from "@/lib/backend-config";

export async function POST(request: Request) {
  try {
    const payload = await request.text();

    console.log("Smart Advice API called (Proxy)");

    const response = await fetch(`${BACKEND_BASE}/dashboard/smart-advice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload,
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status ${response.status}`);
    }

    const body = await response.text();
    console.log("Smart Advice API Response received");

    return new Response(body, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Smart Advice API Proxy Error:", error);
    return new Response(JSON.stringify({ error: "Failed to fetch smart advice" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
