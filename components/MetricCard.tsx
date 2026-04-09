import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  trend: number; // positive or negative
  icon: LucideIcon;
  color?: "blue" | "green" | "red" | "purple";
  suffix?: string;
  compact?: boolean;
}

export default function MetricCard({ title, value, trend, icon: Icon, color = "purple", suffix, compact = false }: MetricCardProps) {
  const isPositive = trend >= 0;

  const colorStyles = {
    blue: "text-[#a3a6ff] bg-[#a3a6ff]/10",
    green: "text-[#ffa5d9] bg-[#ff8ed2]/10",
    red: "text-[#ff6e84] bg-[#ff6e84]/10",
    purple: "text-[#a88cfb] bg-[#a88cfb]/10",
  };

  return (
    <div className={`glass-card group relative overflow-hidden rounded-2xl ${compact ? "p-5" : "p-6"}`}>
      <div className="mb-4 flex items-start justify-between">
        <div className={`rounded-lg p-2 ${colorStyles[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
        
        <div className={`flex flex-col items-end ${isPositive ? "text-[#a3a6ff]" : "text-[#ff6e84]"}`}>
          <span className={`rounded-full px-2 py-1 text-xs font-bold ${isPositive ? "bg-[#a3a6ff]/10" : "bg-[#ff6e84]/10"}`}>
            {isPositive ? "+" : "-"}
            {Math.abs(trend)}%
          </span>
          <span className="mt-1 text-[8px] text-[#a3aac4]">vs last month</span>
        </div>
      </div>

      <div>
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-widest text-[#a3aac4]">{title}</h3>
        <p className="font-manrope text-2xl font-bold text-[#dee5ff]">{value}</p>
        {suffix ? <p className="mt-1 text-[11px] font-semibold text-[#a3aac4]">{suffix}</p> : null}
      </div>
    </div>
  );
}
