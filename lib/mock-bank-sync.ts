export type MockTransaction = {
  id: number;
  merchant: string;
  category: string;
  amount: number;
  type: "income" | "expense";
  rawDate: Date;
  date: string;
  source: "mock";
  language: string;
  mcc: string;
  transaction_reference: string;
  payment_method: "UPI" | "Card" | "Bank Transfer" | "Auto Debit" | "NACH";
  bank_source: string;
  recurring_confidence: number;
  is_subscription: boolean;
  is_emi: boolean;
  subscription_detection?: {
    product: string;
    interval: "Weekly" | "Monthly" | "Quarterly" | "Yearly";
  };
  emi_detection?: {
    lender: string;
    asset: string;
  };
  installment_metadata?: {
    total_amount: number;
    remaining_months: number;
    interest_rate: number;
  };
  liability_type?: "Subscription" | "EMI" | "Bill" | "Rent";
};

type MerchantProfile = {
  merchant: string;
  category: string;
  mcc: string;
  min: number;
  max: number;
  payment_method: MockTransaction["payment_method"];
  bank_source: string;
  recurring_confidence: number;
  subscription?: {
    product: string;
    interval: "Weekly" | "Monthly" | "Quarterly" | "Yearly";
  };
  emi?: {
    lender: string;
    asset: string;
    total_amount: number;
    remaining_months: number;
    interest_rate: number;
  };
  liability_type?: MockTransaction["liability_type"];
};

const MERCHANTS: MerchantProfile[] = [
  { merchant: "Netflix Subscription", category: "Entertainment", mcc: "4899", min: 499, max: 799, payment_method: "Auto Debit", bank_source: "HDFC Visa AutoPay", recurring_confidence: 0.94, subscription: { product: "Netflix", interval: "Monthly" }, liability_type: "Subscription" },
  { merchant: "Spotify Premium", category: "Entertainment", mcc: "5815", min: 119, max: 179, payment_method: "UPI", bank_source: "UPI Autopay", recurring_confidence: 0.92, subscription: { product: "Spotify Premium", interval: "Monthly" }, liability_type: "Subscription" },
  { merchant: "Amazon Prime", category: "Shopping", mcc: "5968", min: 1499, max: 1499, payment_method: "Card", bank_source: "ICICI Credit Card", recurring_confidence: 0.88, subscription: { product: "Amazon Prime", interval: "Yearly" }, liability_type: "Subscription" },
  { merchant: "Apple Music", category: "Entertainment", mcc: "5815", min: 99, max: 149, payment_method: "Card", bank_source: "Axis Debit Card", recurring_confidence: 0.9, subscription: { product: "Apple Music", interval: "Monthly" }, liability_type: "Subscription" },
  { merchant: "Google One", category: "Subscription", mcc: "5734", min: 130, max: 650, payment_method: "Card", bank_source: "SBI Credit Card", recurring_confidence: 0.87, subscription: { product: "Google One", interval: "Monthly" }, liability_type: "Subscription" },
  { merchant: "Adobe CC", category: "Subscription", mcc: "5734", min: 1675, max: 4500, payment_method: "Card", bank_source: "HDFC Credit Card", recurring_confidence: 0.91, subscription: { product: "Adobe Creative Cloud", interval: "Monthly" }, liability_type: "Subscription" },
  { merchant: "Gym Membership", category: "Health", mcc: "7997", min: 1500, max: 3000, payment_method: "UPI", bank_source: "UPI Mandate", recurring_confidence: 0.84, subscription: { product: "Gym Membership", interval: "Monthly" }, liability_type: "Subscription" },
  { merchant: "Apartment Rent", category: "Housing", mcc: "6513", min: 22000, max: 28000, payment_method: "Bank Transfer", bank_source: "NEFT", recurring_confidence: 0.86, liability_type: "Rent" },
  { merchant: "Electricity Bill", category: "Bills", mcc: "4900", min: 1800, max: 5200, payment_method: "UPI", bank_source: "BBPS UPI", recurring_confidence: 0.8, liability_type: "Bill" },
  { merchant: "Water Bill", category: "Utilities", mcc: "4900", min: 450, max: 1250, payment_method: "UPI", bank_source: "BBPS UPI", recurring_confidence: 0.76, liability_type: "Bill" },
  { merchant: "Internet Bill", category: "Bills", mcc: "4814", min: 899, max: 1999, payment_method: "Auto Debit", bank_source: "NACH Mandate", recurring_confidence: 0.82, liability_type: "Bill" },
  { merchant: "Phone Recharge", category: "Telecom", mcc: "4814", min: 299, max: 999, payment_method: "UPI", bank_source: "UPI Lite", recurring_confidence: 0.72, subscription: { product: "Phone Recharge", interval: "Monthly" }, liability_type: "Subscription" },
  { merchant: "Credit Card EMI", category: "EMI", mcc: "6012", min: 4200, max: 8900, payment_method: "NACH", bank_source: "HDFC Bank", recurring_confidence: 0.96, emi: { lender: "HDFC Bank", asset: "Credit Card EMI", total_amount: 84000, remaining_months: 10, interest_rate: 14.5 }, liability_type: "EMI" },
  { merchant: "Laptop EMI", category: "EMI", mcc: "5732", min: 6200, max: 6200, payment_method: "NACH", bank_source: "Bajaj Finance", recurring_confidence: 0.97, emi: { lender: "Bajaj Finance", asset: "Laptop", total_amount: 74400, remaining_months: 8, interest_rate: 11.2 }, liability_type: "EMI" },
  { merchant: "Education Loan EMI", category: "Loan", mcc: "8299", min: 12500, max: 12500, payment_method: "NACH", bank_source: "SBI Loan", recurring_confidence: 0.98, emi: { lender: "SBI", asset: "Education Loan", total_amount: 450000, remaining_months: 36, interest_rate: 9.1 }, liability_type: "EMI" },
  { merchant: "Bike EMI", category: "EMI", mcc: "5571", min: 3800, max: 5200, payment_method: "NACH", bank_source: "IDFC First Bank", recurring_confidence: 0.94, emi: { lender: "IDFC First", asset: "Bike", total_amount: 114000, remaining_months: 18, interest_rate: 10.3 }, liability_type: "EMI" },
  { merchant: "Zomato", category: "Food", mcc: "5812", min: 220, max: 1400, payment_method: "UPI", bank_source: "PhonePe UPI", recurring_confidence: 0.08 },
  { merchant: "Uber", category: "Transport", mcc: "4121", min: 160, max: 950, payment_method: "Card", bank_source: "Axis Credit Card", recurring_confidence: 0.05 },
  { merchant: "Amazon Retail", category: "Shopping", mcc: "5399", min: 499, max: 4500, payment_method: "UPI", bank_source: "Google Pay UPI", recurring_confidence: 0.1 },
];

export function formatDateTime(date: Date | string) {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}   ${hours}:${minutes}`;
}

export function getRandomGap() {
  const min = 2 * 60 * 1000;
  const max = 15 * 60 * 1000;
  return Math.floor(Math.random() * (max - min) + min);
}

export function generateFakeTransaction(baseTime?: Date): MockTransaction {
  const profile = MERCHANTS[Math.floor(Math.random() * MERCHANTS.length)];
  const isIncome = Math.random() < 0.08;
  const rawAmount = isIncome ? Math.floor(Math.random() * 90000) + 30000 : Math.floor(Math.random() * (profile.max - profile.min + 1)) + profile.min;
  const amount = isIncome ? rawAmount : -rawAmount;
  const initialBase = baseTime || new Date();
  const nextTime = new Date(initialBase.getTime() + getRandomGap());
  const sequence = String(Math.floor(Math.random() * 999999)).padStart(6, "0");
  const transaction_reference = `${profile.payment_method.replace(" ", "").toUpperCase()}/${nextTime.getFullYear()}${String(nextTime.getMonth() + 1).padStart(2, "0")}${String(nextTime.getDate()).padStart(2, "0")}/${sequence}`;

  return {
    id: nextTime.getTime(),
    merchant: isIncome ? "Salary Credit" : profile.merchant,
    category: isIncome ? "Income" : profile.category,
    amount,
    type: amount < 0 ? "expense" : "income",
    rawDate: nextTime,
    date: formatDateTime(nextTime),
    source: "mock",
    language: `Source: ${isIncome ? "bank transfer" : profile.bank_source}`,
    mcc: isIncome ? "6010" : profile.mcc,
    transaction_reference,
    payment_method: isIncome ? "Bank Transfer" : profile.payment_method,
    bank_source: isIncome ? "Employer NEFT" : profile.bank_source,
    recurring_confidence: isIncome ? 0 : profile.recurring_confidence,
    is_subscription: Boolean(profile.subscription),
    is_emi: Boolean(profile.emi),
    subscription_detection: profile.subscription,
    emi_detection: profile.emi ? { lender: profile.emi.lender, asset: profile.emi.asset } : undefined,
    installment_metadata: profile.emi
      ? {
          total_amount: profile.emi.total_amount,
          remaining_months: profile.emi.remaining_months,
          interest_rate: profile.emi.interest_rate,
        }
      : undefined,
    liability_type: profile.liability_type,
  };
}

export function startMockSync(onUpdate: (tx: MockTransaction) => void) {
  const interval = window.setInterval(() => {
    const tx = generateFakeTransaction();
    onUpdate(tx);
  }, 3000);

  return () => window.clearInterval(interval);
}
