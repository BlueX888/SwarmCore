import * as React from "react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";

export type StatMetricStatus =
  | "ready"
  | "loading"
  | "zero"
  | "error"
  | "forbidden"
  | "partial";

export type StatMetricProps = {
  label: React.ReactNode;
  value?: React.ReactNode;
  delta?: React.ReactNode;
  deltaTone?: "success" | "error" | "neutral";
  trend?: React.ReactNode;
  status?: StatMetricStatus;
  hint?: React.ReactNode;
  className?: string;
};

const deltaToneClass = {
  success: "text-success-500",
  error: "text-error-500",
  neutral: "text-gray-500",
};

/**
 * KPI / stat card cell with zero-value, forbidden, and loading rules.
 */
export function StatMetric({
  label,
  value,
  delta,
  deltaTone = "neutral",
  trend,
  status = "ready",
  hint,
  className,
}: StatMetricProps) {
  const renderValue = () => {
    switch (status) {
      case "loading":
        return <Skeleton className="mt-2 h-8 w-24" />;
      case "zero":
        return (
          <strong className="mt-2 block text-title-sm font-semibold tabular-nums text-gray-400 dark:text-gray-500">
            0
          </strong>
        );
      case "error":
        return (
          <strong className="mt-2 block text-title-sm font-semibold text-error-500">—</strong>
        );
      case "forbidden":
        return (
          <strong className="mt-2 block text-title-sm font-semibold text-gray-400">•••</strong>
        );
      case "partial":
        return (
          <div className="mt-2 flex items-center gap-2">
            <strong className="text-title-sm font-semibold tabular-nums text-gray-800 dark:text-white/90">
              {value ?? "—"}
            </strong>
            <Spinner size="sm" aria-label="正在更新指标" />
          </div>
        );
      default:
        return (
          <strong className="mt-2 block truncate text-title-sm font-semibold tabular-nums text-gray-800 dark:text-white/90">
            {value}
          </strong>
        );
    }
  };

  return (
    <div
      className={cn(
        "rounded-2xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
    >
      <span className="text-theme-sm text-gray-500">{label}</span>
      {renderValue()}
      {trend && status === "ready" ? <div className="mt-1">{trend}</div> : null}
      {delta && status === "ready" ? (
        <span className={cn("mt-1 block text-theme-xs font-medium", deltaToneClass[deltaTone])}>
          {delta}
        </span>
      ) : null}
      {hint ? (
        <p className="mt-1 text-theme-xs text-gray-500 dark:text-gray-400">{hint}</p>
      ) : null}
    </div>
  );
}
