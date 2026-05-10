"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import DashboardHalo from "@/components/DashboardHalo";

const AUTH_ROUTES = new Set(["/login", "/register"]);

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthRoute = AUTH_ROUTES.has(pathname);
  const isDashboard = pathname === "/" || pathname === "/dashboard";

  if (isAuthRoute) {
    return (
      <main className="mx-auto flex min-h-[calc(100vh-1rem)] max-w-[1460px] items-center justify-center overflow-x-hidden rounded-[42px] bg-[#060e20] px-4 py-10 shadow-[0_30px_90px_rgba(1,6,18,0.55)] md:px-8">
        <div className="w-full max-w-md">{children}</div>
      </main>
    );
  }

  return (
    /*
      Unified Cinematic Shell:
      - Rounded corners increased to 42px for the premium fluid shape.
      - bg-[#050816] environment.
      - max-w expanded to 1640px.
    */
    <div
      className="relative mx-auto min-h-[calc(100vh-1rem)] max-w-[1640px] overflow-hidden rounded-[42px] bg-[#050816] shadow-[0_40px_100px_rgba(0,0,0,0.7)]"
      style={{
        boxShadow: "0 40px 100px rgba(0,0,0,0.7), 0 0 0 1px rgba(139,226,232,0.05)",
      }}
    >
      <Sidebar />
      
      {/* 
        MAIN CINEMATIC DASHBOARD SURFACE (RESTORED)
        - Floating container feel with bg-[#070B17]/80 glass.
        - Shifted left to ml-[250px] to dock seamlessly with sidebar.
        - Large 42px curvature on all sides.
      */}
      <main 
        className={`relative flex min-w-0 flex-1 flex-col overflow-x-hidden transition-all duration-500 ${
          isDashboard 
            ? "lg:ml-[250px] lg:mr-4 lg:my-4 lg:rounded-[42px] bg-[#070B17]/80 backdrop-blur-3xl border border-white/5 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]" 
            : "lg:pl-64"
        }`}
      >
        {/* Cinematic halo — dashboard page ONLY */}
        {isDashboard && <DashboardHalo />}

        {/* 
          ATMOSPHERIC BLEND OVERLAY (Dashboard Only)
          Feathers the left edge of the dashboard surface to dissolve into the sidebar's glass.
        */}
        {isDashboard && (
          <div 
            aria-hidden="true"
            className="pointer-events-none absolute inset-y-0 left-0 z-10 w-32"
            style={{
              background: "linear-gradient(to right, #070B17 0%, rgba(7,11,23,0) 100%)",
              opacity: 0.6
            }}
          />
        )}

        <div className="relative z-20 flex flex-col">
          <Header />
          <div className={`mx-auto w-full ${isDashboard ? "max-w-[1360px] px-6 py-8 md:px-12" : "max-w-[1160px] px-4 py-5 md:px-6 md:py-6 xl:px-7"}`}>
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
