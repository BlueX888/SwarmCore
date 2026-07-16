import * as React from "react";
import { cn } from "@/lib/utils";
import { FilterBar, type FilterChip, type FilterFieldDef } from "./filter-bar";
import { DashboardGrid, type DashboardWidget } from "./dashboard-grid";
import { MetricCard } from "./metric-card";

export type CrossFilterDashboardProps = {
  title?: React.ReactNode;
  globalFields?: FilterFieldDef[];
  globalChips?: FilterChip[];
  crossChips?: FilterChip[];
  pendingRefreshCount?: number;
  metrics?: Array<{
    id: string;
    label: string;
    value: string;
    unit?: string;
    delta?: string;
    deltaTone?: "up" | "down" | "neutral";
  }>;
  widgets: DashboardWidget[];
  renderWidget: (widget: DashboardWidget, ctx: { crossFilters: FilterChip[] }) => React.ReactNode;
  onRemoveChip?: (id: string) => void;
  onClearCrossFilters?: () => void;
  onClearAll?: () => void;
  onChartCrossFilter?: (payload: { chartId: string; chartTitle: string; dimension: string; value: string }) => void;
  className?: string;
};

/**
 * 带 global/cross-filter 的仪表盘组合 — FilterBar + KPI + DashboardGrid。
 * @see references/layout-patterns/bi-filter-linkage.md
 */
export function CrossFilterDashboard({
  title,
  globalFields = [],
  globalChips = [],
  crossChips = [],
  pendingRefreshCount = 0,
  metrics = [],
  widgets,
  renderWidget,
  onRemoveChip,
  onClearCrossFilters,
  onClearAll,
  className,
}: CrossFilterDashboardProps) {
  const allChips = [...globalChips, ...crossChips];

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      {title ? (
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-title-sm font-semibold text-gray-900 dark:text-white/90">{title}</h2>
        </div>
      ) : null}

      <FilterBar
        scope="global"
        fields={globalFields}
        chips={allChips}
        pendingRefreshCount={pendingRefreshCount}
        onRemoveChip={onRemoveChip}
        onClearCrossFilters={onClearCrossFilters}
        onClearAll={onClearAll}
      />

      {metrics.length > 0 ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {metrics.map((m) => (
            <MetricCard
              key={m.id}
              label={m.label}
              value={m.value}
              unit={m.unit}
              delta={m.delta}
              deltaTone={m.deltaTone}
            />
          ))}
        </div>
      ) : null}

      <DashboardGrid
        mode="view"
        widgets={widgets}
        renderWidget={(widget) => renderWidget(widget, { crossFilters: crossChips })}
      />
    </div>
  );
}
