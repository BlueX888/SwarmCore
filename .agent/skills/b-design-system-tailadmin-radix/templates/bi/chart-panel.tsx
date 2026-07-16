import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { ContentState } from "@/components/ui/content-state";

export type ChartPanelStatus =
  | "loading"
  | "empty"
  | "error"
  | "forbidden"
  | "ready";

export type ChartPanelProps = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  status?: ChartPanelStatus;
  errorMessage?: React.ReactNode;
  onRetry?: () => void;
  actions?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  /** Minimum chart area height. */
  minHeight?: number;
};

/**
 * Chart card shell — title, actions, loading/empty/error states.
 * @see references/layout-patterns/bi-chart-builder.md
 */
export function ChartPanel({
  title,
  description,
  status = "ready",
  errorMessage,
  onRetry,
  actions,
  children,
  className,
  minHeight = 280,
}: ChartPanelProps) {
  const renderBody = () => {
    switch (status) {
      case "loading":
        return (
          <div className="flex flex-col items-center justify-center gap-3" style={{ minHeight }}>
            <Spinner className="size-8" />
            <p className="text-theme-sm text-gray-500">正在运行查询...</p>
          </div>
        );
      case "empty":
        return (
          <ContentState
            variant="empty"
            title="暂无数据"
            description="拖入维度和指标以生成图表。"
            className="border-0 bg-transparent shadow-none"
            style={{ minHeight }}
          />
        );
      case "error":
        return (
          <ContentState
            variant="error"
            title="查询失败"
            description={errorMessage ?? "无法加载图表数据。"}
            action={onRetry ? <Button onClick={onRetry}>重试</Button> : undefined}
            className="border-0 bg-transparent shadow-none"
            style={{ minHeight }}
          />
        );
      case "forbidden":
        return (
          <ContentState
            variant="forbidden"
            title="无权限"
            description="你没有访问该数据集的权限。"
            className="border-0 bg-transparent shadow-none"
            style={{ minHeight }}
          />
        );
      default:
        return (
          <div className="min-w-0 overflow-hidden" style={{ minHeight }}>
            {children}
          </div>
        );
    }
  };

  return (
    <div
      className={cn(
        "flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
    >
      {(title || actions) && (
        <div className="flex items-start justify-between gap-3 border-b border-gray-100 px-5 py-4 dark:border-white/[0.05]">
          <div className="min-w-0">
            {title ? (
              <h3 className="truncate text-theme-sm font-semibold text-gray-900 dark:text-white/90">
                {title}
              </h3>
            ) : null}
            {description ? (
              <p className="mt-0.5 text-theme-xs text-gray-500">{description}</p>
            ) : null}
          </div>
          {actions ? <div className="flex shrink-0 gap-2">{actions}</div> : null}
        </div>
      )}
      <div className="p-5">{renderBody()}</div>
    </div>
  );
}
