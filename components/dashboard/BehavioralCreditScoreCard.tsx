type CreditScoreData = {
  score: number;
  category: string;
  range: {
    min: number;
    max: number;
  };
  indicators: {
    spending_stability: string;
    savings_ratio: string;
    risk_level: string;
  };
  feature_contributions: {
    savings_ratio: number;
    volatility: number;
    anomalies: number;
    expense_income_ratio: number;
  };
  suggestions: string[];
  disclaimer: string;
};

function formatContribution(value: number) {
  const rounded = Math.round(value);
  return `${rounded >= 0 ? "+" : ""}${rounded}`;
}

function contributionColor(value: number) {
  if (value > 0) return "text-[#9db2ff]";
  if (value < 0) return "text-[#ff8ca8]";
  return "text-[#a3aac4]";
}

export default function BehavioralCreditScoreCard({ creditScore }: { creditScore: CreditScoreData }) {
  const { score, category, range, indicators, feature_contributions, suggestions, disclaimer } = creditScore;
  const clampedProgress = Math.max(0, Math.min(1, (score - range.min) / (range.max - range.min)));
  const circumference = 2 * Math.PI * 90;
  const dashOffset = circumference - clampedProgress * circumference;

  return (
    <section className="glass-card rounded-[2rem] p-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h4 className="text-lg font-bold text-[#dee5ff]">Behavioral Credit Score</h4>
          <p className="mt-1 text-xs font-medium text-[#92a0c6]" title={disclaimer}>
            Behavioral estimate
          </p>
        </div>
        <span
          className="rounded-full border border-[#4f5d95]/40 bg-[#121a34]/70 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.24em] text-[#9db2ff]"
          title={disclaimer}
        >
          AI Signal
        </span>
      </div>

      <div className="mt-6 flex flex-col items-center">
        <div className="relative flex h-56 w-56 items-center justify-center">
          <svg className="h-full w-full -rotate-90" viewBox="0 0 224 224">
            <defs>
              <linearGradient id="credit-score-gradient" x1="0%" x2="100%" y1="0%" y2="100%">
                <stop offset="0%" stopColor="#72a4ff" />
                <stop offset="100%" stopColor="#9a7cff" />
              </linearGradient>
            </defs>
            <circle cx="112" cy="112" r="90" fill="transparent" stroke="currentColor" strokeWidth="14" className="text-[#141f38]" />
            <circle
              cx="112"
              cy="112"
              r="90"
              fill="transparent"
              stroke="url(#credit-score-gradient)"
              strokeWidth="14"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
              style={{ filter: "drop-shadow(0 0 10px rgba(114,164,255,0.35))" }}
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-5xl font-extrabold text-[#eff2ff]">{score}</span>
            <span className="mt-1 text-xs font-bold uppercase tracking-widest text-[#9db2ff]">{category}</span>
            <span className="mt-2 text-[11px] text-[#8a96b8]">
              Range {range.min} to {range.max}
            </span>
          </div>
        </div>

        <div className="mt-6 grid w-full grid-cols-3 gap-3">
          <div className="rounded-2xl border border-white/5 bg-[#141f38]/35 p-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#95a0c4]">Spending Stability</p>
            <p className="mt-2 text-sm font-bold text-[#9db2ff]">{indicators.spending_stability}</p>
          </div>
          <div className="rounded-2xl border border-white/5 bg-[#141f38]/35 p-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#95a0c4]">Savings Ratio</p>
            <p className="mt-2 text-sm font-bold text-[#bca9ff]">{indicators.savings_ratio}</p>
          </div>
          <div className="rounded-2xl border border-white/5 bg-[#141f38]/35 p-3">
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#95a0c4]">Risk Level</p>
            <p className="mt-2 text-sm font-bold text-[#ff98af]">{indicators.risk_level}</p>
          </div>
        </div>

        <div className="mt-6 w-full rounded-[1.6rem] border border-white/5 bg-[#121a34]/75 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-[#97a5cd]">Feature Contributions</p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-[#0f1730]/85 p-3">
              <p className="text-[10px] font-bold uppercase text-[#8b97ba]">Savings Ratio</p>
              <p className={`mt-2 text-base font-bold ${contributionColor(feature_contributions.savings_ratio)}`}>{formatContribution(feature_contributions.savings_ratio)}</p>
            </div>
            <div className="rounded-2xl bg-[#0f1730]/85 p-3">
              <p className="text-[10px] font-bold uppercase text-[#8b97ba]">Volatility</p>
              <p className={`mt-2 text-base font-bold ${contributionColor(feature_contributions.volatility)}`}>{formatContribution(feature_contributions.volatility)}</p>
            </div>
            <div className="rounded-2xl bg-[#0f1730]/85 p-3">
              <p className="text-[10px] font-bold uppercase text-[#8b97ba]">Anomalies</p>
              <p className={`mt-2 text-base font-bold ${contributionColor(feature_contributions.anomalies)}`}>{formatContribution(feature_contributions.anomalies)}</p>
            </div>
            <div className="rounded-2xl bg-[#0f1730]/85 p-3">
              <p className="text-[10px] font-bold uppercase text-[#8b97ba]">Expense/Income</p>
              <p className={`mt-2 text-base font-bold ${contributionColor(feature_contributions.expense_income_ratio)}`}>{formatContribution(feature_contributions.expense_income_ratio)}</p>
            </div>
          </div>
        </div>

        <div className="mt-6 w-full rounded-[1.6rem] border border-[#6982ff]/15 bg-[#10182f]/85 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-[#9db2ff]">Improve Score</p>
          <ul className="mt-3 space-y-2 text-sm text-[#d8def6]">
            {suggestions.slice(0, 3).map((suggestion) => (
              <li key={suggestion} className="rounded-xl bg-[#141f38]/45 px-3 py-2">
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
