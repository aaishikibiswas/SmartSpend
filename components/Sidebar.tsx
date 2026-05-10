"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bell, LayoutDashboard, LogOut, PieChart, ReceiptText, Target, UserCircle2, Wallet } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Transactions", href: "/transactions", icon: ReceiptText },
  { name: "Wallet", href: "/wallet", icon: Wallet },
  { name: "Goals", href: "/goals", icon: Target },
  { name: "Budget", href: "/budget", icon: PieChart },
  { name: "Alerts", href: "/alerts", icon: Bell },
  { name: "Simulator", href: "/simulator", icon: BarChart3 },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const avatarSeed = user?.avatar_seed || "guest";
  const displayName = user?.full_name || "Guest User";
  const subtitle = user?.plan || "Sign in to sync";

  return (
    <aside className="z-50 w-full border-b border-[#dee5ff]/10 bg-[#060e20]/40 backdrop-blur-3xl lg:fixed lg:inset-y-0 lg:left-0 lg:h-screen lg:w-64 lg:shrink-0 lg:border-b-0">
      <div className="flex h-full flex-col justify-between">
        <div>
          <div className="p-8">
            <Link href="/" className="block">
              <div>
                <h1 className="text-xl font-bold tracking-tight text-[#dee5ff]">SmartSpend</h1>
                <p className="mt-1 text-[10px] uppercase tracking-[0.2em] text-[#a3aac4]">AI Financial Control Center</p>
              </div>
            </Link>
          </div>

          <nav className="space-y-2 px-4 text-sm font-medium tracking-tight">
            {navItems.map((item) => {
              const isActive = pathname === item.href || (pathname.startsWith(item.href) && item.href !== "/");
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 pl-4 py-3 transition-all duration-200 ${
                    isActive
                      ? "border-l-2 border-[#6366f1] bg-[#091328] font-bold text-[#dee5ff]"
                      : "rounded-r-xl text-[#a3aac4] hover:bg-[#0f1930] hover:text-[#dee5ff]"
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          <div className="rounded-xl border border-[#6d758c]/20 bg-[rgba(25,37,64,0.4)] p-4 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 overflow-hidden rounded-full border border-[#40485d]/30 bg-[#192540]">
                <img src={`https://i.pravatar.cc/150?u=${avatarSeed}`} alt="User Workspace Logo" width={40} height={40} className="h-full w-full object-cover" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-[#dee5ff]">{displayName}</p>
                <p className="truncate text-[10px] text-[#a3aac4]">{subtitle}</p>
              </div>
            </div>

            <div className="mt-4 flex gap-2">
              {isAuthenticated ? (
                <>
                  <Link
                    href="/profile"
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-[#40485d]/30 bg-[#11192c] px-3 py-2 text-[11px] font-semibold text-[#dee5ff] transition-colors hover:bg-[#182238]"
                  >
                    <UserCircle2 className="h-3.5 w-3.5" />
                    Profile
                  </Link>
                  <button
                    type="button"
                    onClick={() => void logout()}
                    className="flex items-center justify-center gap-2 rounded-xl border border-[#40485d]/30 bg-[#11192c] px-3 py-2 text-[11px] font-semibold text-[#dee5ff] transition-colors hover:bg-[#182238]"
                  >
                    <LogOut className="h-3.5 w-3.5" />
                  </button>
                </>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
