import * as React from "react";

import { cn } from "../lib/cn";

export type FunnelStage = {
  label: string;
  value: number;
  rate?: string;
};

export type ScreenFunnelChartProps = {
  stages: FunnelStage[];
  theme?: "dark" | "light";
  className?: string;
};

/**
 * 转化漏斗 — 4–6 阶段，右侧百分比标签，浅色 L4 运营看板适用。
 * @see prd/data-screens/atoms.md#task-ds-a07
 */
export function ScreenFunnelChart({
  stages,
  theme = "light",
  className,
}: ScreenFunnelChartProps) {
  const isDark = theme === "dark";
  const maxValue = Math.max(...stages.map((stage) => stage.value), 1);

  return (
    <div className={cn("space-y-2", className)} data-screen-funnel-chart>
      {stages.map((stage, index) => {
        const width = Math.max(28, Math.round((stage.value / maxValue) * 100));
        return (
          <div
            key={stage.label}
            className={cn(
              "group flex items-center gap-3 rounded-md px-2 py-1.5 transition-colors",
              isDark ? "hover:bg-white/5" : "hover:bg-slate-50",
            )}
            title={stage.rate ? `转化率 ${stage.rate}` : undefined}
          >
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <div className="flex items-center justify-between gap-2 text-xs">
                <span className={cn("truncate", isDark ? "text-white/80" : "text-slate-700")}>
                  {stage.label}
                </span>
                <span className={cn("tabular-nums", isDark ? "text-cyan-200" : "text-slate-500")}>
                  {stage.value.toLocaleString("zh-CN")}
                </span>
              </div>
              <div
                className={cn(
                  "h-6 overflow-hidden rounded-md transition-all",
                  isDark ? "bg-white/10" : "bg-slate-100",
                )}
              >
                <div
                  className={cn(
                    "flex h-full items-center justify-center rounded-md text-[10px] font-medium transition-all",
                    index === 0
                      ? "bg-gradient-to-r from-blue-500 to-blue-400 text-white"
                      : index === 1
                        ? "bg-gradient-to-r from-cyan-500 to-cyan-400 text-white"
                        : index === 2
                          ? "bg-gradient-to-r from-violet-500 to-violet-400 text-white"
                          : "bg-gradient-to-r from-amber-500 to-amber-400 text-white",
                  )}
                  style={{ width: `${width}%` }}
                >
                  <span className="opacity-0 group-hover:opacity-100">
                    {stage.rate ?? `${Math.round((stage.value / maxValue) * 100)}%`}
                  </span>
                </div>
              </div>
            </div>
            {stage.rate ? (
              <span
                className={cn(
                  "shrink-0 text-xs tabular-nums",
                  isDark ? "text-cyan-300" : "text-blue-600",
                )}
              >
                {stage.rate}
              </span>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
