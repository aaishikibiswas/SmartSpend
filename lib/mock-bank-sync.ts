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
};

const CATEGORIES = ["Food", "Shopping", "Transport", "Bills"] as const;
const NAMES = ["Zomato", "Amazon", "Uber", "Electricity"] as const;

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
  const category = CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];
  const merchant = NAMES[Math.floor(Math.random() * NAMES.length)];
  const isDebit = Math.random() > 0.5;
  const rawAmount = Math.floor(Math.random() * 2000) + 50;
  const amount = isDebit ? -rawAmount : rawAmount;
  const initialBase = baseTime || new Date();
  const nextTime = new Date(initialBase.getTime() + getRandomGap());

  return {
    id: nextTime.getTime(),
    merchant,
    category,
    amount,
    type: amount < 0 ? "expense" : "income",
    rawDate: nextTime,
    date: formatDateTime(nextTime),
    source: "mock",
    language: "Source: mock",
  };
}

export function startMockSync(onUpdate: (tx: MockTransaction) => void) {
  const interval = window.setInterval(() => {
    const tx = generateFakeTransaction();
    onUpdate(tx);
  }, 3000);

  return () => window.clearInterval(interval);
}
