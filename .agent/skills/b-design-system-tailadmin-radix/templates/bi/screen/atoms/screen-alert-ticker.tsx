import * as React from "react";

import { cn } from "../lib/cn";

export type AlertTickerStatus = "info" | "warning" | "critical" | "resolved";

export type AlertTickerRow = {
  id: string;
  time: string;
  location: string;
  content: string;
  status: AlertTickerStatus;
};

export type ScreenAlertTickerProps = {
  rows: AlertTickerRow[];
  /** scroll 垂直滚动；static 静态表 */
  mode?: "scroll" | "static";
  maxHeight?: number;
  theme?: "dark" | "light";
  className?: string;
};

const statusStyles: Record<AlertTickerStatus, { label: string; className: string }> = {
  info: { label: "提示", className: "text-cyan-300 bg-cyan-500/15" },
  warning: { label: "预警", className: "text-amber-300 bg-amber-500/15" },
  critical: { label: "紧急", className: "text-rose-300 bg-rose-500/15" },
  resolved: { label: "已处置", className: "text-emerald-300 bg-emerald-500/15" },
};

/**
 * 告警滚动/静态表 — 时间、地点、内容、状态色标。
 * @see prd/data-screens/atoms.md#task-ds-a15
 */
export function ScreenAlertTicker({
  rows,
  mode = "scroll",
  maxHeight = 160,
  theme = "dark",
  className,
}: ScreenAlertTickerProps) {
  const isDark = theme === "dark";
  const duplicated = mode === "scroll" ? [...rows, ...rows] : rows;

  return (
    <div
      data-screen-alert-ticker
      data-mode={mode}
      className={cn(
        "overflow-hidden rounded-md border",
        isDark ? "border-white/10 bg-white/[0.02]" : "border-slate-200 bg-white",
        className,
      )}
      style={{ maxHeight }}
    >
      <div
        className={cn(
          "grid grid-cols-[72px_88px_1fr_56px] gap-2 border-b px-2 py-1.5 text-[10px] font-medium uppercase tracking-wide",
          isDark ? "border-white/10 text-white/50" : "border-slate-100 text-slate-500",
        )}
      >
        <span>时间</span>
        <span>地点</span>
        <span>内容</span>
        <span>状态</span>
      </div>
      <div
        className={cn(mode === "scroll" && "animate-screen-alert-scroll")}
        style={mode === "scroll" ? { animationDuration: `${Math.max(rows.length * 2.5, 8)}s` } : undefined}
      >
        {duplicated.map((row, index) => {
          const status = statusStyles[row.status];
          return (
            <div
              key={`${row.id}-${index}`}
              className={cn(
                "grid grid-cols-[72px_88px_1fr_56px] gap-2 border-b px-2 py-2 text-xs last:border-b-0",
                isDark ? "border-white/5 text-white/85" : "border-slate-50 text-slate-700",
              )}
            >
              <span className="tabular-nums opacity-80">{row.time}</span>
              <span className="truncate">{row.location}</span>
              <span className="truncate">{row.content}</span>
              <span
                className={cn(
                  "inline-flex items-center justify-center rounded px-1 py-0.5 text-[10px] font-medium",
                  status.className,
                )}
              >
                {status.label}
              </span>
            </div>
          );
        })}
      </div>
      <style>{`
        @keyframes screen-alert-scroll {
          0% { transform: translateY(0); }
          100% { transform: translateY(-50%); }
        }
        .animate-screen-alert-scroll {
          animation: screen-alert-scroll linear infinite;
        }
        .animate-screen-alert-scroll:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
}
