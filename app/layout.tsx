import type { Metadata } from "next";
import "./globals.css";
import AuthProvider from "@/components/auth/AuthProvider";
import AppShell from "@/components/AppShell";
import { FinanceProvider } from "@/context/FinanceContext";
import { getCurrentUser } from "@/lib/auth-session";

export const metadata: Metadata = {
  title: "SmartSpend - AI Financial Analytics",
  description: "Your personalized AI financial control center",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await getCurrentUser();

  return (
    <html lang="en" className="min-h-full antialiased" suppressHydrationWarning>
      <body className="min-h-screen bg-[#050816] px-2 py-2 text-white [font-family:Inter,Segoe_UI,system-ui,sans-serif] lg:px-3 lg:py-3" suppressHydrationWarning>
        <AuthProvider initialUser={user}>
          <FinanceProvider key={user?.id ?? "anonymous"}>
            <AppShell>{children}</AppShell>
          </FinanceProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
