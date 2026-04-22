"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, Landmark, Lightbulb, Shield, TrendingUp } from "lucide-react";
import { type DashboardMetrics, type GoalSuggestion } from "@/lib/api-client";

function formatCurrency(value: number) {
  return `Rs${Math.round(value).toLocaleString()}`;
}

type AdviceCard = {
  title: string;
  body: string;
  action: string;
  label: string;
  icon: typeof TrendingUp;
  href?: string;
};

function resolveAdviceHref(card: AdviceCard) {
  if (card.href) return card.href;

  const context = `${card.label} ${card.action} ${card.title} ${card.body}`.toLowerCase();

  if (context.includes("goal") || context.includes("investment")) return "/goals";
  if (context.includes("emergency") || context.includes("security") || context.includes("transfer")) return "/wallet";
  if (context.includes("budget") || context.includes("allowance") || context.includes("control")) return "/budget";
  if (context.includes("alert") || context.includes("risk")) return "/alerts";
  if (context.includes("forecast") || context.includes("predict") || context.includes("trend")) return "/analytics";
  if (context.includes("transaction") || context.includes("spending")) return "/transactions";

  // Always keep the CTA connected even when new advice text appears.
  return "/analytics";
}

export default function SmartAdvice({ metrics, budgetFeedback, goalSuggestion }: { metrics: DashboardMetrics; budgetFeedback: string[]; goalSuggestion: GoalSuggestion }) {
  const router = useRouter();

  const adviceCards: AdviceCard[] = [
    {
      title: `Set aside ${formatCurrency(Math.max(3000, Math.round(goalSuggestion.recommendedContribution)))} for your next goal`,
      body: goalSuggestion.message,
      action: "Setup Now",
      label: "Investment",
      icon: TrendingUp,
      href: "/goals",
    },
    {
      title: `Allocate ${formatCurrency(Math.max(10000, Math.round(metrics.netSavings * 4)))} to Emergency Fund`,
      body: `Your safety margin is currently ${Math.max(3, Math.round(metrics.savingsRatio / 8))} months. Aim for 9 months for total security.`,
      action: "Transfer Funds",
      label: "Security",
      icon: Shield,
      href: "/wallet",
    },
    {
      title: "High savings month - consider a lump sum investment",
      body: `Utilize your ${formatCurrency(metrics.netSavings)} surplus for a debt-fund top-up to avoid idle cash.`,
      action: "View Options",
      label: "Efficiency",
      icon: Landmark,
      href: "/analytics",
    },
  ];

  if (budgetFeedback[0]) {
    adviceCards[2] = {
      title: budgetFeedback[0],
      body: budgetFeedback[1] || `Your current daily allowance is ${formatCurrency(metrics.dailyAllowance)} based on active budgets.`,
      action: "View Controls",
      label: "Budgeting",
      icon: Landmark,
      href: "/budget",
    };
  }

  return (
    <section className="glass-card space-y-6 rounded-[2rem] border border-white/10 bg-[#091328]/60 p-8 backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-[#6366f1]/20 p-2 text-[#6366f1]">
            <Lightbulb className="h-5 w-5" />
          </div>
          <h3 className="text-lg font-bold text-[#dee5ff]">Smart Advice</h3>
        </div>
        <span className="rounded-full bg-[#6366f1]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-[#6366f1]">AI Generated</span>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {adviceCards.map((card) => (
          <div key={card.title} className="group flex flex-col justify-between rounded-2xl border border-[#40485d]/10 bg-[#091328]/40 p-5 transition-all hover:border-[#6366f1]/30">
            <div>
              <div className="mb-4 flex items-center justify-between">
                <card.icon className="h-4 w-4 text-[#6366f1]" />
                <span className="text-[10px] font-bold uppercase text-[#a3aac4]">{card.label}</span>
              </div>
              <p className="mb-2 text-sm font-semibold text-[#dee5ff]">{card.title}</p>
              <p className="text-[11px] text-[#a3aac4]">{card.body}</p>
            </div>
            <button
              type="button"
              onClick={() => router.push(resolveAdviceHref(card))}
              className="mt-6 flex items-center gap-1 text-[10px] font-bold text-[#6366f1] transition-all group-hover:gap-2"
            >
              {card.action}
              <ArrowRight className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
