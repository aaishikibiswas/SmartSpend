type Props = {
  context?: string;
};

export default function AIChatbot({ context }: Props) {
  return (
    <div className="glass-card p-5 rounded-2xl flex flex-col gap-3">
      <h3 className="text-lg font-semibold">AI Assistant</h3>

      <div className="bg-[#020617] p-3 rounded-lg text-sm text-gray-300">
        {context || "Ask anything about your spending, savings, or predictions..."}
      </div>

      <input
        placeholder="Type your question..."
        className="bg-[#020617] border border-purple-500/20 p-2 rounded-lg text-sm outline-none"
      />
    </div>
  );
}
