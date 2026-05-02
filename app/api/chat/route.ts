export async function POST(request: Request) {
  const { message } = (await request.json().catch(() => ({}))) as { message?: string };
  const userMessage = String(message || "").trim();

  console.log("API KEY EXISTS:", !!process.env.OPENROUTER_API_KEY);

  if (!userMessage) {
    return Response.json({ reply: "AI error: Message is required" }, { status: 400 });
  }

  if (!process.env.OPENROUTER_API_KEY) {
    return Response.json({ reply: "AI error: Missing OPENROUTER_API_KEY" }, { status: 500 });
  }

  try {
    const headers = {
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
      "Content-Type": "application/json",
    };
    const messages = [
      { role: "system", content: "You are a helpful financial assistant." },
      { role: "user", content: userMessage },
    ];

    const tryModel = async (model: string) => {
      const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers,
        body: JSON.stringify({ model, messages }),
      });
      const data = await response.json().catch(() => ({}));
      return { response, data };
    };

    let { response, data } = await tryModel("mistralai/mistral-7b-instruct");
    if (!response.ok) {
      console.error("OpenRouter Primary Error:", data);
      const primaryMessage = (data as { error?: { message?: string } })?.error?.message || "";
      const shouldFallback =
        response.status >= 500 ||
        /no endpoints found|model.*not.*found|unavailable/i.test(primaryMessage);

      if (shouldFallback) {
        const fallback = await tryModel("meta-llama/llama-3-8b-instruct");
        response = fallback.response;
        data = fallback.data;
      }
    }

    if (!response.ok) {
      console.error("OpenRouter Error:", data);
      return Response.json({
        reply: "AI error: " + ((data as { error?: { message?: string } })?.error?.message || "Unknown error"),
      });
    }

    return Response.json({
      reply: (data as { choices?: Array<{ message?: { content?: string } }> })?.choices?.[0]?.message?.content || "No response",
    });
  } catch (error) {
    console.error("Chat API failure:", error);
    return Response.json({ reply: "AI error: Request failed" }, { status: 500 });
  }
}
