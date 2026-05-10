"use client";

/**
 * DashboardHalo — cinematic ambient glow layer.
 * Renders ONLY on the dashboard page.
 * 5 GPU-accelerated CSS gradient blobs that drift, breathe, and morph.
 * pointer-events:none — fully non-interactive.
 */
export default function DashboardHalo() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        height: "560px",        /* covers navbar + upper dashboard cards */
        zIndex: 0,
        pointerEvents: "none",
        overflow: "visible",
      }}
    >
      {/* 1. Massive cyan bloom — left side */}
      <div style={{
        position: "absolute",
        top: "-120px",
        left: "-80px",
        width: "700px",
        height: "520px",
        borderRadius: "50%",
        background: "radial-gradient(ellipse at 35% 45%, rgba(111,231,255,0.72) 0%, rgba(139,226,232,0.45) 35%, rgba(139,226,232,0.18) 58%, transparent 76%)",
        filter: "blur(34px)",
        animation: "halo-drift-cyan 5.2s ease-in-out infinite, halo-breathe 2.8s ease-in-out infinite",
        willChange: "transform, opacity",
      }} />

      {/* 2. Large lavender bloom — right side */}
      <div style={{
        position: "absolute",
        top: "-100px",
        right: "-80px",
        width: "660px",
        height: "500px",
        borderRadius: "50%",
        background: "radial-gradient(ellipse at 65% 40%, rgba(168,151,255,0.72) 0%, rgba(125,117,255,0.42) 35%, rgba(125,117,255,0.16) 58%, transparent 76%)",
        filter: "blur(36px)",
        animation: "halo-drift-lavender 6.4s ease-in-out infinite, halo-breathe 3.2s ease-in-out infinite 0.6s",
        willChange: "transform, opacity",
      }} />

      {/* 3. Wide indigo fog — center depth layer */}
      <div style={{
        position: "absolute",
        top: "-30px",
        left: "10%",
        width: "80%",
        height: "380px",
        borderRadius: "50%",
        background: "radial-gradient(ellipse at center, rgba(125,117,255,0.34) 0%, rgba(139,226,232,0.18) 48%, transparent 78%)",
        filter: "blur(50px)",
        animation: "halo-morph-center 5.8s ease-in-out infinite",
        willChange: "transform, opacity",
        transform: "translate(0,0)",
      }} />

      {/* 4. Search-bar corona */}
      <div style={{
        position: "absolute",
        top: "20px",
        left: "16%",
        width: "55%",
        height: "72px",
        borderRadius: "9999px",
        background: "radial-gradient(ellipse at center, rgba(139,226,232,0.34) 0%, transparent 78%)",
        filter: "blur(16px)",
        animation: "halo-breathe 2s ease-in-out infinite 0.3s",
        willChange: "opacity",
      }} />

      {/* 5. Mauve bleed — 340px below navbar into upper dashboard */}
      <div style={{
        position: "absolute",
        top: "40px",
        left: "8%",
        width: "84%",
        height: "340px",
        borderRadius: "50%",
        background: "radial-gradient(ellipse at center top, rgba(167,136,163,0.32) 0%, rgba(125,117,255,0.18) 50%, transparent 80%)",
        filter: "blur(44px)",
        animation: "halo-mauve-bottom 7s ease-in-out infinite 1s, halo-breathe 3.6s ease-in-out infinite",
        willChange: "transform, opacity",
      }} />
      <div className="dashboard-halo-particles" />
    </div>
  );
}
