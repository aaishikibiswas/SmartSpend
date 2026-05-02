"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";

export default function DashboardDeepLinkNavigator() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const focus = searchParams.get("focus");
    const hashTarget = window.location.hash ? window.location.hash.slice(1) : "";
    const targetId = focus || hashTarget;

    if (!targetId) {
      return;
    }

    const scrollToSection = () => {
      const target = document.getElementById(targetId);
      if (!target) {
        return;
      }
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    // Wait until client widgets settle and then scroll.
    const timer = window.setTimeout(scrollToSection, 150);
    return () => window.clearTimeout(timer);
  }, [searchParams]);

  return null;
}
