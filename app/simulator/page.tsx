import LoanSimulator from "@/components/LoanSimulator";

export default function SimulatorPage() {
  return (
    <div className="mx-auto w-full max-w-7xl space-y-8 px-8 py-10">
      <div className="flex flex-col gap-2">
        <h1 className="text-4xl font-black tracking-tight text-white">
          Loan EMI Intelligence
        </h1>
        <p className="text-base text-[#B7BDD9] max-w-2xl">
          Advanced financial simulation engine. Model your loan impact, analyze amortization schedules, and optimize your debt-to-income ratio with AI-driven insights.
        </p>
      </div>

      <LoanSimulator />
    </div>
  );
}
