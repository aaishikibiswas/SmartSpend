"use client";

import { Save, Sliders, Shield, BellRing, Settings as SettingsIcon } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex flex-col gap-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
          Settings
        </h1>
        <p className="text-gray-400 mt-2">Manage your budget preferences and account settings.</p>
      </div>

      <div className="flex gap-8">
        {/* Sidebar Nav */}
        <div className="w-48 xl:w-64 flex flex-col gap-2 shrink-0">
          <button className="flex items-center gap-3 px-4 py-3 bg-[#1A2035] text-white rounded-xl border border-[#2A324A] font-semibold transition-colors">
            <Sliders className="w-5 h-5 text-[#8B5CF6]" /> Budgets
          </button>
          <button className="flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl transition-colors">
            <BellRing className="w-5 h-5" /> Notifications
          </button>
          <button className="flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl transition-colors">
            <Shield className="w-5 h-5" /> Security
          </button>
          <button className="flex items-center gap-3 px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl transition-colors">
            <SettingsIcon className="w-5 h-5" /> General
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col gap-6">
          <div className="glass-card p-6">
            <h2 className="text-xl font-bold text-white mb-6">Global Budgets</h2>
            
            <div className="flex flex-col gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-400 mb-2">Monthly Budget</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 font-bold">₹</span>
                  <input 
                    type="number" 
                    defaultValue="50000"
                    className="w-full bg-[#0B0E14] border border-[#2A324A] text-white text-base rounded-xl pl-8 pr-4 py-3 outline-none focus:border-[#8B5CF6] transition-colors"
                  />
                </div>
                <p className="text-xs text-gray-500 mt-2">Your Prophet Engine will calibrate predictions based on this cap.</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-400 mb-2">Weekly Target Spend</label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 font-bold">₹</span>
                  <input 
                    type="number" 
                    defaultValue="11500"
                    className="w-full bg-[#0B0E14] border border-[#2A324A] text-white text-base rounded-xl pl-8 pr-4 py-3 outline-none focus:border-[#8B5CF6] transition-colors"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="glass-card p-6">
            <h2 className="text-xl font-bold text-white mb-6">Category Allocation</h2>
            
            <div className="flex flex-col gap-4">
              {[
                { name: "Housing", value: "20000" },
                { name: "Food & Dining", value: "12000" },
                { name: "Transport", value: "5000" },
                { name: "Entertainment", value: "8000" },
              ].map(cat => (
                <div key={cat.name} className="flex items-center gap-4">
                  <span className="w-32 text-sm text-gray-300 font-medium">{cat.name}</span>
                  <div className="relative flex-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 font-bold text-sm">₹</span>
                    <input 
                      type="number" 
                      defaultValue={cat.value}
                      className="w-full bg-[#0B0E14] border border-[#2A324A] text-white text-sm rounded-lg pl-8 pr-4 py-2 outline-none focus:border-[#8B5CF6] transition-colors"
                    />
                  </div>
                </div>
              ))}
            </div>

            <button className="mt-4 text-sm text-[#8B5CF6] hover:text-[#A78BFA] font-semibold transition-colors">+ Add Category Restriction</button>
          </div>

          <div className="flex justify-end mt-4">
            <button className="flex items-center gap-2 bg-[#8B5CF6] hover:bg-[#A78BFA] text-white px-6 py-3 rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(139,92,246,0.3)] hover:shadow-[0_0_25px_rgba(139,92,246,0.5)]">
              <Save className="w-5 h-5" /> Save Changes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
