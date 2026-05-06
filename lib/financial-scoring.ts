import type { DashboardMetrics, TransactionItem } from "@/lib/api-client";

type CreditScore = DashboardMetrics["creditScore"];

type ScoreSlab = {
  label: string;
  range: string;
  summary: string;
  tone: "strong" | "steady" | "watch" | "risk";
};

type ScoreInputs = {
  income: number;
  totalExpense: number;
  savingsRatio: number;
  volatility: number;
  anomalyCount: number;
  budgetUsagePercent: number;
};

function clamp(value: number, minimum: number, maximum: number) {
  return Math.max(minimum, Math.min(maximum, value));
}

function roundMoney(value: number) {
  return Number((Number(value) || 0).toFixed(2));
}

function txTime(tx: TransactionItem) {
  const d = new Date(tx.rawDate || tx.date);
  return Number.isNaN(d.getTime()) ? 0 : d.getTime();
}

function isIncome(tx: TransactionItem) {
  return tx.type === "income" || Number(tx.amount) > 0;
}

function isExpense(tx: TransactionItem) {
  return tx.type === "expense" || Number(tx.amount) < 0;
}

export function getFinancialHealthSlab(score: number): ScoreSlab {
  if (score >= 80) return { label: "Excellent", range: "80-100", summary: "Strong surplus and low budget pressure.", tone: "strong" };
  if (score >= 65) return { label: "Healthy", range: "65-79", summary: "Good cushion with room to optimize.", tone: "steady" };
  if (score >= 50) return { label: "Stable", range: "50-64", summary: "Manageable, but needs active tracking.", tone: "watch" };
  return { label: "Needs Focus", range: "0-49", summary: "Spending pressure is weakening resilience.", tone: "risk" };
}

export function getCreditScoreSlab(score: number): ScoreSlab {
  if (score >= 750) return { label: "Excellent", range: "750-900", summary: "Very strong behavioral credit profile.", tone: "strong" };
  if (score >= 650) return { label: "Good", range: "650-749", summary: "Reliable profile with moderate risk.", tone: "steady" };
  if (score >= 550) return { label: "Fair", range: "550-649", summary: "Some stress signals are visible.", tone: "watch" };
  return { label: "Risky", range: "300-549", summary: "High spend pressure or irregularity detected.", tone: "risk" };
}

export function calculateTransactionVolatility(transactions: TransactionItem[]) {
  const dailyExpenses = new Map<string, number>();
  for (const tx of transactions) {
    if (!isExpense(tx)) continue;
    const d = new Date(tx.rawDate || tx.date);
    if (Number.isNaN(d.getTime())) continue;
    const key = d.toISOString().slice(0, 10);
    dailyExpenses.set(key, (dailyExpenses.get(key) || 0) + Math.abs(Number(tx.amount) || 0));
  }

  const values = Array.from(dailyExpenses.values());
  if (values.length <= 1) return 0;

  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (values.length - 1);
  return roundMoney(Math.sqrt(variance));
}

export function calculateAnomalyCount(transactions: TransactionItem[]) {
  const expenses = transactions.filter(isExpense).map((tx) => Math.abs(Number(tx.amount) || 0));
  if (expenses.length < 4) return 0;

  const mean = expenses.reduce((sum, value) => sum + value, 0) / expenses.length;
  const variance = expenses.reduce((sum, value) => sum + (value - mean) ** 2, 0) / expenses.length;
  const threshold = mean + Math.sqrt(variance) * 2;
  return expenses.filter((value) => value > threshold).length;
}

export function calculateFinancialHealthScore({ income, savingsRatio, volatility, budgetUsagePercent }: ScoreInputs) {
  const budgetPressure = Math.min(100, Math.max(0, budgetUsagePercent));
  const rawScore = 55 + savingsRatio * 0.45 - (volatility / Math.max(income, 1)) * 100 - budgetPressure * 0.18;
  return Math.round(clamp(rawScore, 0, 100));
}

function getCreditCategory(score: number) {
  return getCreditScoreSlab(score).label;
}

function buildCreditSuggestions(savingsRatio: number, volatility: number, anomalyCount: number, expenseIncomeRatio: number) {
  const suggestions: string[] = [];
  if (savingsRatio < 20) suggestions.push("Increase monthly savings contributions to strengthen your financial buffer.");
  if (volatility > 5000) suggestions.push("Reduce irregular spending spikes to improve behavioral stability.");
  if (anomalyCount > 1) suggestions.push("Review unusual transactions and eliminate suspicious or avoidable outliers.");
  if (expenseIncomeRatio > 0.75) suggestions.push("Lower expense load relative to income to improve affordability confidence.");
  return suggestions.length > 0 ? suggestions : ["Maintain your current discipline to preserve a strong behavioral credit profile."];
}

export function calculateCreditScore({ income, totalExpense, savingsRatio, volatility, anomalyCount }: ScoreInputs): CreditScore {
  const expenseIncomeRatio = income > 0 ? totalExpense / income : 1;
  const savingsContribution = clamp((savingsRatio / 35) * 100, -20, 100);
  const volatilityContribution = clamp(((6000 - volatility) / 6000) * 80, -80, 80);
  const anomalyContribution = clamp(-(anomalyCount * 23), -70, 0);
  const expenseRatioContribution = clamp(((0.55 - expenseIncomeRatio) / 0.55) * 100, -100, 80);
  const score = Math.round(clamp(600 + savingsContribution + volatilityContribution + anomalyContribution + expenseRatioContribution, 300, 900));

  const contributions = {
    savings_ratio: roundMoney(savingsContribution),
    volatility: roundMoney(volatilityContribution),
    anomalies: roundMoney(anomalyContribution),
    expense_income_ratio: roundMoney(expenseRatioContribution),
  };

  return {
    score,
    category: getCreditCategory(score),
    range: { min: 300, max: 900 },
    indicators: {
      spending_stability: volatility <= 1800 ? "High" : volatility <= 4200 ? "Medium" : "Low",
      savings_ratio: savingsRatio >= 30 ? "Strong" : savingsRatio >= 15 ? "Moderate" : "Weak",
      risk_level: anomalyCount === 0 && expenseIncomeRatio < 0.65 ? "Low" : anomalyCount <= 2 && expenseIncomeRatio < 0.85 ? "Medium" : "High",
    },
    feature_contributions: contributions,
    explainability: {
      top_positive_driver: Object.entries(contributions).sort((a, b) => b[1] - a[1])[0][0],
      top_negative_driver: Object.entries(contributions).sort((a, b) => a[1] - b[1])[0][0],
    },
    suggestions: buildCreditSuggestions(savingsRatio, volatility, anomalyCount, expenseIncomeRatio),
    disclaimer: "This is a behavioral credit estimate based on synced transaction data, not an official bank score.",
  };
}

export function calculateScoreInputs(transactions: TransactionItem[], budgetUsagePercent: number): ScoreInputs {
  let income = 0;
  let totalExpense = 0;

  for (const tx of transactions) {
    const amount = Number(tx.amount) || 0;
    if (isIncome(tx)) income += Math.abs(amount);
    if (isExpense(tx)) totalExpense += Math.abs(amount);
  }

  const netSavings = income - totalExpense;
  return {
    income: roundMoney(income),
    totalExpense: roundMoney(totalExpense),
    savingsRatio: income > 0 ? roundMoney((netSavings / income) * 100) : 0,
    volatility: calculateTransactionVolatility(transactions),
    anomalyCount: calculateAnomalyCount(transactions),
    budgetUsagePercent,
  };
}

export function calculateLiveScores(inputs: ScoreInputs) {
  return {
    healthScore: calculateFinancialHealthScore(inputs),
    creditScore: calculateCreditScore(inputs),
  };
}

export function sortTransactionsByLatest(items: TransactionItem[]) {
  return [...items].sort((a, b) => txTime(b) - txTime(a));
}
