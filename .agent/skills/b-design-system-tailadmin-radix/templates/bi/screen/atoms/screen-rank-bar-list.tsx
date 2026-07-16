import * as React from "react";

import { cn } from "../lib/cn";

export type RankRow = {
  rank: number;
  label: string;
  value: number;
  max?: number;
};

export type ScreenRankBarListProps = {
  rows: RankRow[];
  orientation?: "horizontal";
  barGradient?: boolean;
  variant?: "dark" | "light";
};

export function ScreenRankBarList({
  rows,
  barGradient = true,
  variant = "dark",
}: ScreenRankBarListProps) {
  const isDark = variant === "dark";
  const maxValue = Math.max(...rows.map((row) => row.max ?? row.value), 1);

  return (
    <div className="space-y-2" data-screen-rank-bar-list>
      {rows.map((row) => {
        const width = Math.round((row.value / (row.max ?? maxValue)) * 100);
        return (
          <div
            key={`${row.rank}-${row.label}`}
            className={cn(
              "group rounded-md px-2 py-1.5 transition-colors",
              isDark ? "hover:bg-white/5" : "hover:bg-slate-50",
            )}
          >
            <div className="mb-1 flex items-center justify-between gap-2 text-xs">
              <span className={cn("truncate", isDark ? "text-white/80" : "text-slate-700")}>
                <span className="mr-2 opacity-60">#{row.rank}</span>
                {row.label}
              </span>
              <span className={cn("tabular-nums", isDark ? "text-cyan-200" : "text-slate-600")}>
                {row.value}
              </span>
            </div>
            <div className={cn("h-1.5 overflow-hidden rounded-full", isDark ? "bg-white/10" : "bg-slate-100")}>
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  barGradient
                    ? "bg-gradient-to-r from-cyan-400 to-transparent"
                    : isDark
                      ? "bg-cyan-400"
                      : "bg-blue-500",
                )}
                style={{ width: `${width}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
