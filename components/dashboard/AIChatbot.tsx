"use client";

import { useMemo, useState } from "react";
import { Sparkles, Send, X } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { apiClient, type DashboardMetrics } from "@/lib/api-client";

type Message = {
  role: "ai" | "user";
  text: string;
  suggestions?: string[];
};

export default function AIChatbot({ metrics, floating = false }: { metrics?: DashboardMetrics; floating?: boolean }) {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isAsking, setIsAsking] = useState(false);

  const visibleMessages = useMemo(() => {
    if (messages.length > 0) return messages;

    return [
      {
        role: "ai" as const,
        text: `Hi ${user?.full_name?.split(" ")[0] || "there"}! I can answer from your uploaded transactions, budgets, alerts, goals, bills, and forecast data.`,
        suggestions: [
          "Which category am I spending the most on?",
          "What is my next predicted expense?",
          "Do I have any budget alerts right now?",
          "What are my top 3 recent transactions?",
        ],
      },
    ];
  }, [messages, user]);

  const handleSend = async (overrideQuestion?: string) => {
    const question = (overrideQuestion ?? inputValue).trim();
    if (!question || isAsking) return;

    const nextMessages = [...visibleMessages, { role: "user" as const, text: question }];
    setMessages(nextMessages);
    setIsAsking(true);

    try {
      const response = await apiClient.askAssistant(question);
      setMessages((current) => [
        ...current,
        {
          role: "ai",
          text: response.data.answer,
          suggestions: response.data.suggestions,
        },
      ]);
    } catch (error) {
      console.error(error);
      setMessages((current) => [
        ...current,
        {
          role: "ai",
          text: error instanceof Error ? error.message : "I couldn't read your latest financial context just now.",
        },
      ]);
    } finally {
      setIsAsking(false);
    }

    setInputValue("");
  };

  if (!floating) return null;

  return (
    <div className="fixed bottom-8 right-8 z-[100]">
      <div className="relative group">
        {isOpen ? (
          <div className="glass-card absolute bottom-20 right-0 mb-4 flex w-96 origin-bottom-right flex-col overflow-hidden rounded-[2.5rem] shadow-2xl">
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
              <button type="button" onClick={() => setIsOpen(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="custom-scrollbar h-80 space-y-5 overflow-y-auto bg-[#091328]/95 p-6">
              {visibleMessages.map((message, index) =>
                message.role === "ai" ? (
                  <div key={index} className="rounded-3xl rounded-tl-none border border-[#40485d]/10 bg-[#141f38]/50 p-4">
                    <p className="text-xs leading-relaxed text-[#dee5ff]">{message.text}</p>
                    {message.suggestions?.length ? (
                      <div className="mt-3 flex gap-2">
                        {message.suggestions.slice(0, 2).map((suggestion) => (
                          <button
                            key={suggestion}
                            type="button"
                            onClick={() => void handleSend(suggestion)}
                            className="rounded-full bg-[#a3a6ff]/10 px-3 py-1 text-[10px] font-bold text-[#a3a6ff]"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <div key={index} className="flex flex-col items-end gap-1">
                    <div className="max-w-[85%] rounded-3xl rounded-tr-none border border-[#a3a6ff]/20 bg-[#a3a6ff]/20 p-4 text-xs text-[#dee5ff]">
                      {message.text}
                    </div>
                    <span className="mr-2 text-[9px] text-[#a3aac4]">Seen</span>
                  </div>
                ),
              )}
            </div>

            <div className="border-t border-[#40485d]/10 bg-[#091328] p-5">
              <div className="relative">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(event) => setInputValue(event.target.value)}
                  onKeyDown={(event) => event.key === "Enter" && handleSend()}
                  placeholder="Ask AI about your finances..."
                  className="w-full rounded-2xl border-none bg-[#192540] py-3.5 pl-5 pr-12 text-xs text-[#dee5ff] outline-none placeholder:text-[#a3aac4]/40 focus:ring-1 focus:ring-[#a3a6ff]/50"
                />
                <button
                  type="button"
                  onClick={() => void handleSend()}
                  disabled={isAsking}
                  className="absolute right-3 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-[#a3a6ff] transition-colors hover:bg-[#a3a6ff]/10 disabled:opacity-50"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ) : null}

        <button
          type="button"
          onClick={() => setIsOpen((value) => !value)}
          className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-[#a3a6ff] to-[#6063ee] text-[#0f00a4] shadow-2xl transition-transform hover:scale-110 active:scale-95"
        >
          <Sparkles className="h-8 w-8" />
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full border-2 border-[#060e20] bg-[#ff6e84] text-[10px] font-bold text-white">
            2
          </span>
        </button>
      </div>
    </div>
  );
}
