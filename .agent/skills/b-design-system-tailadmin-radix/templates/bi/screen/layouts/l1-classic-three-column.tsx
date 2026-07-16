import * as React from "react";

import { cn } from "../lib/cn";

export type L1LayoutProps = {
  header?: React.ReactNode;
  kpi?: React.ReactNode;
  left: React.ReactNode;
  center: React.ReactNode;
  right: React.ReactNode;
  footer?: React.ReactNode;
  theme?: "dark";
  className?: string;
};

/**
 * L1 经典三栏指挥台布局壳 — 仅负责 grid + slot，不含业务 mock。
 * @see prd/data-screens/layouts.md#task-ds-l1
 */
export function L1ClassicThreeColumnLayout({
  header,
  kpi,
  left,
  center,
  right,
  footer,
  className,
}: L1LayoutProps) {
  return (
    <div className={cn("flex h-full min-h-0 flex-col gap-3", className)} data-screen-layout="l1">
      {header ? <div className="shrink-0">{header}</div> : null}
      {kpi ? <div className="shrink-0">{kpi}</div> : null}
      <div className="grid min-h-0 flex-1 grid-cols-12 grid-rows-6 gap-3">
        <div className="col-span-3 row-span-6 flex min-h-0 flex-col gap-3">{left}</div>
        <div className="col-span-6 row-span-6 flex min-h-0 flex-col gap-3">{center}</div>
        <div className="col-span-3 row-span-6 flex min-h-0 flex-col gap-3">{right}</div>
      </div>
      {footer ? <div className="shrink-0">{footer}</div> : null}
    </div>
  );
}
