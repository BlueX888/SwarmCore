import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ContentState } from "@/components/ui/content-state";

export type DashboardMode = "edit" | "preview" | "view";

export type DashboardWidget = {
  id: string;
  title: string;
  colSpan?: number;
  rowSpan?: number;
};

export type DashboardGridProps = {
  mode?: DashboardMode;
  widgets: DashboardWidget[];
  renderWidget: (widget: DashboardWidget) => React.ReactNode;
  onAddWidget?: () => void;
  className?: string;
};

/**
 * Dashboard widget grid — edit/preview/view modes.
 * @see references/layout-patterns/bi-dashboard-builder.md
 */
export function DashboardGrid({
  mode = "view",
  widgets,
  renderWidget,
  onAddWidget,
  className,
}: DashboardGridProps) {
  if (widgets.length === 0) {
    return (
      <ContentState
        variant="empty"
        title="暂无组件"
        description="添加第一个图表或指标卡片。"
        action={
          mode !== "view" && onAddWidget ? (
            <Button onClick={onAddWidget}>添加组件</Button>
          ) : undefined
        }
        className={cn("min-h-[320px] rounded-xl border border-dashed", className)}
      />
    );
  }

  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-12",
        mode === "edit" && "[&>*]:ring-1 [&>*]:ring-dashed [&>*]:ring-gray-200 dark:[&>*]:ring-gray-700",
        className,
      )}
    >
      {widgets.map((widget) => (
        <div
          key={widget.id}
          className={cn(
            "min-w-0 overflow-hidden",
            widget.colSpan === 8 ? "xl:col-span-8" : widget.colSpan === 6 ? "xl:col-span-6" : widget.colSpan === 4 ? "xl:col-span-4" : "xl:col-span-3",
            widget.rowSpan === 2 && "min-h-[280px]",
          )}
        >
          {mode === "edit" ? (
            <div className="relative">
              <span className="absolute right-2 top-2 z-10 cursor-se-resize rounded bg-gray-100 px-1.5 py-0.5 text-theme-xs text-gray-500 dark:bg-gray-800">
                ⤡
              </span>
              {renderWidget(widget)}
            </div>
          ) : (
            renderWidget(widget)
          )}
        </div>
      ))}
    </div>
  );
}
