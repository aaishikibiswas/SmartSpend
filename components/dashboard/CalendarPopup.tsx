"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface CalendarPopupProps {
  selectedDate: Date | null;
  onSelect: (date: Date) => void;
  onClose: () => void;
}

export default function CalendarPopup({ selectedDate, onSelect, onClose }: CalendarPopupProps) {
  const today = new Date();
  const [viewDate, setViewDate] = useState(selectedDate || today);

  const month = viewDate.getMonth();
  const year = viewDate.getFullYear();

  const firstDayOfMonth = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const prevMonth = () => setViewDate(new Date(year, month - 1, 1));
  const nextMonth = () => setViewDate(new Date(year, month + 1, 1));

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const days = [];
  // Fill empty days for the first week
  for (let i = 0; i < firstDayOfMonth; i++) {
    days.push(<div key={`empty-${i}`} className="h-8 w-8" />);
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(year, month, d);
    const isSelected = selectedDate?.toDateString() === date.toDateString();
    const isToday = today.toDateString() === date.toDateString();
    const isPast = date < new Date(today.setHours(0, 0, 0, 0)) && !isToday;

    days.push(
      <button
        key={d}
        onClick={() => {
          if (!isPast) {
            onSelect(date);
            onClose();
          }
        }}
        disabled={isPast}
        className={`h-8 w-8 rounded-lg text-[11px] font-bold transition-all ${
          isSelected
            ? "bg-[#7B6CF6] text-white shadow-[0_0_10px_rgba(123,108,246,0.5)]"
            : isPast
            ? "text-[#4B5563] cursor-not-allowed"
            : isToday
            ? "border border-[#8BE2E8] text-[#8BE2E8]"
            : "text-[#B7BDD9] hover:bg-white/10 hover:text-white"
        }`}
      >
        {d}
      </button>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: 10 }}
      className="absolute bottom-full left-0 mb-2 z-50 w-64 rounded-2xl border border-white/10 bg-[#10182E]/95 p-4 backdrop-blur-xl shadow-[0_10px_40px_rgba(0,0,0,0.5)]"
    >
      <div className="mb-4 flex items-center justify-between">
        <h4 className="text-sm font-bold text-white">
          {monthNames[month]} {year}
        </h4>
        <div className="flex gap-1">
          <button onClick={prevMonth} className="rounded-md p-1 hover:bg-white/5 text-[#B7BDD9]">
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button onClick={nextMonth} className="rounded-md p-1 hover:bg-white/5 text-[#B7BDD9]">
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-1 mb-2">
        {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((d) => (
          <div key={d} className="text-center text-[10px] font-bold uppercase tracking-tighter text-[#4B5563]">
            {d}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {days}
      </div>
    </motion.div>
  );
}
