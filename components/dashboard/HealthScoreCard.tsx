type CreditScoreSummary = {
  score: number;
  category: string;
};

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

  return (
    <section className="glass-card flex flex-col items-center rounded-[2rem] p-8 text-center">
      <h4 className="mb-6 w-full text-left text-lg font-bold text-[#dee5ff]">Financial Health Score</h4>

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
            {clampedScore >= 75 ? "Excellent" : clampedScore >= 55 ? "Stable" : "Needs Focus"}
          </span>
        </div>
      </div>

      {creditScore ? (
        <div className="mt-6 w-full rounded-[1.7rem] border border-white/6 bg-[linear-gradient(180deg,rgba(20,31,56,0.82),rgba(14,22,40,0.9))] px-5 py-4 shadow-[0_14px_40px_rgba(37,59,124,0.18)]">
          <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-[#95a0c7]">Credit Score</p>
          <div className="mt-3 flex items-center justify-between gap-4">
            <div className="min-w-0">
              <p className="text-3xl font-extrabold text-[#ebefff]">{creditScore.score}</p>
              <p className="mt-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#9ea8ff]">{creditScore.category}</p>
            </div>
            <div className="h-12 w-12 rounded-full border border-[#7c88ff]/25 bg-[radial-gradient(circle_at_top,rgba(157,178,255,0.45),rgba(122,101,255,0.14)_58%,rgba(13,21,39,0.3)_100%)] shadow-[0_0_24px_rgba(122,101,255,0.28)]" />
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-[#8e9bbb]">
            Based on system-generated financial behavior. Not an official credit score.
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
