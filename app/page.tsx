import DashboardLiveSocket from "@/components/dashboard/DashboardLiveSocket";
import LiveNotificationCenter from "@/components/dashboard/LiveNotificationCenter";
import DashboardDeepLinkNavigator from "@/components/dashboard/DashboardDeepLinkNavigator";
import DashboardFinanceBridge from "@/components/dashboard/DashboardFinanceBridge";
import DashboardRealtimeView from "@/components/dashboard/DashboardRealtimeView";
import type { DashboardData } from "@/lib/api-client";
import { BACKEND_API_BASE } from "@/lib/backend-config";

export const dynamic = "force-dynamic";

async function getDashboardData(): Promise<DashboardData> {
  const response = await fetch(`${BACKEND_API_BASE}/dashboard/`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Dashboard request failed with status ${response.status}.`);
  }

  const payload = await response.json();
  return payload.data as DashboardData;
}

export default async function Dashboard() {
  let data: DashboardData | null = null;
  let error = "";

  try {
    data = await getDashboardData();
  } catch (err) {
    console.error(err);
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
