"use client";

import SidebarFinancialSimulator from "@/components/SidebarFinancialSimulator";

export default function SimulatorPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-4 py-6">
      <div>
        <h1 className="text-3xl font-bold text-[#dee5ff]">Financial Simulator</h1>
        <p className="mt-2 text-sm text-[#a3aac4]">Model how income and expense changes can affect savings and risk.</p>
      </div>
      <SidebarFinancialSimulator />
    </div>
  );
}
