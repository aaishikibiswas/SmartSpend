import { getSessionToken } from "@/lib/auth-session";

export async function POST(request: Request) {
  const token = await getSessionToken();
  if (!token) {
    return Response.json({ reply: "Authentication required" }, { status: 401 });
  }

  const { message, contextData } = (await request.json().catch(() => ({}))) as {
    message?: string;
    contextData?: {
      income?: number;
      expenses?: number;
      categoryBreakdown?: Array<{ name: string; amount: number }>;
      subscriptions?: Array<{ name: string; monthly_cost: number; next_due_date?: string }>;
      emi?: Array<{ name: string; monthly_emi: number; remaining_months?: number }>;
      alerts?: string[];
      goals?: Array<{ recommendedContribution?: number; message?: string }>;
      cashflow?: { monthly_outflow_projection?: number; upcoming_payments?: Array<{ name: string; amount: number; date?: string }> };
      recentTransactions?: Array<{ merchant?: string; category?: string; amount?: number; type?: string; date?: string; source?: string }>;
    };
  };

  const userMessage = String(message || "").trim();

  if (!userMessage) {
    return Response.json({ reply: "AI error: Message is required" }, { status: 400 });
  }

  if (!process.env.OPENROUTER_API_KEY) {
    return Response.json({ reply: "AI error: Missing OPENROUTER_API_KEY" }, { status: 500 });
  }

  try {
    const lower = userMessage.toLowerCase();
    const hasData = Boolean(contextData && Object.keys(contextData).length > 0);
    const isUiQuestion = /(how to use|where is|how to add|navigation|how do i use|what does this do|where can i find|how to open|location)/i.test(lower);
    const isFinanceQuestion = /(saving|save|spending|spend|budget|goal|goals|alert|alerts|subscription|emi|cash flow|expense)/i.test(lower);
    const isGeneralFinance = /(investment tips|how to budget|how to save money|general saving tips|finance tips|general advice|saving tips|money tips)/i.test(lower);
    const isChartQuestion = /(chart|graph|trend|anomal|split|timeline|dashboard)/i.test(lower);

    const decisionMode = isUiQuestion
      ? "ui_guide"
      : isFinanceQuestion && hasData
        ? "data_advice"
        : isGeneralFinance
          ? "general_finance"
          : isChartQuestion
            ? "insight_explainer"
            : "mixed";

    const headers = {
      Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
      "Content-Type": "application/json",
    };

    const messages = [
      {
        role: "system",
        content: `You are SmartSpend AI - an intelligent assistant inside a financial dashboard.

You have FIVE roles:
ROLE 1 PRODUCT GUIDE. For UI/navigation questions, give step-by-step app instructions.
ROLE 2 DATA-DRIVEN FINANCE ADVISOR. For spending/savings/budget/goals/alerts, use user data first.
ROLE 3 GENERAL FINANCE ADVISOR. For general finance questions, give short practical guidance.
ROLE 4 PROACTIVE ASSISTANT. Add one useful next action tied to this app.
ROLE 5 INSIGHT EXPLAINER. Explain chart meaning and what to do next.

APP STRUCTURE:
Sidebar:
- Dashboard
- Transactions
- Wallet
- Goals
- Budget
- Analytics
- Alerts
- Simulator

Dashboard:
- Left: Transaction History
- Bottom left: Recurring Payments & EMI

Right column:
- Financial Priority Engine
- Financial Goals
- Cash Flow Timeline
- Expense Split

DECISION LOGIC:
IF UI question then navigation steps.
IF finance plus data exists then data-based answer.
IF general finance question then general advice plus app linkage.
IF mixed then combine.

MODE FOR THIS REQUEST:
${decisionMode}

USER DATA:
${JSON.stringify(contextData || {})}

RESPONSE FORMAT RULES:
- Format your responses beautifully using Markdown.
- ALWAYS use clear headings (###), bulleted/numbered lists, and **bold text** for key metrics.
- Keep concise and personal-finance focused.
- Never respond in a single long paragraph. Ensure an organized, industry-level professional chatbot experience.`,
      },
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

    let { response, data } = await tryModel("meta-llama/llama-3-8b-instruct");
    if (!response.ok) {
      const primaryMessage = (data as { error?: { message?: string } })?.error?.message || "";
      const shouldFallback = response.status >= 500 || /no endpoints found|model.*not.*found|unavailable/i.test(primaryMessage);
      if (shouldFallback) {
        const fallback = await tryModel("mistralai/mistral-7b-instruct");
        response = fallback.response;
        data = fallback.data;
      }
    }

    if (!response.ok) {
      return Response.json({
        reply: "AI error: " + ((data as { error?: { message?: string } })?.error?.message || "Unknown error"),
      });
    }

    const rawReply = (data as { choices?: Array<{ message?: { content?: string } }> })?.choices?.[0]?.message?.content || "No response";

    return Response.json({
      reply: rawReply || "Insight:\n1. I could not generate a data-based response right now.\nSuggestion:\n1. Try asking about spending, goals, or alerts.",
    });
  } catch (error) {
    console.error("Chat API failure:", error);
    return Response.json({ reply: "AI error: Request failed" }, { status: 500 });
  }
}
