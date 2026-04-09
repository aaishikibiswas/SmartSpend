"use client";

import { useEffect, useState } from "react";
import { Laptop, PlusCircle, ShieldAlert, Plane } from "lucide-react";
import { apiClient, type GoalItem, type GoalSuggestion } from "@/lib/api-client";

function goalIcon(index: number) {
  return [Laptop, ShieldAlert, Plane][index] ?? Laptop;
}

function goalTone(index: number) {
  return [
    { text: "text-[#a3a6ff]", bg: "bg-[#a3a6ff]/10", bar: "bg-[#a3a6ff]" },
    { text: "text-[#a88cfb]", bg: "bg-[#a88cfb]/10", bar: "bg-[#a88cfb]" },
    { text: "text-[#ffa5d9]", bg: "bg-[#ffa5d9]/10", bar: "bg-[#ffa5d9]" },
  ][index] ?? { text: "text-[#a3a6ff]", bg: "bg-[#a3a6ff]/10", bar: "bg-[#a3a6ff]" };
}

function formatCurrency(value: number) {
  return `Rs${Math.round(value).toLocaleString()}`;
}

export default function GoalTracker({ suggestion }: { suggestion: GoalSuggestion }) {
  const [goals, setGoals] = useState<GoalItem[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await apiClient.getGoals();
        setGoals(res.data.slice(0, 3));
      } catch (error) {
        console.error(error);
        setGoals([]);
      }
    }

    load();
  }, []);

  return (
    <section className="glass-card rounded-[2rem] p-8">
      <div className="mb-6 flex items-center justify-between">
        <h4 className="font-bold text-[#dee5ff]">Financial Goals</h4>
        <PlusCircle className="h-5 w-5 cursor-pointer text-[#a3aac4] transition-colors hover:text-[#a3a6ff]" />
      </div>

      <div className="space-y-10">
        {goals.length === 0 ? <p className="text-sm text-[#a3aac4]">No goals yet.</p> : null}

        {goals.map((goal, index) => {
          const percent = Math.min(100, Math.round((goal.achieved / goal.target) * 100));
          const remaining = Math.max(0, goal.target - goal.achieved);
          const Icon = goalIcon(index);
          const tone = goalTone(index);

          return (
            <div key={goal.id} className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${tone.bg} ${tone.text}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold leading-tight text-[#dee5ff]">{goal.name}</p>
                    <p className="text-[10px] font-medium text-[#a3aac4]">
                      {formatCurrency(goal.achieved)} saved of {formatCurrency(goal.target)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-manrope text-lg font-black ${tone.text}`}>{percent}%</p>
                  <p className={`text-[9px] font-bold uppercase tracking-widest ${tone.text}`}>
                    {percent >= 90 ? "Nearly Goal" : percent >= 45 ? "On Track" : "Progress"}
                  </p>
                </div>
              </div>

              <div className="pt-1">
                <div className="flex h-3 overflow-hidden rounded-full border border-[#40485d]/10 bg-[#141f38] shadow-inner">
                  <div className={`${tone.bar} relative rounded-full`} style={{ width: `${percent}%` }}>
                    <div className="absolute bottom-0 right-0 top-0 w-2 bg-white/20 blur-[2px]" />
                  </div>
                </div>
                <div className="mt-2 flex justify-between">
                  <div className="flex flex-col">
                    <span className="text-[9px] font-bold uppercase tracking-tighter text-[#a3aac4]">Remaining</span>
                    <span className="text-xs font-bold text-[#dee5ff]">{formatCurrency(remaining)}</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[9px] font-bold uppercase tracking-tighter text-[#a3aac4]">Deadline</span>
                    <span className="text-xs font-bold text-[#dee5ff]">{goal.daysLeft} days left</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8">
        <div className="mb-4 rounded-2xl border border-[#40485d]/20 bg-[#10192d] px-4 py-3 text-xs text-[#a3aac4]">
          <span className="font-semibold text-[#dee5ff]">Suggested contribution:</span> Rs{Math.round(suggestion.recommendedContribution).toLocaleString()}
          <p className="mt-1">{suggestion.message}</p>
        </div>
        <button className="flex w-full items-center justify-center gap-2 rounded-2xl border border-[#40485d]/30 bg-[#192540] py-3 text-xs font-bold text-[#dee5ff] transition-colors hover:bg-[#1f2b49]">
          <PlusCircle className="h-4 w-4" /> Create New Goal
        </button>
      </div>
    </section>
  );
}
