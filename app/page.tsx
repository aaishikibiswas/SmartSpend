import { Suspense } from "react";
import DashboardLiveSocket from "@/components/dashboard/DashboardLiveSocket";
import DashboardDeepLinkNavigator from "@/components/dashboard/DashboardDeepLinkNavigator";
import DashboardFinanceBridge from "@/components/dashboard/DashboardFinanceBridge";
import DashboardRealtimeView from "@/components/dashboard/DashboardRealtimeView";
import type { DashboardData } from "@/lib/api-client";
import { BACKEND_API_BASE } from "@/lib/backend-config";
import { getSessionToken } from "@/lib/auth-session";
import { redirect } from "next/navigation";
import Loading from "./loading";

export const dynamic = "force-dynamic";

import { FALLBACK_DASHBOARD_DATA } from "@/lib/fallback-data";

async function fetchWithRetry(url: string, init: RequestInit, retries = 3, delay = 1000): Promise<Response> {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, init);
      // If the response is OK or it's a 401 (which we handle by redirecting), return it
      if (response.ok || response.status === 401) {
        return response;
      }
      // For other errors (500, 503, etc.), retry if we have attempts left
      if (i < retries - 1) {
        await new Promise((res) => setTimeout(res, delay));
        continue;
      }
      return response;
    } catch (err) {
      if (i === retries - 1) throw err;
      await new Promise((res) => setTimeout(res, delay));
    }
  }
  throw new Error("Failed to fetch dashboard data after multiple attempts.");
}

async function getDashboardData(): Promise<DashboardData> {
  const token = await getSessionToken();
  if (!token) {
    redirect("/login");
  }

  try {
    const response = await fetchWithRetry(`${BACKEND_API_BASE}/dashboard/`, {
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (response.status === 401) {
      redirect("/login");
    }

    if (!response.ok) {
      console.warn(`[Dashboard] Backend responded with status ${response.status}. Using fallback data.`);
      return FALLBACK_DASHBOARD_DATA;
    }

    const payload = await response.json();
    return payload.data as DashboardData;
  } catch (err) {
    // Re-throw redirect errors so Next.js can handle them
    if (err instanceof Error && (err.message === "NEXT_REDIRECT" || (err as any).digest?.startsWith("NEXT_REDIRECT"))) {
      throw err;
    }

    console.warn("[Dashboard] Backend unavailable or returned error. Using fallback data to keep dashboard alive.");
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
