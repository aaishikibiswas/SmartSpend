import Link from "next/link";
import { ArrowRight, BarChart3, BrainCircuit, Sparkles } from "lucide-react";

const cards = [
  {
    title: "Spending intelligence",
    description: "Trace category spikes, identify duplicate payments, and compare imported statements over time.",
    icon: BarChart3,
  },
  {
    title: "Forecast insights",
    description: "Use the Prophet and regression outputs together to understand the next likely expense window.",
    icon: BrainCircuit,
  },
  {
    title: "AI recommendations",
    description: "Turn alerts and budget pressure into actionable savings nudges for the user.",
    icon: Sparkles,
  },
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#7D8AB5]">Analytics Workspace</p>
        <h1 className="mt-2 text-3xl font-bold text-white">Advanced financial analytics</h1>
        <p className="mt-3 max-w-2xl text-sm text-[#93A1C7]">
          This space is ready for deeper views like trend decomposition, recurring spend clusters, and what-if simulations driven by uploaded statements.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {cards.map((card) => (
          <div key={card.title} className="glass-card panel-shell p-6">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#8B5CF6]/10 text-[#b89cff]">
              <card.icon className="h-5 w-5" />
            </div>
            <h2 className="mt-5 text-lg font-semibold text-white">{card.title}</h2>
            <p className="mt-3 text-sm leading-7 text-[#93A1C7]">{card.description}</p>
          </div>
        ))}
      </div>

      <div className="glass-card panel-shell flex flex-col items-start gap-4 p-6 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Return to the main dashboard</h2>
          <p className="mt-2 text-sm text-[#93A1C7]">The core widgets on the dashboard remain connected to your uploaded live statement data.</p>
        </div>
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-[#8B5CF6] to-[#6D7CFF] px-5 py-3 text-sm font-semibold text-white"
        >
          Open Dashboard
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
