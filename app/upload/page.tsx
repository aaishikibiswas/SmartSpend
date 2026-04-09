"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UploadCloud, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api-client";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [resultCount, setResultCount] = useState(0);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);
  const router = useRouter();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setError("");
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError("");

    try {
      const res = await apiClient.uploadStatement(file);
      setResultCount(res.data.extractedTransactionsCount);
      setMessage(res.data.message);
      setIsComplete(true);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Upload failed.");
      setIsComplete(false);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-8 h-full justify-center py-10">
      <div className="text-center">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-[#8B5CF6]">
          AI Statement Analysis
        </h1>
        <p className="text-gray-400 mt-2">Upload your bank statements to extract insights and predict future spending.</p>
      </div>

      <div className="glass-card p-10 flex flex-col items-center">
        {!isProcessing && !isComplete ? (
          <>
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              className="w-full border-2 border-dashed border-[#2A324A] hover:border-[#8B5CF6] rounded-2xl p-12 flex flex-col items-center justify-center transition-all bg-[#0B0E14]/50 cursor-pointer group"
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.csv,.png,.jpg,.jpeg"
                className="hidden"
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null);
                  setError("");
                }}
              />
              <div className="p-4 bg-[#1A2035] rounded-full mb-4 group-hover:scale-110 transition-transform">
                <UploadCloud className="w-8 h-8 text-[#8B5CF6]" />
              </div>
              <p className="text-white font-bold text-lg mb-1">{file ? file.name : "Drag & drop file here"}</p>
              <p className="text-gray-500 text-sm">Supported formats: PDF, CSV, PNG, JPEG</p>
              {!file ? (
                <button
                  type="button"
                  className="mt-6 px-6 py-2 bg-[#1A2035] text-white rounded-xl border border-[#2A324A] hover:bg-[#8B5CF6] hover:border-[#8B5CF6] transition-colors"
                >
                  Browse Files
                </button>
              ) : null}
            </div>

            {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}

            <button
              onClick={handleUpload}
              disabled={!file}
              className={`mt-8 w-full py-3.5 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
                file
                  ? "bg-[#8B5CF6] hover:bg-[#A78BFA] text-white shadow-[0_0_20px_rgba(139,92,246,0.3)]"
                  : "bg-[#1A2035] text-gray-500 cursor-not-allowed"
              }`}
            >
              <Sparkles className="w-5 h-5" />
              Upload & Analyze
            </button>
          </>
        ) : isProcessing ? (
          <div className="py-20 flex flex-col items-center">
            <Loader2 className="w-12 h-12 text-[#8B5CF6] animate-spin mb-6" />
            <h3 className="text-xl font-bold text-white mb-2 text-center">Prophet Engine Processing...</h3>
            <p className="text-gray-400 text-sm text-center max-w-sm">
              Extracting transactions, categorizing merchants, and updating your financial forecast.
            </p>
          </div>
        ) : (
          <div className="py-16 flex flex-col items-center">
            <CheckCircle2 className="w-16 h-16 text-emerald-400 mb-6" />
            <h3 className="text-2xl font-bold text-white mb-2 text-center">Analysis Complete</h3>
            <p className="text-gray-400 text-sm text-center max-w-md mb-2">
              We successfully processed your statement and added {resultCount} new transactions to your dashboard.
            </p>
            <p className="text-gray-500 text-sm text-center max-w-md mb-8">{message}</p>
            <div className="flex gap-4">
              <button
                onClick={() => {
                  setIsComplete(false);
                  setFile(null);
                  setResultCount(0);
                  setMessage("");
                }}
                className="px-6 py-2.5 bg-[#1A2035] text-white rounded-xl border border-[#2A324A] hover:bg-[#2A324A] transition-colors"
              >
                Upload Another
              </button>
              <button
                onClick={() => {
                  router.push(`/?refresh=${Date.now()}`);
                  router.refresh();
                }}
                className="px-6 py-2.5 bg-[#8B5CF6] hover:bg-[#A78BFA] text-white rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(139,92,246,0.3)]"
              >
                View Insights
              </button>
              <Link
                href="/alerts"
                className="px-6 py-2.5 bg-transparent border border-[#2A324A] hover:border-[#8B5CF6] text-white rounded-xl font-bold transition-all"
              >
                View Alerts
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
