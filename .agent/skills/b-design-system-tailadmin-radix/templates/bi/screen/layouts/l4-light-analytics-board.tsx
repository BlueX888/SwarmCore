import * as React from "react";

import { cn } from "../lib/cn";

export type L4LayoutProps = {
  header?: React.ReactNode;
  leftColumn: React.ReactNode;
  centerTop: React.ReactNode;
  centerMiddle: React.ReactNode;
  centerBottom: React.ReactNode;
  rightColumn: React.ReactNode;
  fullWidthBottom?: React.ReactNode;
  className?: string;
};

/**
 * L4 浅色运营看板布局壳 — 非对称左 3 / 中 6 / 右 3，中部 2×2 嵌套 grid。
 * @see prd/data-screens/layouts.md#task-ds-l4
 */
export function L4LightAnalyticsBoardLayout({
  header,
  leftColumn,
  centerTop,
  centerMiddle,
  centerBottom,
  rightColumn,
  fullWidthBottom,
  className,
}: L4LayoutProps) {
  return (
    <div className={cn("flex h-full min-h-0 flex-col gap-3", className)} data-screen-layout="l4">
      {header ? <div className="shrink-0">{header}</div> : null}
      <div className="grid min-h-0 flex-1 grid-cols-12 gap-3">
        <div className="col-span-3 flex min-h-0 flex-col gap-3">{leftColumn}</div>
        <div className="col-span-6 flex min-h-0 flex-col gap-3">
          <div className="grid min-h-0 flex-1 grid-rows-3 gap-3">
            <div className="min-h-0">{centerTop}</div>
            <div className="min-h-0">{centerMiddle}</div>
            <div className="min-h-0">{centerBottom}</div>
          </div>
        </div>
        <div className="col-span-3 flex min-h-0 flex-col gap-3">{rightColumn}</div>
      </div>
      {fullWidthBottom ? (
        <div className="grid shrink-0 grid-cols-12 gap-3">
          <div className="col-span-12">{fullWidthBottom}</div>
        </div>
      ) : null}
    </div>
  );
}
