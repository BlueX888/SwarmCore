import * as React from "react";

import { cn } from "./lib/cn";
import { screenTokens } from "./theme/screen-tokens";

export type RefreshStatus = {
  lastAt?: string;
  intervalSec?: number;
  state?: "idle" | "refreshing" | "error";
};

export type ScreenShellProps = {
  title: string;
  showClock?: boolean;
  aspectRatio?: "16:9" | "21:9";
  scaleMode?: "fit" | "width";
  theme?: "dark" | "light";
  refreshStatus?: RefreshStatus;
  onRefreshClick?: () => void;
  children: React.ReactNode;
  className?: string;
};

function formatClock(date: Date) {
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

export function RefreshStatusBadge({
  lastAt,
  intervalSec,
  state = "idle",
  theme = "dark",
  onClick,
}: RefreshStatus & { theme?: "dark" | "light"; onClick?: () => void }) {
  const isDark = theme === "dark";
  const label =
    state === "error"
      ? "同步失败，请重试"
      : state === "refreshing"
        ? "正在同步..."
        : `更新于 ${lastAt ?? "—"}`;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-xs transition-colors",
        isDark
          ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-100 hover:bg-cyan-500/20"
          : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
      )}
    >
      {state === "refreshing" ? (
        <span className="inline-block size-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
      ) : null}
      <span>{label}</span>
      {intervalSec ? <span className="opacity-70">· 每 {intervalSec}s</span> : null}
    </button>
  );
}

/**
 * Fixed-ratio data screen shell with header, clock and refresh badge.
 * @see references/layout-patterns/bi-data-screen.md
 */
export function ScreenShell({
  title,
  showClock = true,
  aspectRatio = "16:9",
  scaleMode = "fit",
  theme = "dark",
  refreshStatus,
  onRefreshClick,
  children,
  className,
}: ScreenShellProps) {
  const isDark = theme === "dark";
  const [clock, setClock] = React.useState(() => formatClock(new Date()));

  React.useEffect(() => {
    if (!showClock) return undefined;
    const timer = window.setInterval(() => setClock(formatClock(new Date())), 1000);
    return () => window.clearInterval(timer);
  }, [showClock]);

  const aspectClass = aspectRatio === "21:9" ? "aspect-[21/9]" : "aspect-video";

  return (
    <div className={cn("flex flex-col gap-3", className)} data-screen-shell>
      <div className="flex items-center justify-between gap-3">
        <h1
          className={cn(
            "text-lg font-semibold tracking-wide",
            isDark ? "text-cyan-50" : "text-slate-900",
          )}
        >
          {title}
        </h1>
        <div className="flex items-center gap-3">
          {showClock ? (
            <span className={cn(screenTokens.clock, !isDark && "text-slate-500")}>{clock}</span>
          ) : null}
          {refreshStatus ? (
            <RefreshStatusBadge
              {...refreshStatus}
              theme={theme}
              onClick={onRefreshClick}
            />
          ) : null}
        </div>
      </div>
      <div
        className={cn(
          "relative w-full overflow-hidden rounded-xl border",
          aspectClass,
          scaleMode === "width" && "origin-top",
          isDark
            ? "border-cyan-500/20 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white shadow-[0_0_24px_rgba(34,211,238,0.08)]"
            : "border-slate-200 bg-gradient-to-b from-slate-50 to-blue-50/30 text-slate-900",
        )}
      >
        <div className="absolute inset-0 p-4">{children}</div>
      </div>
    </div>
  );
}

/** @deprecated Use ScreenShell — kept for backward compatibility with data-screen-canvas imports */
export const DataScreenCanvas = ScreenShell;
