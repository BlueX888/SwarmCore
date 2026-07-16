import * as React from "react";

import { cn } from "../lib/cn";
import { screenTokens } from "../theme/screen-tokens";

export type TimelineNode = {
  id: string;
  date: string;
  title: string;
  description?: string;
  status?: "done" | "active" | "pending";
};

export type ScreenTimelineProps = {
  nodes: TimelineNode[];
  theme?: "dark" | "light";
  className?: string;
};

const statusDot: Record<NonNullable<TimelineNode["status"]>, string> = {
  done: "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]",
  active: "bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)]",
  pending: "bg-slate-500 shadow-none",
};

/**
 * 水平时间轴 — 日期 + 描述节点，生态事件/项目里程碑适用。
 * @see prd/data-screens/atoms.md#task-ds-a14
 */
export function ScreenTimeline({ nodes, theme = "dark", className }: ScreenTimelineProps) {
  const isDark = theme === "dark";

  return (
    <div
      data-screen-timeline
      data-theme={theme}
      className={cn("relative w-full overflow-x-auto px-1", className)}
    >
      <div className="flex min-w-max items-start gap-0">
        {nodes.map((node, index) => {
          const status = node.status ?? (index === nodes.length - 1 ? "active" : "done");
          const isLast = index === nodes.length - 1;

          return (
            <div key={node.id} className="flex min-w-[140px] max-w-[180px] flex-1 flex-col items-center">
              <div className="flex w-full items-center">
                {index > 0 ? (
                  <div
                    className={cn(
                      "h-px flex-1",
                      isDark ? "bg-gradient-to-r from-cyan-500/40 to-cyan-400/20" : "bg-slate-300",
                    )}
                  />
                ) : (
                  <div className="flex-1" />
                )}
                <span
                  className={cn(
                    "relative z-10 h-3 w-3 shrink-0 rounded-full ring-2 ring-offset-2",
                    isDark ? "ring-offset-slate-900" : "ring-offset-white",
                    statusDot[status],
                    status === "active" && "ring-cyan-400/60",
                  )}
                />
                {!isLast ? (
                  <div
                    className={cn(
                      "h-px flex-1",
                      isDark ? "bg-gradient-to-r from-cyan-400/20 to-cyan-500/40" : "bg-slate-300",
                    )}
                  />
                ) : (
                  <div className="flex-1" />
                )}
              </div>
              <div className="mt-2 w-full px-2 text-center">
                <p
                  className={cn(
                    "text-[10px] font-medium tabular-nums",
                    isDark ? "text-cyan-300/90" : "text-sky-600",
                  )}
                >
                  {node.date}
                </p>
                <p className={cn("mt-0.5 text-xs font-semibold", isDark ? "text-white" : "text-slate-900")}>
                  {node.title}
                </p>
                {node.description ? (
                  <p className={cn("mt-0.5 line-clamp-2 text-[10px]", isDark ? screenTokens.kpiLabel : "text-slate-500")}>
                    {node.description}
                  </p>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
