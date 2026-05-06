import { getCreditScoreSlab, getFinancialHealthSlab } from "@/lib/financial-scoring";

type CreditScoreSummary = {
  score: number;
  category: string;
};

function slabTone(tone: string) {
  if (tone === "strong") return "border-[#76e4b3]/20 bg-[#15342c]/55 text-[#9ff0c7]";
  if (tone === "steady") return "border-[#8fa7ff]/20 bg-[#152345]/60 text-[#aebdff]";
  if (tone === "watch") return "border-[#ffd166]/20 bg-[#3a2f16]/50 text-[#ffd986]";
  return "border-[#ff8ca8]/25 bg-[#3a1724]/55 text-[#ffabc0]";
}

export default function HealthScoreCard({
  score,
  savingsRatio,
  creditScore,
}: {
  score: number;
  savingsRatio: number;
  creditScore?: CreditScoreSummary;
}) {
  const clampedScore = Math.max(0, Math.min(100, Math.round(score)));
  const circumference = 2 * Math.PI * 90;
  const dashOffset = circumference - (clampedScore / 100) * circumference;
  const safetyMonths = Math.max(2.5, Number((savingsRatio / 8).toFixed(1)));
  const healthSlab = getFinancialHealthSlab(clampedScore);
  const creditSlab = creditScore ? getCreditScoreSlab(creditScore.score) : null;

  return (
    <section className="glass-card flex flex-col items-center rounded-[2rem] p-8 text-center">
      <div className="mb-6 flex w-full items-start justify-between gap-4 text-left">
        <div>
          <h4 className="text-lg font-bold text-[#dee5ff]">Financial Health Score</h4>
          <p className="mt-1 text-xs font-semibold text-[#96a4c7]">Live from synced user transactions</p>
        </div>
        <span className={`shrink-0 rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${slabTone(healthSlab.tone)}`}>
          {healthSlab.label}
        </span>
      </div>

      <div className="relative flex h-56 w-56 items-center justify-center">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 224 224">
          <circle cx="112" cy="112" r="90" fill="transparent" stroke="currentColor" strokeWidth="14" className="text-[#141f38]" />
          <circle
            cx="112"
            cy="112"
            r="90"
            fill="transparent"
            stroke="currentColor"
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className="text-[#a3a6ff]"
            style={{ filter: "drop-shadow(0 0 8px rgba(163,166,255,0.4))" }}
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-5xl font-extrabold text-[#dee5ff]">{clampedScore}</span>
          <span className="mt-1 text-xs font-bold uppercase tracking-widest text-[#a3aac4]">
            {healthSlab.range}
          </span>
        </div>
      </div>

      <div className="mt-6 w-full rounded-[1.5rem] border border-white/6 bg-[#121a34]/70 p-4 text-left">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#95a0c7]">Health Score Slab</p>
            <p className="mt-2 text-base font-extrabold text-[#ebefff]">{healthSlab.label}</p>
          </div>
          <span className="rounded-full bg-[#0f1730]/80 px-3 py-1 text-xs font-bold text-[#a3a6ff]">{healthSlab.range}</span>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-[#9aa6c6]">{healthSlab.summary}</p>
      </div>

      {creditScore ? (
        <div className="mt-6 w-full rounded-[1.7rem] border border-white/6 bg-[linear-gradient(180deg,rgba(20,31,56,0.82),rgba(14,22,40,0.9))] px-5 py-4 shadow-[0_14px_40px_rgba(37,59,124,0.18)]">
          <div className="flex items-center justify-between gap-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-[#95a0c7]">Credit Score</p>
            {creditSlab ? <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${slabTone(creditSlab.tone)}`}>{creditSlab.label}</span> : null}
          </div>
          <div className="mt-3 flex items-center justify-between gap-4">
            <div className="min-w-0">
              <p className="text-3xl font-extrabold text-[#ebefff]">{creditScore.score}</p>
              <p className="mt-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#9ea8ff]">{creditSlab?.range || creditScore.category}</p>
            </div>
            <div className="h-12 w-12 rounded-full border border-[#7c88ff]/25 bg-[radial-gradient(circle_at_top,rgba(157,178,255,0.45),rgba(122,101,255,0.14)_58%,rgba(13,21,39,0.3)_100%)] shadow-[0_0_24px_rgba(122,101,255,0.28)]" />
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-[#8e9bbb]">
            {creditSlab?.summary || "Based on synced financial behavior."} Not an official credit score.
          </p>
        </div>
      ) : null}

      <div className="mt-8 grid w-full grid-cols-2 gap-4">
        <div className="rounded-2xl border border-[#40485d]/10 bg-[#141f38]/30 p-3">
          <p className="text-[10px] font-bold uppercase text-[#a3aac4]">Sustainability</p>
          <p className="text-sm font-bold text-[#a3a6ff]">{clampedScore >= 75 ? "High" : clampedScore >= 55 ? "Medium" : "Low"}</p>
        </div>
        <div className="rounded-2xl border border-[#40485d]/10 bg-[#141f38]/30 p-3">
          <p className="text-[10px] font-bold uppercase text-[#a3aac4]">Safety Margin</p>
          <p className="text-sm font-bold text-[#a88cfb]">{safetyMonths} mos</p>
        </div>
      </div>
    </section>
  );
}
