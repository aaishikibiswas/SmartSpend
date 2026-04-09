type Props = {
  title: string;
  value: number;
  trend?: number;
};

export default function MetricCard({ title, value, trend }: Props) {
  const isPositive = trend && trend > 0;

  return (
    <div className="glass-card p-5 rounded-2xl flex flex-col gap-2">

      <span className="text-gray-400 text-sm">{title}</span>

      <div className="flex items-center justify-between">
        <span className="text-2xl font-bold text-white">
          ₹{value.toLocaleString()}
        </span>

        {trend !== undefined && (
          <span
            className={`text-sm ${
              isPositive ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {isPositive ? '▲' : '▼'} {Math.abs(trend)}%
          </span>
        )}
      </div>

    </div>
  );
}