const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export type AlertItem = {
  id: number;
  type: string;
  title: string;
  message: string;
};

export type GoalItem = {
  id: number;
  name: string;
  target: number;
  achieved: number;
  daysLeft: number;
  color: string;
};

export type BillItem = {
  id: number;
  name: string;
  amount: number;
  due: string;
  icon: string;
  color: string;
};

export type SubscriptionCreatePayload = {
  name: string;
  monthly_cost: number;
  frequency: string;
  last_charge_date: string;
  next_due_date: string;
};

export type BillCreatePayload = {
  name: string;
  amount: number;
  due: string;
  icon?: string;
  color?: string;
};

export type TransactionItem = {
  id?: number;
  merchant: string;
  category: string;
  date: string;
  amount: number;
  type: string;
  language?: string;
};

export type DashboardMetrics = {
  totalIncome: number;
  totalExpense: number;
  netSavings: number;
  totalBalance: number;
  savingsRatio: number;
  volatility: number;
  healthScore: number;
  budgetUsagePercent: number;
  remainingBudget: number;
  dailyAllowance: number;
  burnRate: number;
  savingsGrowth: number;
  lifestyleInflation: number;
  runwayMonths: number;
  financialPersonality: string;
  subscriptionLoad: number;
  monthlyEmiLoad: number;
  netWorth: number;
  assets: number;
  liabilities: number;
  fixedExpensePercent: number;
  variableExpensePercent: number;
  projectedOutflow: number;
  creditScore: {
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
    explainability: {
      top_positive_driver: string;
      top_negative_driver: string;
    };
    suggestions: string[];
    disclaimer: string;
  };
  trends: {
    balanceTrend: number;
    incomeTrend: number;
    expenseTrend: number;
    savingsTrend: number;
  };
};

export type CategoryBreakdownItem = {
  name: string;
  amount: number;
};

export type BudgetCategoryItem = {
  name: string;
  allocated_amount: number;
  frequency: string;
  spent_amount: number;
  remaining_amount: number;
  usage_percent: number;
  status: string;
  monthly_equivalent: number;
};

export type GlobalBudgetSummary = {
  monthly_budget: number;
  weekly_budget: number;
  spent_amount: number;
  remaining_amount: number;
  usage_percent: number;
  daily_allowance: number;
  auto_distribute: boolean;
  status: string;
};

export type BudgetSnapshot = {
  global: GlobalBudgetSummary;
  categories: BudgetCategoryItem[];
  feedback: string[];
};

export type GoalSuggestion = {
  recommendedContribution: number;
  message: string;
};

export type SubscriptionItem = {
  id?: number;
  name: string;
  frequency: string;
  monthly_cost: number;
  yearly_cost: number;
  last_charge_date: string;
  next_due_date: string;
  source?: string;
};

export type EmiItem = {
  id: number | string;
  name: string;
  total_amount: number;
  monthly_emi: number;
  remaining_months: number;
  interest_rate: number;
  due_date: string;
  source?: string;
};

export type EmiSummary = {
  items: EmiItem[];
  monthly_load: number;
  remaining_liability: number;
};

export type ExpenseSplitData = {
  fixed_total: number;
  variable_total: number;
  fixed_percent: number;
  variable_percent: number;
  breakdown: { name: string; amount: number }[];
};

export type NetworthData = {
  assets: number;
  liabilities: number;
  net_worth: number;
};

export type CashflowData = {
  upcoming_payments: { name: string; date: string; amount: number; type: string }[];
  monthly_outflow_projection: number;
};

export type PriorityItem = {
  level: string;
  title: string;
  message: string;
};

export type DashboardData = {
  metrics: DashboardMetrics;
  budgeting: BudgetSnapshot;
  goalSuggestion: GoalSuggestion;
  categoryBreakdown: CategoryBreakdownItem[];
  subscriptions: SubscriptionItem[];
  emi: EmiSummary;
  expenseSplit: ExpenseSplitData;
  networth: NetworthData;
  cashflow: CashflowData;
  priorities: PriorityItem[];
  bills: BillItem[];
  recentTransactions: TransactionItem[];
  allTransactions: TransactionItem[];
};

export type PredictionData = {
  forecast: { peakAlert: { day: string; amount: number }; series: number[] };
  next_expense_prediction: { predicted_expense: number; risk_level: string; budget_usage_percent: number; recurring_load: number };
};

export type UploadResult = {
  success: boolean;
  extractedTransactionsCount: number;
  message: string;
};

export type AssistantResponse = {
  answer: string;
  suggestions: string[];
};

export type AuthUser = {
  id: number;
  full_name: string;
  email: string;
  plan: string;
  avatar_seed: string;
};

export type TransactionCreatePayload = {
  date: string;
  merchant: string;
  category?: string;
  amount: number;
};

export type BudgetConfigPayload = {
  monthly_budget: number;
  auto_distribute: boolean;
};

export type CategoryBudgetPayload = {
  name: string;
  amount: number;
  frequency: string;
};

export type DecisionPayload = {
  item_name: string;
  price: number;
};

export type DecisionResult = {
  item_name: string;
  category: string;
  price: number;
  affordability: string;
  status: string;
  budget_impact_percent: number;
  current_risk_level: string;
  new_risk_level: string;
  remaining_global_budget: number;
  remaining_category_budget: number;
  recommendation: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type RegisterPayload = {
  full_name: string;
  email: string;
  password: string;
};

export type ProfileUpdatePayload = {
  full_name: string;
  plan?: string;
};

export type EmiCreatePayload = {
  name: string;
  total_amount: number;
  monthly_emi: number;
  remaining_months: number;
  interest_rate?: number;
  due_date: string;
};

export type SimulationPayload = {
  income_adjustment: number;
  expense_adjustment: number;
  months: number;
};

export type SimulationResult = {
  new_income: number;
  new_expense: number;
  monthly_savings: number;
  projected_savings: number;
  risk_level: string;
  expense_split: ExpenseSplitData;
  updated_metrics: DashboardMetrics;
  networth: NetworthData;
  cashflow: CashflowData;
  priorities: PriorityItem[];
  months: number;
};

type ApiEnvelope<T> = {
  status: number;
  data: T;
  message?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<ApiEnvelope<T>> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      redirect: "follow",
      ...init,
      signal: controller.signal,
    });

    let payload: unknown = null;

    try {
      payload = await response.json();
    } catch {
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}.`);
      }
    }

    if (!response.ok) {
      const message =
        typeof payload === "object" && payload && "message" in payload && typeof payload.message === "string"
          ? payload.message
          : `Request failed with status ${response.status}.`;
      throw new Error(message);
    }

    if (payload && typeof payload === "object" && "status" in payload && "data" in payload) {
      return payload as ApiEnvelope<T>;
    }

    return {
      status: response.status,
      data: payload as T,
    };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`Request to ${API_BASE || "same-origin"}${path} timed out after 10 seconds.`);
    }

    if (error instanceof Error) {
      throw error;
    }

    throw new Error(`Network request to ${API_BASE || "same-origin"}${path} failed.`);
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export const apiClient = {
  getDashboardData() {
    return request<DashboardData>("/api/dashboard");
  },

  getPrediction(params: { timelineDays: number }) {
    return request<PredictionData>("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
  },

  uploadStatement(file: File) {
    const formData = new FormData();
    formData.append("file", file);

    return request<UploadResult>("/api/upload", {
      method: "POST",
      body: formData,
    });
  },

  getAlerts() {
    return request<AlertItem[]>("/api/alerts");
  },

  getGoals() {
    return request<GoalItem[]>("/api/goals");
  },

  getBills() {
    return request<BillItem[]>("/api/bills");
  },

  addBill(payload: BillCreatePayload) {
    return request<BillItem>("/api/bills", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  deleteBill(identifier: string | number) {
    return request<{ removed: string | number }>(`/api/bills/${encodeURIComponent(String(identifier))}`, {
      method: "DELETE",
    });
  },

  getGlobalBudget() {
    return request<GlobalBudgetSummary>("/api/budget/global");
  },

  askAssistant(question: string) {
    return request<AssistantResponse>("/api/assistant/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
  },

  updateGlobalBudget(payload: BudgetConfigPayload) {
    return request<BudgetSnapshot & { alerts: AlertItem[] }>("/api/budget/global", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  getCategoryBudgets() {
    return request<BudgetCategoryItem[]>("/api/budget/category");
  },

  upsertCategoryBudget(payload: CategoryBudgetPayload) {
    return request<{ category: BudgetCategoryItem; categories: BudgetCategoryItem[]; feedback: string[]; alerts: AlertItem[] }>("/api/budget/category", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  deleteCategoryBudget(name: string) {
    return request<{ categories: BudgetCategoryItem[]; feedback: string[]; alerts: AlertItem[] }>(`/api/budget/category/${encodeURIComponent(name)}`, {
      method: "DELETE",
    });
  },

  evaluateDecision(payload: DecisionPayload) {
    return request<DecisionResult>("/api/decision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  addTransaction(payload: TransactionCreatePayload) {
    return request<TransactionItem>("/api/transactions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  login(payload: LoginPayload) {
    return request<{ user: AuthUser }>("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  register(payload: RegisterPayload) {
    return request<{ user: AuthUser }>("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  getCurrentUser() {
    return request<AuthUser>("/api/auth/me");
  },

  updateProfile(payload: ProfileUpdatePayload) {
    return request<AuthUser>("/api/auth/me", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  getSubscriptions() {
    return request<SubscriptionItem[]>("/api/subscriptions");
  },

  addSubscription(payload: SubscriptionCreatePayload) {
    return request<SubscriptionItem>("/api/subscriptions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  deleteSubscription(name: string) {
    return request<{ removed: string }>(`/api/subscriptions/${encodeURIComponent(name)}`, {
      method: "DELETE",
    });
  },

  getEmis() {
    return request<EmiSummary>("/api/emi");
  },

  addEmi(payload: EmiCreatePayload) {
    return request<EmiItem>("/api/emi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  deleteEmi(identifier: string | number) {
    return request<{ removed: string | number }>(`/api/emi/${encodeURIComponent(String(identifier))}`, {
      method: "DELETE",
    });
  },

  getExpenseSplit() {
    return request<ExpenseSplitData>("/api/expense-split");
  },

  getNetworth() {
    return request<NetworthData>("/api/networth");
  },

  getCashflow() {
    return request<CashflowData>("/api/cashflow");
  },

  getPriorities() {
    return request<PriorityItem[]>("/api/priorities");
  },

  runSimulation(payload: SimulationPayload) {
    return request<SimulationResult>("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  logout() {
    return request<{ success: boolean }>("/api/auth/logout", {
      method: "POST",
    });
  },
};
