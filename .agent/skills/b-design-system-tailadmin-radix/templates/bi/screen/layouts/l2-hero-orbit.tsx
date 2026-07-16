import * as React from "react";

import { cn } from "../lib/cn";

export type L2LayoutProps = {
  header?: React.ReactNode;
  kpi?: React.ReactNode;
  leftColumn: React.ReactNode;
  hero: React.ReactNode;
  rightColumn: React.ReactNode;
  bottomTrend: React.ReactNode;
  className?: string;
};

/**
 * L2 中央主视觉环绕布局壳 — 左/中 Hero/右三栏 + 底全宽趋势。
 * @see prd/data-screens/layouts.md#task-ds-l2
 */
export function L2HeroOrbitLayout({
  header,
  kpi,
  leftColumn,
  hero,
  rightColumn,
  bottomTrend,
  className,
}: L2LayoutProps) {
  return (
    <div className={cn("flex h-full min-h-0 flex-col gap-3", className)} data-screen-layout="l2">
      {header ? <div className="shrink-0">{header}</div> : null}
      {kpi ? <div className="shrink-0">{kpi}</div> : null}
      <div className="grid min-h-0 flex-1 grid-cols-12 grid-rows-6 gap-3">
        <div className="col-span-3 row-span-4 flex min-h-0 flex-col gap-3">{leftColumn}</div>
        <div className="col-span-6 row-span-4 min-h-0">{hero}</div>
        <div className="col-span-3 row-span-4 flex min-h-0 flex-col gap-3">{rightColumn}</div>
        <div className="col-span-12 row-span-2 min-h-0">{bottomTrend}</div>
      </div>
    </div>
  );
}
