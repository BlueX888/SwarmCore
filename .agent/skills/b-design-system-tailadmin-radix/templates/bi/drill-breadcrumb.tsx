import * as React from "react";
import { cn } from "@/lib/utils";
import { ChevronRight } from "lucide-react";

export type DrillBreadcrumbItem = {
  id: string;
  label: string;
  /** 是否为当前层级（不可点击） */
  current?: boolean;
};

export type DrillBreadcrumbProps = {
  items: DrillBreadcrumbItem[];
  onNavigate?: (item: DrillBreadcrumbItem, index: number) => void;
  className?: string;
};

/**
 * BI 下钻路径面包屑 — 逐级返回汇总视图，保留筛选上下文。
 * @see references/layout-patterns/bi-drill-down.md
 */
export function DrillBreadcrumb({ items, onNavigate, className }: DrillBreadcrumbProps) {
  if (items.length === 0) return null;

  return (
    <nav aria-label="下钻路径" className={cn("flex flex-wrap items-center gap-1 text-theme-sm", className)}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        const isCurrent = item.current ?? isLast;

        return (
          <React.Fragment key={item.id}>
            {index > 0 ? (
              <ChevronRight className="size-4 shrink-0 text-gray-400" aria-hidden />
            ) : null}
            {isCurrent ? (
              <span className="font-medium text-gray-900 dark:text-white/90" aria-current="page">
                {item.label}
              </span>
            ) : (
              <button
                type="button"
                onClick={() => onNavigate?.(item, index)}
                className="text-gray-500 transition hover:text-brand-500 dark:text-gray-400 dark:hover:text-brand-400"
              >
                {item.label}
              </button>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
