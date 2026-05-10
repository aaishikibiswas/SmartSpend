"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  ArrowRight, 
  Landmark, 
  Lightbulb, 
  Shield, 
  TrendingUp, 
  Wallet, 
  Zap, 
  Target, 
  Activity,
  Sparkles
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AdviceItem {
  icon: string;
  label: string;
  title: string;
  body: string;
  href: string;
  action: string;
}

export default function SmartAdvice({ adviceItems = [] }: { adviceItems: AdviceItem[] }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  // Rotation logic: change every 10 seconds
  useEffect(() => {
    if (adviceItems.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % adviceItems.length);
    }, 10000);

    return () => clearInterval(interval);
  }, [adviceItems.length]);

  const getIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case "shield": return Shield;
      case "trending-up": return TrendingUp;
      case "landmark": return Landmark;
      case "wallet": return Wallet;
      case "zap": return Zap;
      case "target": return Target;
      case "activity": return Activity;
      default: return Lightbulb;
    }
  };

  if (!adviceItems || adviceItems.length === 0) {
    return (
      <div className="glass-card flex h-48 items-center justify-center rounded-[2rem] border border-white/10 bg-[#10182E]/60 p-8 backdrop-blur-xl">
        <div className="flex flex-col items-center gap-2 text-[#B7BDD9]">
          <Activity className="h-8 w-8 animate-pulse" />
          <p className="text-sm">Analyzing your financial data...</p>
        </div>
      </div>
    );
  }

  const currentAdvice = adviceItems[currentIndex];
  const Icon = getIcon(currentAdvice.icon);

  return (
    <section className="relative overflow-hidden glass-card rounded-[2rem] border border-white/10 bg-[#10182E]/60 p-8 backdrop-blur-xl transition-all duration-500">
      {/* Decorative background glow */}
      <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[#8BE2E8]/10 blur-[100px]" />
      <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-[#ec4899]/5 blur-[100px]" />

      <div className="relative z-10 flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#8BE2E8] to-[#a855f7] text-white shadow-lg shadow-[#8BE2E8]/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-xl font-bold tracking-tight text-white">Smart Insights</h3>
            <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-[#8BE2E8]">Real-time Advisory</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
            {adviceItems.map((_, idx) => (
                <div 
                    key={idx} 
                    className={`h-1 rounded-full transition-all duration-500 ${idx === currentIndex ? "w-8 bg-[#8BE2E8]" : "w-2 bg-[rgba(255,255,255,0.05)]"}`}
                />
            ))}
        </div>
      </div>

      <div className="relative min-h-[160px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ opacity: 0, y: 20, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -20, filter: "blur(10px)" }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="grid grid-cols-1 md:grid-cols-[auto_1fr] gap-8 items-start"
          >
            <div className="flex h-20 w-20 items-center justify-center rounded-[2rem] border border-white/5 bg-white/5 p-4 text-[#8BE2E8] backdrop-blur-sm shadow-inner">
              <Icon className="h-10 w-10" />
            </div>

            <div className="space-y-4">
              <div>
                <span className="mb-2 inline-block rounded-full bg-[#8BE2E8]/10 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-[#8BE2E8]">
                  {currentAdvice.label}
                </span>
                <h4 className="text-2xl font-bold text-[#F4F6FF] leading-tight">
                  {currentAdvice.title}
                </h4>
              </div>
              
              <p className="text-base text-[#B7BDD9] leading-relaxed max-w-2xl">
                {currentAdvice.body}
              </p>

              <div className="pt-4">
                <Link 
                  href={currentAdvice.href} 
                  className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full bg-white/5 px-6 py-3 text-sm font-bold text-white transition-all hover:bg-[#8BE2E8] hover:shadow-[0_0_20px_rgba(99,102,241,0.4)]"
                >
                  <span className="relative z-10">{currentAdvice.action}</span>
                  <ArrowRight className="relative z-10 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Progress bar for 10s timer */}
      <div className="absolute bottom-0 left-0 h-1 bg-[#8BE2E8]/20 w-full overflow-hidden">
        <motion.div 
            key={currentIndex}
            initial={{ width: "0%" }}
            animate={{ width: "100%" }}
            transition={{ duration: 10, ease: "linear" }}
            className="h-full bg-[#8BE2E8]"
        />
      </div>
    </section>
  );
}
