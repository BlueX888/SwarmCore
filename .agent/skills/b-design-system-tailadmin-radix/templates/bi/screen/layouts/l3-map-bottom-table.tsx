import * as React from "react";

import { cn } from "../lib/cn";

export type L3LayoutProps = {
  header?: React.ReactNode;
  kpi?: React.ReactNode;
  left: React.ReactNode;
  centerMap: React.ReactNode;
  right: React.ReactNode;
  bottomTable: React.ReactNode;
  className?: string;
};

/**
 * L3 地图主导 + 底表布局壳 — 中央地图、左右栏堆叠、底部宽表。
 * @see prd/data-screens/layouts.md#task-ds-l3
 */
export function L3MapBottomTableLayout({
  header,
  kpi,
  left,
  centerMap,
  right,
  bottomTable,
  className,
}: L3LayoutProps) {
  return (
    <div className={cn("flex h-full min-h-0 flex-col gap-3", className)} data-screen-layout="l3">
      {header ? <div className="shrink-0">{header}</div> : null}
      {kpi ? <div className="shrink-0">{kpi}</div> : null}
      <div className="grid min-h-0 flex-1 grid-cols-12 grid-rows-6 gap-3">
        <div className="col-span-3 row-span-4 flex min-h-0 flex-col gap-3">{left}</div>
        <div className="col-span-6 row-span-4 min-h-0">{centerMap}</div>
        <div className="col-span-3 row-span-4 flex min-h-0 flex-col gap-3">{right}</div>
        <div className="col-span-12 row-span-2 min-h-0">{bottomTable}</div>
      </div>
    </div>
  );
}
