"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Send, Sparkles, X } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { type AssistantChatMessage, type DashboardMetrics } from "@/lib/api-client";

type Message = AssistantChatMessage & {
  suggestions?: string[];
};

const STORAGE_KEY = "smartspend-ai-chat";

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

export default function AIChatbot({ metrics, floating = false }: { metrics?: DashboardMetrics; floating?: boolean }) {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const firstName = user?.full_name?.split(" ")[0] || "there";

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
        body: JSON.stringify({ message: question }),
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
          suggestions: [
            "How can I improve my savings this month?",
            "Which category am I spending the most on?",
          ],
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
            <div className="flex items-center justify-between bg-gradient-to-br from-[#a3a6ff] to-[#6063ee] p-5 font-bold text-[#0f00a4]">
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

            <div ref={scrollRef} className="custom-scrollbar flex h-[26rem] flex-col gap-5 overflow-y-auto bg-[#091328]/95 p-6">
              {visibleMessages.map((message, index) =>
                message.role === "ai" ? (
                  <div key={`${message.role}-${index}-${message.text.slice(0, 12)}`} className="rounded-3xl rounded-tl-none border border-[#40485d]/10 bg-[#141f38]/50 p-4">
                    <p className="text-xs leading-relaxed text-[#dee5ff]">{message.text}</p>
                    {message.suggestions?.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {message.suggestions.slice(0, 4).map((suggestion) => (
                          <button
                            key={suggestion}
                            type="button"
                            onClick={() => void sendMessage(suggestion)}
                            className="rounded-full bg-[#a3a6ff]/10 px-3 py-1 text-[10px] font-bold text-[#a3a6ff] transition hover:bg-[#a3a6ff]/20"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <div key={`${message.role}-${index}-${message.text.slice(0, 12)}`} className="flex flex-col items-end gap-1">
                    <div className="max-w-[88%] rounded-3xl rounded-tr-none border border-[#a3a6ff]/20 bg-[#a3a6ff]/20 p-4 text-xs text-[#dee5ff]">
                      {message.text}
                    </div>
                    <span className="mr-2 text-[9px] text-[#a3aac4]">Seen</span>
                  </div>
                ),
              )}

              {isAsking ? (
                <div className="rounded-3xl rounded-tl-none border border-[#40485d]/10 bg-[#141f38]/50 p-4">
                  <div className="flex items-center gap-2 text-xs text-[#a3aac4]">
                    <Loader2 className="h-4 w-4 animate-spin text-[#a3a6ff]" />
                    Thinking through your financial context...
                  </div>
                </div>
              ) : null}
            </div>

            <form
              className="border-t border-[#40485d]/10 bg-[#091328] p-5"
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
                  className="w-full resize-none rounded-2xl border-none bg-[#192540] py-3.5 pl-5 pr-14 text-xs text-[#dee5ff] outline-none placeholder:text-[#a3aac4]/40 focus:ring-1 focus:ring-[#a3a6ff]/50"
                />
                <button
                  type="button"
                  onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    void sendMessage();
                  }}
                  disabled={isAsking || !inputValue.trim()}
                  className="absolute bottom-3 right-3 z-10 flex h-9 w-9 items-center justify-center rounded-full text-[#a3a6ff] transition-colors hover:bg-[#a3a6ff]/10 disabled:cursor-not-allowed disabled:opacity-50"
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
          className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-[#a3a6ff] to-[#6063ee] text-[#0f00a4] shadow-2xl transition-transform hover:scale-110 active:scale-95"
        >
          <Sparkles className="h-8 w-8" />
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full border-2 border-[#060e20] bg-[#ff6e84] text-[10px] font-bold text-white">
            {Math.min(visibleMessages.filter((message) => message.role === "ai").length, 9)}
          </span>
        </button>
      </div>
    </div>
  );
}
