"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Send, Sparkles, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "@/components/auth/AuthProvider";
import {
  type AssistantChatMessage,
  type BudgetSnapshot,
  type CashflowData,
  type CategoryBreakdownItem,
  type DashboardMetrics,
  type EmiSummary,
  type GoalSuggestion,
  type TransactionItem,
  type SubscriptionItem,
} from "@/lib/api-client";

type Message = AssistantChatMessage & {
  suggestions?: string[];
};

const STORAGE_KEY = "smartspend-ai-chat";
const OPEN_STATE_KEY = "smartspend-ai-chat-open";

function initialGreeting(name: string) {
  return {
    role: "ai" as const,
    text: `Hi ${name}! I can reason from your uploaded transactions, budgets, alerts, recurring payments, goals, and forecasts. Ask me naturally, and I will answer from your actual SmartSpend data.`,
    suggestions: [
      "How can I improve my savings this month?",
      "Which category am I spending the most on?",
      "What recurring payments should I review?",
      "Do I have any budget alerts right now?",
    ],
  };
}

export default function AIChatbot({
  metrics,
  categoryBreakdown,
  subscriptions,
  emi,
  cashflow,
  goalSuggestion,
  budgeting,
  recentTransactions,
  floating = false,
}: {
  metrics?: DashboardMetrics;
  categoryBreakdown?: CategoryBreakdownItem[];
  subscriptions?: SubscriptionItem[];
  emi?: EmiSummary;
  cashflow?: CashflowData;
  goalSuggestion?: GoalSuggestion;
  budgeting?: BudgetSnapshot;
  recentTransactions?: TransactionItem[];
  floating?: boolean;
}) {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const firstName = user?.full_name?.split(" ")[0] || "there";

  useEffect(() => {
    const saved = window.localStorage.getItem(OPEN_STATE_KEY);
    if (saved === "1") {
      setIsOpen(true);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem(OPEN_STATE_KEY, isOpen ? "1" : "0");
  }, [isOpen]);

  useEffect(() => {
    try {
      const stored = window.sessionStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as Message[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
          return;
        }
      }
    } catch (error) {
      console.error("Failed to restore assistant chat", error);
    }

    setMessages([initialGreeting(firstName)]);
  }, [firstName]);

  useEffect(() => {
    if (messages.length === 0) return;
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    const node = scrollRef.current;
    if (!node) return;
    node.scrollTop = node.scrollHeight;
  }, [messages, isAsking]);

  const visibleMessages = useMemo(() => (messages.length > 0 ? messages : [initialGreeting(firstName)]), [messages, firstName]);
  const aiMessageCount = useMemo(() => Math.min(visibleMessages.filter((message) => message.role === "ai").length, 9), [visibleMessages]);
  const recentTransactionContext = useMemo(
    () =>
      (recentTransactions ?? []).slice(0, 8).map((tx) => ({
        merchant: tx.merchant,
        category: tx.category,
        amount: tx.amount,
        type: tx.type,
        date: tx.date,
        source: tx.source || "uploaded",
      })),
    [recentTransactions],
  );

  const sendMessage = async (questionOverride?: string) => {
    const question = (questionOverride ?? inputValue).trim();
    if (!question || isAsking) return;

    const optimisticUserMessage: Message = { role: "user", text: question };

    setMessages((current) => [...(current.length > 0 ? current : [initialGreeting(firstName)]), optimisticUserMessage]);
    setInputValue("");
    setIsAsking(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          contextData: {
            income: metrics?.totalIncome ?? 0,
            expenses: metrics?.totalExpense ?? 0,
            categoryBreakdown: categoryBreakdown ?? [],
            subscriptions: subscriptions ?? [],
            emi: emi?.items ?? [],
            alerts: budgeting?.feedback ?? [],
            goals: goalSuggestion ? [goalSuggestion] : [],
            cashflow: cashflow ?? { upcoming_payments: [], monthly_outflow_projection: 0 },
            recentTransactions: recentTransactionContext,
          },
        }),
      });
      const data = (await res.json().catch(() => ({}))) as { reply?: string };
      const reply = data.reply || "No response";
      setMessages((current) => [
        ...current,
        {
          role: "ai",
          text: reply,
          suggestions: [
            "How can I improve my savings this month?",
            "Which category am I spending the most on?",
            "What recurring payments should I review?",
            "Do I have any budget alerts right now?",
          ],
        },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((current) => [
        ...current,
        {
          role: "ai",
          text: error instanceof Error ? error.message : "I couldn't read your latest financial context just now.",
          suggestions: ["How can I improve my savings this month?", "Which category am I spending the most on?"],
        },
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  if (!floating) return null;

  return (
    <div className="fixed bottom-8 right-8 z-[100]">
      <div className="relative group">
        {isOpen ? (
          <div className="glass-card absolute bottom-20 right-0 mb-4 flex w-[25rem] origin-bottom-right flex-col overflow-hidden rounded-[2.5rem] shadow-2xl">
            <div className="flex items-center justify-between bg-gradient-to-br from-[#A897FF] to-[#6063ee] p-5 font-bold text-[#0f00a4]">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/20">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm leading-none">SmartSpend AI Assistant</p>
                  <p className="mt-1 text-[10px] opacity-80">Referencing: Rs{metrics?.totalIncome || 0} Income | Rs{metrics?.totalExpense || 0} Spend</p>
                </div>
              </div>
              <button type="button" onClick={() => setIsOpen(false)} aria-label="Close assistant">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div ref={scrollRef} className="custom-scrollbar flex h-[26rem] flex-col gap-5 overflow-y-auto bg-[#10182E]/95 p-6">
              {visibleMessages.map((message, index) =>
                message.role === "ai" ? (
                  <div key={`${message.role}-${index}-${message.text.slice(0, 12)}`} className="rounded-3xl rounded-tl-none border border-[rgba(255,255,255,0.05)]/10 bg-[#10182E]/50 p-4">
                    <div className="text-xs leading-relaxed text-[#F4F6FF]">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
                          h3: ({node, ...props}) => <h3 className="text-sm font-bold text-[#A897FF] mt-3 mb-1" {...props} />,
                          h4: ({node, ...props}) => <h4 className="text-xs font-bold text-[#A897FF] mt-2 mb-1" {...props} />,
                          ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2" {...props} />,
                          ol: ({node, ...props}) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                          li: ({node, ...props}) => <li className="mb-1" {...props} />,
                          strong: ({node, ...props}) => <strong className="font-bold text-white" {...props} />,
                          a: ({node, ...props}) => <a className="text-[#A897FF] hover:underline" {...props} />,
                        }}
                      >
                        {message.text}
                      </ReactMarkdown>
                    </div>
                    {message.suggestions?.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {message.suggestions.slice(0, 4).map((suggestion) => (
                          <button
                            key={suggestion}
                            type="button"
                            onClick={() => void sendMessage(suggestion)}
                            className="rounded-full bg-[#A897FF]/10 px-3 py-1 text-[10px] font-bold text-[#A897FF] transition hover:bg-[#A897FF]/20"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <div key={`${message.role}-${index}-${message.text.slice(0, 12)}`} className="flex flex-col items-end gap-1">
                    <div className="max-w-[88%] rounded-3xl rounded-tr-none border border-[#A897FF]/20 bg-[#A897FF]/20 p-4 text-xs text-[#F4F6FF]">{message.text}</div>
                    <span className="mr-2 text-[9px] text-[#B7BDD9]">Seen</span>
                  </div>
                ),
              )}

              {isAsking ? (
                <div className="rounded-3xl rounded-tl-none border border-[rgba(255,255,255,0.05)]/10 bg-[#10182E]/50 p-4">
                  <div className="flex items-center gap-2 text-xs text-[#B7BDD9]">
                    <Loader2 className="h-4 w-4 animate-spin text-[#A897FF]" />
                    Thinking through your financial context...
                  </div>
                </div>
              ) : null}
            </div>

            <form
              className="border-t border-[rgba(255,255,255,0.05)]/10 bg-[#10182E] p-5"
              onSubmit={(event) => {
                event.preventDefault();
                event.stopPropagation();
                void sendMessage();
              }}
            >
              <div className="relative">
                <textarea
                  value={inputValue}
                  onClick={(event) => event.stopPropagation()}
                  onChange={(event) => setInputValue(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      void sendMessage();
                    }
                  }}
                  rows={2}
                  placeholder="Ask AI about your finances..."
                  className="w-full resize-none rounded-2xl border-none bg-[#10182E] py-3.5 pl-5 pr-14 text-xs text-[#F4F6FF] outline-none placeholder:text-[#B7BDD9]/40 focus:ring-1 focus:ring-[#A897FF]/50"
                />
                <button
                  type="button"
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    void sendMessage();
                  }}
                  disabled={isAsking || !inputValue.trim()}
                  className="absolute bottom-3 right-3 z-10 flex h-9 w-9 items-center justify-center rounded-full text-[#A897FF] transition-colors hover:bg-[#A897FF]/10 disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label="Send message"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </form>
          </div>
        ) : null}

        <button
          type="button"
          onClick={() => setIsOpen((value) => !value)}
          className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-[#A897FF] to-[#6063ee] text-[#0f00a4] shadow-2xl transition-transform hover:scale-110 active:scale-95"
        >
          <Sparkles className="h-8 w-8" />
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full border-2 border-[#050816] bg-[#ff6e84] text-[10px] font-bold text-white">
            {aiMessageCount}
          </span>
        </button>
      </div>
    </div>
  );
}
