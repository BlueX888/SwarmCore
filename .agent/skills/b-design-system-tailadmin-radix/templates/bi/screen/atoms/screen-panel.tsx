import * as React from "react";

import { cn } from "../lib/cn";
import { screenTokens } from "../theme/screen-tokens";

export type ScreenPanelProps = {
  title: React.ReactNode;
  extra?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  variant?: "dark" | "light";
  fullHeight?: boolean;
};

export function ScreenPanel({
  title,
  extra,
  children,
  className,
  variant = "dark",
  fullHeight = false,
}: ScreenPanelProps) {
  const isDark = variant === "dark";

  return (
    <section
      className={cn(
        "relative flex min-h-[120px] flex-col overflow-hidden rounded-lg border p-3",
        isDark
          ? cn(screenTokens.panelBg, screenTokens.panelBorder, "shadow-[0_0_12px_rgba(34,211,238,0.15)]")
          : "border-slate-200 bg-white/90",
        fullHeight && "h-full",
        className,
      )}
    >
      <span
        aria-hidden
        className="pointer-events-none absolute left-0 top-0 h-3 w-3 border-l-2 border-t-2 border-cyan-400/70"
      />
      <span
        aria-hidden
        className="pointer-events-none absolute right-0 top-0 h-3 w-3 border-r-2 border-t-2 border-cyan-400/70"
      />
      <span
        aria-hidden
        className="pointer-events-none absolute bottom-0 left-0 h-3 w-3 border-b-2 border-l-2 border-cyan-400/70"
      />
      <span
        aria-hidden
        className="pointer-events-none absolute bottom-0 right-0 h-3 w-3 border-b-2 border-r-2 border-cyan-400/70"
      />
      <header className="mb-2 flex items-center justify-between gap-2">
        <h3 className={cn(isDark ? screenTokens.title : "text-sm font-medium text-slate-700")}>
          {title}
        </h3>
        {extra ? <div className="shrink-0">{extra}</div> : null}
      </header>
      <div className="min-h-0 flex-1">{children}</div>
    </section>
  );
}
