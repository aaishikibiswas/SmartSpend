"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";

const AUTH_ROUTES = new Set(["/login", "/register"]);

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthRoute = AUTH_ROUTES.has(pathname);

  if (isAuthRoute) {
    return (
      <main className="mx-auto flex min-h-[calc(100vh-1rem)] max-w-[1460px] items-center justify-center overflow-x-hidden rounded-[28px] border border-[#27314d] bg-[#09101d] px-4 py-10 shadow-[0_30px_90px_rgba(1,6,18,0.55)] md:px-8">
        <div className="w-full max-w-md">{children}</div>
      </main>
    );
  }

  return (
    <div className="mx-auto min-h-[calc(100vh-1rem)] max-w-[1460px] overflow-hidden rounded-[28px] border border-[#27314d] bg-[#09101d] shadow-[0_30px_90px_rgba(1,6,18,0.55)] lg:flex">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-x-hidden">
        <div className="mx-auto max-w-[1160px] px-4 py-5 md:px-6 md:py-6 xl:px-7">{children}</div>
      </main>
    </div>
  );
}
