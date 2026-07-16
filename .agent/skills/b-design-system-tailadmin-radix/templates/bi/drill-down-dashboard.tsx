import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { DrillBreadcrumb, type DrillBreadcrumbItem } from "./drill-breadcrumb";
import { FilterBar, type FilterChip, type FilterFieldDef } from "./filter-bar";

export type DrillView = "chart" | "detail";

export type DrillPayload = {
  dimension: string;
  value: string;
  chartId?: string;
  chartTitle?: string;
};

export type DrillDownDashboardProps = {
  title?: React.ReactNode;
  breadcrumb: DrillBreadcrumbItem[];
  view?: DrillView;
  globalFields?: FilterFieldDef[];
  filterChips?: FilterChip[];
  selectedDimension?: { dimension: string; value: string } | null;
  onBreadcrumbNavigate?: (item: DrillBreadcrumbItem, index: number) => void;
  onDrill?: (payload: DrillPayload) => void;
  onViewDetail?: () => void;
  onBackToChart?: () => void;
  renderChart: () => React.ReactNode;
  renderDetail: () => React.ReactNode;
  className?: string;
};

/**
 * BI 下钻仪表盘 — 图表点击下钻 + 面包屑 + 明细表切换，保留筛选上下文。
 * @see references/layout-patterns/bi-drill-down.md
 */
export function DrillDownDashboard({
  title,
  breadcrumb,
  view = "chart",
  globalFields = [],
  filterChips = [],
  selectedDimension,
  onBreadcrumbNavigate,
  onViewDetail,
  onBackToChart,
  renderChart,
  renderDetail,
  className,
}: DrillDownDashboardProps) {
  const showDetailActions = view === "chart" && breadcrumb.length > 1;

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        {title ? (
          <h2 className="text-title-sm font-semibold text-gray-900 dark:text-white/90">{title}</h2>
        ) : null}
        <DrillBreadcrumb items={breadcrumb} onNavigate={onBreadcrumbNavigate} />
      </div>

      <FilterBar scope="global" fields={globalFields} chips={filterChips} />

      {selectedDimension && view === "chart" ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-brand-500/30 bg-brand-50 px-4 py-2 text-theme-sm dark:bg-brand-500/10">
          <span className="text-gray-700 dark:text-gray-300">
            已下钻：<strong>{selectedDimension.dimension}</strong> = {selectedDimension.value}
          </span>
          <div className="flex gap-2">
            {showDetailActions && onViewDetail ? (
              <Button size="sm" variant="outline" onClick={onViewDetail}>
                查看明细
              </Button>
            ) : null}
            {onBackToChart && view === "detail" ? (
              <Button size="sm" variant="ghost" onClick={onBackToChart}>
                返回图表
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}

      {view === "chart" ? renderChart() : renderDetail()}
    </div>
  );
}
