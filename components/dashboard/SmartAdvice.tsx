import Link from "next/link";
import { ArrowRight, Landmark, Lightbulb, Shield, TrendingUp } from "lucide-react";

export default function SmartAdvice({ adviceItems }: { adviceItems: any[] }) {
  const getIcon = (name: string) => {
    switch (name) {
      case "shield":
        return Shield;
      case "trending-up":
        return TrendingUp;
      case "landmark":
        return Landmark;
      default:
        return Lightbulb;
    }
  };

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
        {adviceItems.map((card, idx) => {
          const Icon = getIcon(card.icon);
          return (
            <div key={idx} className="group flex flex-col justify-between rounded-2xl border border-[#40485d]/10 bg-[#091328]/40 p-5 transition-all hover:border-[#6366f1]/30">
              <div>
                <div className="mb-4 flex items-center justify-between">
                  <Icon className="h-4 w-4 text-[#6366f1]" />
                  <span className="text-[10px] font-bold uppercase text-[#a3aac4]">{card.label}</span>
                </div>
                <p className="mb-2 text-sm font-semibold text-[#dee5ff]">{card.title}</p>
                <p className="text-[11px] text-[#a3aac4]">{card.body}</p>
              </div>
              <Link href={card.href} className="mt-6 flex items-center gap-1 text-[10px] font-bold text-[#6366f1] transition-all group-hover:gap-2">
                {card.action}
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          );
        })}
      </div>
    </section>
  );
}
