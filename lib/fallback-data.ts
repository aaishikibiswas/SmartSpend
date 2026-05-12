import type { DashboardData } from "./api-client";

export const FALLBACK_DASHBOARD_DATA: DashboardData = {
  metrics: {
    totalBalance: 12500.0,
    totalIncome: 45000.0,
    totalExpense: 38000.0,
    netSavings: 7000.0,
    burnRate: 1266.0,
    savingsGrowth: 4.2,
    lifestyleInflation: 8.5,
    runwayMonths: 18,
    healthScore: 84,
    creditScore: 785,
    savingsRatio: 32.8,
    volatility: 14.5,
    budgetUsagePercent: 67,
    trends: {
      balanceTrend: 2.4,
      incomeTrend: 5.1,
      expenseTrend: -1.2,
      savingsTrend: 8.4
    },
    financialPersonality: "Strategic Planner"
  },
  budgeting: {
    global: {
      monthly_budget: 150000,
      weekly_budget: 37500,
      spent_amount: 124300,
      remaining_amount: 25700,
      usage_percent: 82,
      daily_allowance: 1200,
      auto_distribute: true,
      status: "ok"
    },
    categories: [
      { name: "Housing", allocated_amount: 50000, spent_amount: 45000, remaining_amount: 5000, usage_percent: 90, status: "warning", frequency: "Monthly", monthly_equivalent: 50000 },
      { name: "Food", allocated_amount: 25000, spent_amount: 22000, remaining_amount: 3000, usage_percent: 88, status: "warning", frequency: "Monthly", monthly_equivalent: 25000 }
    ],
    feedback: []
  },
  goalSuggestion: {
    recommendedContribution: 25000,
    message: "Based on your current savings ratio, you can comfortably allocate ₹25,000 more to your long-term goals."
  },
  categoryBreakdown: [
    { name: "Housing", amount: 45000 },
    { name: "Food", amount: 22000 },
    { name: "Transport", amount: 12000 },
    { name: "Entertainment", amount: 8500 },
    { name: "Bills", amount: 15000 },
    { name: "Other", amount: 21800 }
  ],
  subscriptions: [
    { name: "Netflix", monthly_cost: 649, frequency: "Monthly", last_charge_date: "2026-05-01", next_due_date: "2026-06-01", source: "manual" },
    { name: "Spotify", monthly_cost: 119, frequency: "Monthly", last_charge_date: "2026-05-05", next_due_date: "2026-06-05", source: "manual" }
  ],
  emi: {
    items: [
      { id: 1, name: "Home Loan", total_amount: 5000000, monthly_emi: 42000, remaining_months: 180, interest_rate: 8.5, due_date: "10th", source: "manual" }
    ],
    monthly_load: 42000,
    remaining_liability: 7560000
  },
  expenseSplit: {
    fixed_total: 85000,
    variable_total: 39300,
    fixed_percent: 68,
    variable_percent: 32,
    breakdown: [
      { name: "Fixed", amount: 85000 },
      { name: "Variable", amount: 39300 }
    ]
  },
  networth: {
    total: 12500000,
    assets: 13000000,
    liabilities: 500000,
    growth: 5.2,
    trend: []
  },
  cashflow: {
    upcoming_payments: [
      { name: "Rent", date: "2026-06-01", amount: 45000, type: "expense" },
      { name: "Electricity", date: "2026-06-05", amount: 3500, type: "expense" }
    ],
    monthly_outflow_projection: 115000
  },
  priorities: [
    { level: "High", title: "Emergency Fund", message: "Build 6 months of expenses in a liquid fund." }
  ],
  bills: [],
  recentTransactions: [
    { id: 101, merchant: "Amazon", category: "Shopping", amount: -4500, date: new Date().toISOString(), type: "expense" },
    { id: 102, merchant: "Salary", category: "Income", amount: 185000, date: new Date().toISOString(), type: "income" }
  ],
  allTransactions: [],
  advisory: {
    recommended_savings: 50000,
    advice: [
      { icon: "Shield", label: "Protection", title: "Term Insurance", body: "Ensure you have adequate coverage.", href: "#", action: "Review" }
    ],
    behavior_profile: "Consistent Saver"
  },
  prediction: {
    forecast: { peakAlert: { day: "Day 12", amount: 15000 }, series: [2000, 2500, 2100, 3000, 2800, 3200, 2900, 3100, 3500, 3300, 4000, 15000, 3800, 3600, 3400] },
    next_expense_prediction: { predicted_expense: 12430, risk_level: "Low", budget_usage_percent: 67, recurring_load: 42000 }
  },
  behavior: { day_of_month: new Date().getDate() }
};
