import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export type FilterScope = "global" | "local";

export type FilterValueSource = "user" | "chart" | "default";

export type FilterChip = {
  id: string;
  label: string;
  value: string;
  scope: FilterScope;
  source?: FilterValueSource;
  sourceChart?: string;
};

export type FilterFieldType =
  | "date-range"
  | "relative-time"
  | "enum"
  | "multi"
  | "cascade"
  | "search";

export type FilterFieldDef = {
  id: string;
  label: string;
  type: FilterFieldType;
  placeholder?: string;
};

export type FilterBarProps = {
  scope?: FilterScope;
  fields?: FilterFieldDef[];
  chips?: FilterChip[];
  pendingRefreshCount?: number;
  onRemoveChip?: (id: string) => void;
  onClearCrossFilters?: () => void;
  onClearAll?: () => void;
  className?: string;
};

const sourceLabel: Record<FilterValueSource, string> = {
  user: "手动",
  chart: "图表联动",
  default: "默认",
};

/**
 * BI 筛选条 — global/local 筛选 chips、清除联动与待刷新提示。
 * @see references/layout-patterns/bi-filter-linkage.md
 */
export function FilterBar({
  scope = "global",
  fields = [],
  chips = [],
  pendingRefreshCount = 0,
  onRemoveChip,
  onClearCrossFilters,
  onClearAll,
  className,
}: FilterBarProps) {
  const crossChips = chips.filter((c) => c.source === "chart");
  const hasCross = crossChips.length > 0;

  return (
    <div
      className={cn(
        "sticky top-0 z-10 flex flex-col gap-3 rounded-xl border border-gray-200 bg-white/95 p-3 backdrop-blur dark:border-gray-800 dark:bg-gray-900/95",
        className,
      )}
      data-scope={scope}
    >
      {fields.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-theme-xs font-medium uppercase tracking-wide text-gray-500">
            {scope === "global" ? "全局筛选" : "局部筛选"}
          </span>
          {fields.map((field) => (
            <button
              key={field.id}
              type="button"
              className="inline-flex h-9 min-w-[120px] items-center justify-between gap-2 rounded-lg border border-gray-200 bg-white px-3 text-theme-sm text-gray-700 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
            >
              <span className="truncate">{field.label}</span>
              <span className="text-gray-400">▾</span>
            </button>
          ))}
        </div>
      ) : null}

      {chips.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2">
          {chips.map((chip) => (
            <Badge
              key={chip.id}
              variant="outline"
              className={cn(
                "gap-1.5 py-1 pl-2 pr-1 text-theme-xs font-normal",
                chip.source === "chart" && "border-brand-500/40 bg-brand-50 dark:bg-brand-500/10",
              )}
            >
              {chip.source === "chart" ? (
                <span className="size-1.5 rounded-full bg-brand-500" aria-hidden />
              ) : null}
              <span className="text-gray-500">{chip.label}</span>
              <span className="font-medium text-gray-800 dark:text-white/90">{chip.value}</span>
              {chip.sourceChart ? (
                <span className="text-gray-400">← {chip.sourceChart}</span>
              ) : null}
              {onRemoveChip ? (
                <button
                  type="button"
                  className="ml-0.5 rounded p-0.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800"
                  aria-label={`移除筛选 ${chip.label}`}
                  onClick={() => onRemoveChip(chip.id)}
                >
                  ×
                </button>
              ) : null}
            </Badge>
          ))}
        </div>
      ) : (
        <p className="text-theme-sm text-gray-500">未应用筛选，显示全部数据。</p>
      )}

      <div className="flex flex-wrap items-center gap-2">
        {pendingRefreshCount > 0 ? (
          <span className="text-theme-xs text-warning-600 dark:text-warning-500">
            筛选已变更，{pendingRefreshCount} 个图表待更新
          </span>
        ) : null}
        {hasCross && onClearCrossFilters ? (
          <Button type="button" variant="outline" size="sm" onClick={onClearCrossFilters}>
            清除联动
          </Button>
        ) : null}
        {onClearAll ? (
          <Button type="button" variant="ghost" size="sm" onClick={onClearAll}>
            清除全部
          </Button>
        ) : null}
      </div>

      {process.env.NODE_ENV === "development" && chips.some((c) => c.source) ? (
        <p className="text-theme-xs text-gray-400">
          来源：
          {Array.from(new Set(chips.map((c) => c.source).filter(Boolean)))
            .map((s) => sourceLabel[s as FilterValueSource])
            .join("、")}
        </p>
      ) : null}
    </div>
  );
}
