import { Suspense } from "react";
import DashboardLiveSocket from "@/components/dashboard/DashboardLiveSocket";
import DashboardDeepLinkNavigator from "@/components/dashboard/DashboardDeepLinkNavigator";
import DashboardFinanceBridge from "@/components/dashboard/DashboardFinanceBridge";
import DashboardRealtimeView from "@/components/dashboard/DashboardRealtimeView";
import type { DashboardData } from "@/lib/api-client";
import { BACKEND_API_BASE } from "@/lib/backend-config";
import { getSessionToken } from "@/lib/auth-session";
import Loading from "./loading";

export const dynamic = "force-dynamic";

import { FALLBACK_DASHBOARD_DATA } from "@/lib/fallback-data";

async function getDashboardData(): Promise<DashboardData> {
  const token = await getSessionToken();
  if (!token) {
    throw new Error("Authentication required. Please sign in again.");
  }

  try {
    const response = await fetch(`${BACKEND_API_BASE}/dashboard/`, {
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      console.warn(`[Dashboard] Backend responded with status ${response.status}. Using fallback data.`);
      return FALLBACK_DASHBOARD_DATA;
    }

    const payload = await response.json();
    return payload.data as DashboardData;
  } catch (err) {
    console.warn("[Dashboard] Backend unavailable. Using fallback data to keep dashboard alive.");
    return FALLBACK_DASHBOARD_DATA;
  }
}

async function DashboardContent() {
  const data = await getDashboardData();
  const { metrics, categoryBreakdown, recentTransactions, allTransactions } = data;

  return (
    <>
      <DashboardDeepLinkNavigator />
      <DashboardLiveSocket />
      <DashboardFinanceBridge metrics={metrics} categoryBreakdown={categoryBreakdown} recentTransactions={recentTransactions} allTransactions={allTransactions} />
      <DashboardRealtimeView initialData={data} />
    </>
  );
}

export default function Dashboard() {
  return (
    <div className="-mx-4 -my-5 pb-36 md:-mx-6 md:-my-6 xl:-mx-7 xl:-my-6">
      <Suspense fallback={<Loading />}>
        <DashboardContent />
      </Suspense>
    </div>
  );
}
