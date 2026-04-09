type Prediction = {
  predicted_expense?: number;
  risk_level?: string;
};

type Props = {
  prediction?: Prediction;
};

export default function AIPanel({ prediction }: Props) {
  return (
    <div className="glass-card p-5 rounded-2xl">
      <h3 className="text-lg font-semibold mb-3">AI Prediction</h3>

      {prediction ? (
        <div className="flex flex-col gap-2">
          <p>Predicted Expense: Rs. {prediction.predicted_expense?.toFixed(2)}</p>

          <p className={`${prediction.risk_level === "High" ? "text-red-400" : "text-green-400"}`}>
            Risk Level: {prediction.risk_level}
          </p>
        </div>
      ) : (
        <p className="text-gray-400">Loading AI insights...</p>
      )}
    </div>
  );
}
