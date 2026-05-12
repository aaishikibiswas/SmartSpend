"use client";

import React, { useState, useMemo } from "react";
import { 
  Calculator, 
  ChevronDown, 
  ChevronUp, 
  CreditCard, 
  Info, 
  Landmark, 
  Calendar, 
  Sparkles, 
  TrendingUp,
  Percent,
  Clock,
  Wallet
} from "lucide-react";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from "recharts";
import { motion, AnimatePresence } from "framer-motion";

// --- HELPERS ---

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value).replace("₹", "₹ ");
};

const formatDateLong = (dateStr: string) => {
  if (!dateStr) return "N/A";
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
};

const formatCompact = (value: number) => {
  if (value >= 10000000) return `₹ ${(value / 10000000).toFixed(1)} Cr`;
  if (value >= 100000) return `₹ ${(value / 100000).toFixed(1)} L`;
  return formatCurrency(value);
};

// --- COMPONENTS ---

export default function LoanSimulator() {
  // Input States
  const [loanAmount, setLoanAmount] = useState(2500000);
  const [interestRate, setInterestRate] = useState(8.5);
  const [tenure, setTenure] = useState(20);
  const [processingFee, setProcessingFee] = useState(15000);
  const [startDate, setStartDate] = useState(new Date().toISOString().split("T")[0]);
  const [frequency, setFrequency] = useState("Monthly");
  const [includeInsurance, setIncludeInsurance] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeTab, setActiveTab] = useState<"calc" | "prepay">("calc");

  // Calculations
  const stats = useMemo(() => {
    // Calculate principal including insurance if enabled (1.5% premium)
    const insurancePremium = includeInsurance ? loanAmount * 0.015 : 0;
    const P = loanAmount + insurancePremium;
    const r = interestRate / 12 / 100;
    const n = tenure * 12;

    const emi = (P * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
    const totalPayment = (emi * n) + processingFee;
    const totalInterest = totalPayment - P - processingFee;
    
    const mockMonthlyIncome = 150000;
    const affordability = (emi / mockMonthlyIncome) * 100;

    const amortization = [];
    let balance = P;
    for (let year = 1; year <= tenure; year++) {
      let interestYear = 0;
      let principalYear = 0;
      for (let month = 1; month <= 12; month++) {
        const interest = balance * r;
        const principal = emi - interest;
        interestYear += interest;
        principalYear += principal;
        balance -= principal;
      }
      amortization.push({
        year: `Year ${year}`,
        principal: Math.round(principalYear),
        interest: Math.round(interestYear),
        balance: Math.max(0, Math.round(balance)),
      });
    }

    return {
      emi: Math.round(emi),
      totalPayment: Math.round(totalPayment),
      totalInterest: Math.round(totalInterest),
      affordability,
      amortization,
      insurancePremium
    };
  }, [loanAmount, interestRate, tenure, processingFee, includeInsurance]);

  const firstEmiDate = useMemo(() => {
    if (!startDate) return "N/A";
    const date = new Date(startDate);
    const increment = frequency === "Monthly" ? 1 : 3;
    date.setMonth(date.getMonth() + increment);
    return date.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }, [startDate, frequency]);

  const pieData = [
    { name: "Principal", value: loanAmount, color: "#7B6CF6" },
    { name: "Interest", value: stats.totalInterest, color: "#8BE2E8" },
  ];

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[400px_1fr]">
      
      {/* --- LEFT PANEL: CONTROLS --- */}
      <div className="space-y-6">
        <div className="glass-card flex flex-col gap-6 p-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#7B6CF6] to-[#a855f7] text-white shadow-lg shadow-[#7B6CF6]/20">
              <Calculator className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Loan EMI Simulator</h2>
              <p className="text-xs text-[#B7BDD9]">Plan your loan and see how it fits.</p>
            </div>
          </div>

          {/* Segmented Tabs */}
          <div className="flex rounded-xl bg-white/5 p-1">
            <button 
              onClick={() => setActiveTab("calc")}
              className={`flex-1 rounded-lg py-2 text-xs font-bold transition-all ${activeTab === "calc" ? "bg-[#7B6CF6] text-white shadow-md" : "text-[#B7BDD9] hover:text-white"}`}
            >
              EMI Calculator
            </button>
            <button 
              onClick={() => setActiveTab("prepay")}
              className={`flex-1 rounded-lg py-2 text-xs font-bold transition-all ${activeTab === "prepay" ? "bg-[#7B6CF6] text-white shadow-md" : "text-[#B7BDD9] hover:text-white"}`}
            >
              Prepayment Impact
            </button>
          </div>

          {/* Input Controls */}
          <div className="space-y-8 py-2">
            
            {/* Loan Amount */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-[#7D839E]">Loan Amount</label>
                <span className="text-lg font-black text-[#8BE2E8]">{formatCompact(loanAmount)}</span>
              </div>
              <div className="relative h-6 w-full">
                <input 
                  type="range"
                  min={100000}
                  max={50000000}
                  step={50000}
                  value={loanAmount}
                  onChange={(e) => setLoanAmount(Number(e.target.value))}
                  className="absolute top-0 z-10 w-full cursor-pointer accent-[#7B6CF6]"
                />
                <div className="absolute top-[10px] h-1 w-full rounded-full bg-white/5" />
                <div 
                  className="absolute top-[10px] h-1 rounded-full bg-gradient-to-r from-[#7B6CF6] to-[#8BE2E8] blur-[1px]"
                  style={{ width: `${(loanAmount / 50000000) * 100}%` }}
                />
              </div>
            </div>

            {/* Interest Rate */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-[#7D839E]">Interest Rate (P.A.)</label>
                <span className="text-lg font-black text-[#8BE2E8]">{interestRate}%</span>
              </div>
              <div className="relative h-6 w-full">
                <input 
                  type="range"
                  min={5}
                  max={20}
                  step={0.1}
                  value={interestRate}
                  onChange={(e) => setInterestRate(Number(e.target.value))}
                  className="absolute top-0 z-10 w-full cursor-pointer accent-[#7B6CF6]"
                />
                <div className="absolute top-[10px] h-1 w-full rounded-full bg-white/5" />
                <div 
                  className="absolute top-[10px] h-1 rounded-full bg-gradient-to-r from-[#7B6CF6] to-[#8BE2E8] blur-[1px]"
                  style={{ width: `${((interestRate - 5) / 15) * 100}%` }}
                />
              </div>
            </div>

            {/* Loan Tenure */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-[#7D839E]">Loan Tenure</label>
                <span className="text-lg font-black text-[#8BE2E8]">{tenure} Years</span>
              </div>
              <div className="relative h-6 w-full">
                <input 
                  type="range"
                  min={1}
                  max={30}
                  step={1}
                  value={tenure}
                  onChange={(e) => setTenure(Number(e.target.value))}
                  className="absolute top-0 z-10 w-full cursor-pointer accent-[#7B6CF6]"
                />
                <div className="absolute top-[10px] h-1 w-full rounded-full bg-white/5" />
                <div 
                  className="absolute top-[10px] h-1 rounded-full bg-gradient-to-r from-[#7B6CF6] to-[#8BE2E8] blur-[1px]"
                  style={{ width: `${(tenure / 30) * 100}%` }}
                />
              </div>
            </div>

            {/* Processing Fee */}
            <div className="space-y-3">
              <label className="text-xs font-bold uppercase tracking-wider text-[#7D839E]">Processing Fee</label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#B7BDD9]">₹</span>
                <input 
                  type="number"
                  value={processingFee}
                  onChange={(e) => setProcessingFee(Number(e.target.value))}
                  className="h-12 w-full rounded-xl border border-white/8 bg-[#10182E] pl-8 pr-4 text-sm font-bold text-white outline-none focus:border-[#7B6CF6]/50 transition-all"
                />
              </div>
            </div>

            {/* Advanced Options */}
            <div className="pt-2">
              <button 
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-[#B7BDD9] hover:text-white transition-colors"
              >
                Advanced Options
                {showAdvanced ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
              
              <AnimatePresence>
                {showAdvanced && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden space-y-4 pt-4"
                  >
                    <div className="grid grid-cols-2 gap-4">
                       <div className="space-y-2">
                         <label className="text-[10px] font-bold text-[#7D839E] uppercase">Start Date</label>
                         <input 
                           type="date" 
                           value={startDate}
                           onChange={(e) => setStartDate(e.target.value)}
                           className="h-10 w-full rounded-lg bg-white/5 border border-white/10 px-3 text-xs text-white outline-none focus:border-[#7B6CF6]/50" 
                         />
                       </div>
                       <div className="space-y-2">
                         <label className="text-[10px] font-bold text-[#7D839E] uppercase">Frequency</label>
                         <select 
                           value={frequency}
                           onChange={(e) => setFrequency(e.target.value)}
                           className="h-10 w-full rounded-lg bg-white/5 border border-white/10 px-3 text-xs text-white outline-none focus:border-[#7B6CF6]/50"
                         >
                           <option>Monthly</option>
                           <option>Quarterly</option>
                         </select>
                       </div>
                    </div>
                    <label className="flex items-center gap-3 cursor-pointer group select-none">
                      <div className={`h-5 w-5 rounded border flex items-center justify-center transition-all ${includeInsurance ? "bg-[#7B6CF6] border-[#7B6CF6]" : "border-white/10 bg-white/5 group-hover:border-[#7B6CF6]/50"}`}>
                        <input 
                          type="checkbox" 
                          className="hidden" 
                          checked={includeInsurance}
                          onChange={(e) => setIncludeInsurance(e.target.checked)}
                        />
                        {includeInsurance && (
                          <motion.svg 
                            initial={{ scale: 0 }} 
                            animate={{ scale: 1 }} 
                            viewBox="0 0 24 24" 
                            className="h-3 w-3 text-white" 
                            fill="none" 
                            stroke="currentColor" 
                            strokeWidth="4"
                          >
                            <polyline points="20 6 9 17 4 12" />
                          </motion.svg>
                        )}
                      </div>
                      <span className="text-xs text-[#B7BDD9] group-hover:text-white transition-colors">Include Insurance</span>
                    </label>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        <div className="glass-card p-6 space-y-4">
           <div className="flex items-center gap-3 text-[#A897FF]">
             <Sparkles className="h-4 w-4" />
             <h4 className="text-sm font-bold">Simulator Insights</h4>
           </div>
           <p className="text-xs leading-relaxed text-[#B7BDD9]">
             Our AI analyzes your spending patterns to ensure your loan fits comfortably within your disposable income.
           </p>
        </div>
      </div>

      {/* --- RIGHT PANEL: ANALYTICS --- */}
      <div className="space-y-8">
        
        {/* Top Stats Cards */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-[1fr_240px]">
          
          <div className="glass-card flex flex-col justify-between p-8 relative overflow-hidden">
             {/* Background glow */}
             <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-[#7B6CF6]/5 blur-[100px]" />
             
             <div>
               <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#7D839E]">Your Monthly EMI</p>
               <h3 className="mt-4 text-5xl font-black tracking-tight text-white">
                 {formatCurrency(stats.emi)}
                 <span className="text-lg font-bold text-[#B7BDD9]"> /month</span>
               </h3>
             </div>

             <div className="mt-8 flex items-center gap-4">
               <div className="flex items-center gap-2 rounded-full bg-emerald-500/10 px-4 py-1.5 text-xs font-bold text-emerald-400 border border-emerald-500/20">
                 <TrendingUp className="h-3 w-3" />
                 {stats.affordability.toFixed(1)}% of your monthly income
               </div>
               <span className="text-[10px] font-bold uppercase tracking-widest text-[#7D839E]">Based on local trends</span>
             </div>
          </div>

          <div className="glass-card flex flex-col items-center justify-center p-6 gap-4">
            <p className="text-[10px] font-bold uppercase tracking-widest text-[#7D839E]">EMI Health Gauge</p>
            <div className="relative h-24 w-40">
               {/* Gauge Arc */}
               <svg viewBox="0 0 100 50" className="w-full">
                 <path d="M10 50 A 40 40 0 0 1 90 50" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" strokeLinecap="round" />
                 <path 
                   d="M10 50 A 40 40 0 0 1 90 50" 
                   fill="none" 
                   stroke="url(#gaugeGradient)" 
                   strokeWidth="8" 
                   strokeLinecap="round"
                   strokeDasharray="125.6"
                   strokeDashoffset={125.6 * (1 - Math.min(stats.affordability, 50) / 50)}
                 />
                 <defs>
                   <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                     <stop offset="0%" stopColor="#8BE2E8" />
                     <stop offset="50%" stopColor="#7B6CF6" />
                     <stop offset="100%" stopColor="#ff7a98" />
                   </linearGradient>
                 </defs>
               </svg>
               {/* Needle */}
               <div 
                 className="absolute bottom-0 left-1/2 h-16 w-1 origin-bottom bg-white transition-transform duration-1000 ease-out shadow-[0_0_10px_white]"
                 style={{ transform: `translateX(-50%) rotate(${ (Math.min(stats.affordability, 50) / 50) * 180 - 90 }deg)` }}
               />
               <div className="absolute bottom-[-4px] left-1/2 h-4 w-4 -translate-x-1/2 rounded-full bg-white shadow-lg" />
            </div>
            <div className="text-center">
              <p className={`text-sm font-black uppercase tracking-widest ${stats.affordability < 25 ? "text-emerald-400" : stats.affordability < 40 ? "text-amber-400" : "text-rose-400"}`}>
                {stats.affordability < 25 ? "Excellent" : stats.affordability < 40 ? "Moderate" : "Risky"}
              </p>
              <p className="mt-1 text-[9px] font-bold text-[#7D839E]">Ideal: Below 25%</p>
            </div>
          </div>

        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-6 lg:grid-cols-4">
          <MetricCard icon={Wallet} label="Total Interest" value={formatCurrency(stats.totalInterest)} desc="Over loan period" color="purple" />
          <MetricCard icon={Landmark} label="Total Payment" value={formatCurrency(stats.totalPayment)} desc="Principal + Interest" color="cyan" />
          <MetricCard icon={Clock} label="Loan Tenure" value={`${tenure} Years`} desc={`${tenure * 12} Months`} color="purple" />
          <MetricCard icon={CreditCard} label="Principal Amount" value={formatCurrency(loanAmount)} desc="Initial borrowing" color="cyan" />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 gap-8 xl:grid-cols-[1fr_300px]">
          
          <div className="glass-card p-8">
            <div className="mb-8 flex items-center justify-between">
              <h4 className="text-lg font-bold text-white">Amortization Overview</h4>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#7B6CF6]" />
                  <span className="text-[10px] font-bold text-[#B7BDD9] uppercase">Principal</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#8BE2E8]" />
                  <span className="text-[10px] font-bold text-[#B7BDD9] uppercase">Interest</span>
                </div>
              </div>
            </div>

            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.amortization}>
                  <defs>
                    <linearGradient id="pColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7B6CF6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#7B6CF6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="iColor" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8BE2E8" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#8BE2E8" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis 
                    dataKey="year" 
                    stroke="#4B5563" 
                    fontSize={10} 
                    tickLine={false} 
                    axisLine={false} 
                    dy={10}
                  />
                  <YAxis 
                    stroke="#4B5563" 
                    fontSize={10} 
                    tickLine={false} 
                    axisLine={false}
                    tickFormatter={(val) => `₹${val/100000}L`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="principal" stroke="#7B6CF6" strokeWidth={3} fillOpacity={1} fill="url(#pColor)" />
                  <Area type="monotone" dataKey="interest" stroke="#8BE2E8" strokeWidth={3} fillOpacity={1} fill="url(#iColor)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-card flex flex-col items-center justify-center p-8">
            <h4 className="mb-8 text-sm font-bold uppercase tracking-[0.2em] text-[#7D839E]">EMI Breakdown</h4>
            <div className="relative h-48 w-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-xl font-black text-white">{formatCompact(stats.emi)}</p>
                <p className="text-[8px] font-bold uppercase tracking-widest text-[#7D839E]">Monthly EMI</p>
              </div>
            </div>
            
            <div className="mt-8 w-full space-y-3">
               <div className="flex items-center justify-between">
                 <div className="flex items-center gap-2">
                   <div className="h-2 w-2 rounded-full bg-[#7B6CF6]" />
                   <span className="text-xs font-semibold text-[#B7BDD9]">Principal</span>
                 </div>
                 <span className="text-xs font-bold text-white">{((loanAmount / stats.totalPayment) * 100).toFixed(0)}%</span>
               </div>
               <div className="flex items-center justify-between">
                 <div className="flex items-center gap-2">
                   <div className="h-2 w-2 rounded-full bg-[#8BE2E8]" />
                   <span className="text-xs font-semibold text-[#B7BDD9]">Interest</span>
                 </div>
                 <span className="text-xs font-bold text-white">{((stats.totalInterest / stats.totalPayment) * 100).toFixed(0)}%</span>
               </div>
            </div>
          </div>

        </div>

        {/* Bottom Strip */}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="glass-card flex items-center gap-4 px-6 py-4">
             <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 text-[#8BE2E8]">
               <Calendar className="h-5 w-5" />
             </div>
             <div>
               <p className="text-[10px] font-bold uppercase tracking-widest text-[#7D839E]">First EMI Due On</p>
               <p className="text-sm font-black text-white">{firstEmiDate}</p>
             </div>
          </div>

          <div className="flex-1 lg:max-w-xl">
             <div className="relative overflow-hidden rounded-2xl border border-[#7B6CF6]/20 bg-gradient-to-r from-[#7B6CF6]/10 to-transparent p-4">
                <div className="flex items-start gap-3">
                   <Sparkles className="h-4 w-4 mt-0.5 text-[#7B6CF6]" />
                   <div>
                     <p className="text-xs text-white leading-relaxed">
                       <span className="font-bold text-[#A897FF]">Smart Tip:</span> If you increase your EMI by <span className="font-bold">₹2,000</span>, you can save <span className="font-bold text-emerald-400">₹4,12,850</span> in interest and reduce tenure by <span className="font-bold">3 years</span>.
                     </p>
                     <button className="mt-2 text-[10px] font-bold uppercase tracking-[0.15em] text-[#7B6CF6] hover:text-[#8B7DFF] transition-colors">
                       View Prepayment Impact →
                     </button>
                   </div>
                </div>
             </div>
          </div>
        </div>

      </div>
    </div>
  );
}

// --- SUB-COMPONENTS ---

function MetricCard({ icon: Icon, label, value, desc, color }: any) {
  const isPurple = color === "purple";
  return (
    <div className="glass-card group p-6 transition-all hover:bg-white/10">
      <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white/5 ${isPurple ? "text-[#7B6CF6]" : "text-[#8BE2E8]"} group-hover:scale-110 transition-transform`}>
        <Icon className="h-5 w-5" />
      </div>
      <p className="text-[10px] font-bold uppercase tracking-widest text-[#7D839E]">{label}</p>
      <p className="mt-2 text-lg font-black text-white">{value}</p>
      <p className="mt-1 text-[9px] font-medium text-[#4B5563]">{desc}</p>
    </div>
  );
}

function CustomTooltip({ active, payload }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-white/10 bg-[#0A0F1E]/90 p-4 backdrop-blur-xl shadow-2xl">
        <p className="mb-2 text-xs font-bold text-[#7D839E]">{payload[0].payload.year}</p>
        <div className="space-y-1">
          <div className="flex items-center justify-between gap-8">
            <span className="text-[10px] font-bold uppercase text-[#7B6CF6]">Principal</span>
            <span className="text-xs font-black text-white">{formatCurrency(payload[0].value)}</span>
          </div>
          <div className="flex items-center justify-between gap-8">
            <span className="text-[10px] font-bold uppercase text-[#8BE2E8]">Interest</span>
            <span className="text-xs font-black text-white">{formatCurrency(payload[1].value)}</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
}

function ArrowRight({ className }: { className?: string }) {
  return (
    <svg 
      className={className} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2.5" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    >
      <line x1="5" y1="12" x2="19" y2="12"></line>
      <polyline points="12 5 19 12 12 19"></polyline>
    </svg>
  );
}
