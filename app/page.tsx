import DashboardLiveSocket from "@/components/dashboard/DashboardLiveSocket";
import LiveNotificationCenter from "@/components/dashboard/LiveNotificationCenter";
import DashboardDeepLinkNavigator from "@/components/dashboard/DashboardDeepLinkNavigator";
import DashboardFinanceBridge from "@/components/dashboard/DashboardFinanceBridge";
import DashboardRealtimeView from "@/components/dashboard/DashboardRealtimeView";
import type { DashboardData } from "@/lib/api-client";
import { BACKEND_API_BASE } from "@/lib/backend-config";
import { getSessionToken } from "@/lib/auth-session";

export const dynamic = "force-dynamic";

async function getDashboardData(): Promise<DashboardData> {
  const token = await getSessionToken();
  if (!token) {
    throw new Error("Authentication required. Please sign in again.");
  }

  let response: Response;
  try {
    response = await fetch(`${BACKEND_API_BASE}/dashboard/`, {
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  } catch {
    throw new Error("Dashboard backend unavailable. Start the Python backend on port 8001 and refresh.");
  }

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.message || payload?.detail || `Dashboard request failed with status ${response.status}.`);
  }
  return payload.data as DashboardData;
}

export default async function Dashboard() {
  let data: DashboardData | null = null;
  let error = "";

  try {
    data = await getDashboardData();
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load dashboard data.";
  }

  if (error || !data) {
    return <div className="flex justify-center p-10 text-sm font-semibold text-rose-300">{error || "Failed to load dashboard data."}</div>;
  }

  const { metrics, categoryBreakdown, recentTransactions, allTransactions } = data;

  return (
    <div className="-mx-4 -my-5 pb-36 md:-mx-6 md:-my-6 xl:-mx-7 xl:-my-6">
      <DashboardDeepLinkNavigator />
      <DashboardLiveSocket />
      <LiveNotificationCenter />
      <DashboardFinanceBridge metrics={metrics} categoryBreakdown={categoryBreakdown} recentTransactions={recentTransactions} allTransactions={allTransactions} />

      <DashboardRealtimeView initialData={data} />
    </div>
  );
}
