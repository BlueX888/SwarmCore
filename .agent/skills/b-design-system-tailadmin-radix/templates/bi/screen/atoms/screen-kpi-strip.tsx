import * as React from "react";

import { cn } from "../lib/cn";
import { screenTokens } from "../theme/screen-tokens";

export type KpiItem = {
  icon?: React.ReactNode;
  label: string;
  value: string | number;
  unit?: string;
};

export type ScreenKpiStripProps = {
  items: KpiItem[];
  columns?: 3 | 4 | 6;
  variant?: "dark" | "light";
};

export function ScreenKpiStrip({ items, columns = 3, variant = "dark" }: ScreenKpiStripProps) {
  const isDark = variant === "dark";
  const gridClass =
    columns === 6
      ? "grid-cols-6"
      : columns === 4
        ? "grid-cols-4"
        : "grid-cols-3";

  return (
    <div className={cn("grid gap-3", gridClass)} data-screen-kpi-strip>
      {items.map((item) => (
        <div
          key={item.label}
          className={cn(
            "flex items-center gap-3 rounded-lg border px-3 py-2",
            isDark ? "border-cyan-500/20 bg-slate-900/60" : "border-slate-200 bg-white",
          )}
        >
          {item.icon ? (
            <div className={cn("shrink-0", isDark ? "text-cyan-300" : "text-slate-500")}>
              {item.icon}
            </div>
          ) : null}
          <div className="min-w-0">
            <div className={cn(isDark ? screenTokens.kpiValue : "text-2xl font-bold tabular-nums text-slate-900")}>
              {item.value}
              {item.unit ? (
                <span className="ml-1 text-sm font-normal opacity-70">{item.unit}</span>
              ) : null}
            </div>
            <div className={cn(isDark ? screenTokens.kpiLabel : "text-xs text-slate-500")}>
              {item.label}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
