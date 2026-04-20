import { useState } from "react";
import MetricCard from "./components/MetricCard";
import SectionCard from "./components/SectionCard";
import { BarChart, DonutChart, LineChart } from "./components/Charts";
import { analyzeDashboard, uploadStatement } from "./lib/api";

const DEFAULT_BUDGETS = {
  monthly_budget: 10000,
  weekly_budget_amount: 2500,
  financial_goals: [],
  bill_reminders: [],
  category_budgets: {},
  filters: {
    start_date: null,
    end_date: null,
    categories: ["All"],
    projection_months: 6
  }
};

function formatCurrency(value) {
  return `Rs. ${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function AlertList({ alerts }) {
  if (!alerts.length) {
    return <p className="muted">No alerts yet.</p>;
  }

  return (
    <div className="alert-list">
      {alerts.map((alert, index) => (
        <article key={`${alert.section}-${index}`} className={`alert alert--${alert.type || "info"}`}>
          <p className="alert__section">{alert.section}</p>
          <p>{alert.message}</p>
        </article>
      ))}
    </div>
  );
}

function TransactionsTable({ transactions }) {
  if (!transactions.length) {
    return <p className="muted">Upload a receipt or statement to populate recent transactions.</p>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Category</th>
            <th>Debit</th>
            <th>Credit</th>
            <th>Balance</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx, index) => (
            <tr key={`${tx.date}-${tx.description}-${index}`}>
              <td>{tx.date}</td>
              <td>{tx.description}</td>
              <td>{tx.category || "Other"}</td>
              <td>{formatCurrency(tx.debit)}</td>
              <td>{formatCurrency(tx.credit)}</td>
              <td>{formatCurrency(tx.balance)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [transactions, setTransactions] = useState([]);
  const [availableCategories, setAvailableCategories] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");

  const metrics = dashboard?.metrics || {};
  const charts = dashboard?.charts || {};

  async function handleUpload(event) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV, PDF, PNG, JPG, or JPEG file first.");
      return;
    }

    setUploading(true);
    setError("");

    try {
      const uploadData = await uploadStatement(file);
      setTransactions(uploadData.transactions || []);
      setAvailableCategories(uploadData.available_categories || []);

      const analysis = await analyzeDashboard({
        ...DEFAULT_BUDGETS,
        transactions: uploadData.transactions || []
      });

      setDashboard(analysis);
    } catch (err) {
      setDashboard(null);
      setError(err.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">FinSet</p>
          <h1>Upload a receipt and watch the dashboard update end to end.</h1>
          <p className="hero__copy">
            This flow posts your file to FastAPI, normalizes transactions, runs the dashboard analysis, and renders
            alerts plus chart data from the API response.
          </p>
        </div>

        <form className="upload-panel" onSubmit={handleUpload}>
          <label className="file-picker">
            <span>Receipt or statement</span>
            <input
              type="file"
              accept=".csv,.pdf,.png,.jpg,.jpeg"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          <button type="submit" disabled={uploading}>
            {uploading ? "Analyzing..." : "Upload and analyze"}
          </button>
          <p className="helper">
            Current API target: <code>VITE_API_BASE</code> or <code>http://127.0.0.1:8000</code> by default.
          </p>
          {file ? <p className="file-name">Selected: {file.name}</p> : null}
          {error ? <p className="error-banner">{error}</p> : null}
        </form>
      </section>

      <section className="metrics-grid">
        <MetricCard label="Total income" value={formatCurrency(metrics.total_income)} detail="From analyzed transactions" />
        <MetricCard label="Total expense" value={formatCurrency(metrics.total_expense)} detail="Debit sum from API" tone="warning" />
        <MetricCard label="Savings" value={formatCurrency(metrics.total_savings)} detail={`Savings rate ${metrics.savings_rate || 0}%`} tone="success" />
        <MetricCard
          label="Top category"
          value={metrics.top_category || "Awaiting data"}
          detail={metrics.top_category_value ? formatCurrency(metrics.top_category_value) : "No spend detected"}
        />
      </section>

      <section className="dashboard-grid">
        <SectionCard title="Alerts" subtitle="Budget, duplicates, high transactions, and weekly tips">
          <AlertList alerts={dashboard?.alerts || []} />
        </SectionCard>

        <SectionCard title="Expense breakdown" subtitle="Top categories returned by the backend">
          {charts.expense_breakdown?.length ? <DonutChart data={charts.expense_breakdown} /> : <p className="muted">No chart data yet.</p>}
        </SectionCard>

        <SectionCard title="Daily expense trend" subtitle="Line chart of the backend daily series" className="section-card--wide">
          {charts.daily_expense?.length ? <LineChart data={charts.daily_expense} /> : <p className="muted">No timeline yet.</p>}
        </SectionCard>

        <SectionCard title="Overview" subtitle="Income vs expense vs savings">
          {charts.report_overview?.length ? <BarChart data={charts.report_overview} /> : <p className="muted">No summary chart yet.</p>}
        </SectionCard>
      </section>

      <section className="details-grid">
        <SectionCard title="Recent transactions" subtitle="Latest items after normalization">
          <TransactionsTable transactions={dashboard?.recent_transactions || transactions} />
        </SectionCard>

        <SectionCard title="Upload diagnostics" subtitle="Useful when debugging fetch or CORS issues">
          <dl className="diagnostics">
            <div>
              <dt>Transactions parsed</dt>
              <dd>{transactions.length}</dd>
            </div>
            <div>
              <dt>Categories detected</dt>
              <dd>{availableCategories.length ? availableCategories.join(", ") : "None yet"}</dd>
            </div>
            <div>
              <dt>Dashboard response</dt>
              <dd>{dashboard?.has_data ? "Received" : "Waiting"}</dd>
            </div>
          </dl>
        </SectionCard>
      </section>
    </main>
  );
}
