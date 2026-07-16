import * as React from "react";

import { cn } from "../lib/cn";
import { screenTokens } from "../theme/screen-tokens";

export type OrbitItem = {
  label: string;
  value: string | number;
  unit?: string;
};

export type ScreenHeroCenterProps = {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  orbitItems: OrbitItem[];
  className?: string;
  theme?: "dark" | "light";
};

const orbitPositions = [
  "left-[8%] top-[12%]",
  "right-[8%] top-[12%]",
  "left-[4%] top-1/2 -translate-y-1/2",
  "right-[4%] top-1/2 -translate-y-1/2",
  "left-[8%] bottom-[12%]",
  "right-[8%] bottom-[12%]",
] as const;

/**
 * 中央主视觉 + 6 环绕指标位 — L2 Hero 布局核心原子。
 * @see prd/data-screens/atoms.md#task-ds-a09
 */
export function ScreenHeroCenter({
  title,
  subtitle,
  orbitItems,
  className,
  theme = "dark",
}: ScreenHeroCenterProps) {
  const isDark = theme === "dark";
  const items = orbitItems.slice(0, 6);

  return (
    <div
      className={cn("relative min-h-[280px] w-full", className)}
      data-screen-hero-center
      aria-label="中央主视觉"
    >
      <div
        aria-hidden
        className={cn(
          "pointer-events-none absolute left-1/2 top-1/2 h-44 w-44 -translate-x-1/2 -translate-y-1/2 rounded-full border",
          isDark
            ? "border-cyan-400/25 shadow-[0_0_40px_rgba(34,211,238,0.12)]"
            : "border-blue-300/40 shadow-[0_0_24px_rgba(59,130,246,0.1)]",
        )}
      />
      <div
        aria-hidden
        className={cn(
          "pointer-events-none absolute left-1/2 top-1/2 h-56 w-56 -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed",
          isDark ? "border-cyan-500/15" : "border-slate-300/60",
        )}
      />

      <div className="absolute left-1/2 top-1/2 z-10 flex w-[42%] -translate-x-1/2 -translate-y-1/2 flex-col items-center text-center">
        <h2
          className={cn(
            "text-xl font-bold tracking-wide",
            isDark ? "text-cyan-50" : "text-slate-800",
          )}
        >
          {title}
        </h2>
        {subtitle ? (
          <p className={cn("mt-1 text-xs", isDark ? "text-white/60" : "text-slate-500")}>
            {subtitle}
          </p>
        ) : null}
      </div>

      {items.map((item, index) => (
        <div
          key={`${item.label}-${index}`}
          className={cn(
            "absolute z-10 min-w-[88px] rounded-lg border px-2 py-1.5 text-center backdrop-blur-sm",
            orbitPositions[index],
            isDark
              ? "border-cyan-500/30 bg-slate-900/70 shadow-[0_0_10px_rgba(34,211,238,0.08)]"
              : "border-slate-200 bg-white/90 shadow-sm",
          )}
        >
          <p className={cn("text-[10px]", isDark ? screenTokens.kpiLabel : "text-slate-500")}>
            {item.label}
          </p>
          <p className={cn("text-sm font-semibold tabular-nums", isDark ? "text-white" : "text-slate-800")}>
            {item.value}
            {item.unit ? (
              <span className={cn("ml-0.5 text-[10px] font-normal", isDark ? "text-white/50" : "text-slate-400")}>
                {item.unit}
              </span>
            ) : null}
          </p>
        </div>
      ))}
    </div>
  );
}
