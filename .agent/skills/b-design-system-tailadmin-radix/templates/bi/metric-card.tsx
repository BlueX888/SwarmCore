import * as React from "react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

export type MetricCardStatus = "ready" | "loading" | "zero" | "error";

export type MetricCardProps = {
  label: React.ReactNode;
  value?: React.ReactNode;
  unit?: React.ReactNode;
  delta?: React.ReactNode;
  deltaTone?: "up" | "down" | "neutral";
  status?: MetricCardStatus;
  className?: string;
};

const deltaClass = {
  up: "text-success-500",
  down: "text-error-500",
  neutral: "text-gray-500",
};

/**
 * BI metric tile — big number, unit, delta badge.
 * @see references/layout-patterns/bi-dashboard-builder.md
 */
export function MetricCard({
  label,
  value,
  unit,
  delta,
  deltaTone = "neutral",
  status = "ready",
  className,
}: MetricCardProps) {
  const renderValue = () => {
    if (status === "loading") return <Skeleton className="mt-2 h-9 w-28" />;
    if (status === "error") return <span className="mt-2 block text-title-sm font-semibold text-error-500">—</span>;
    if (status === "zero") return <span className="mt-2 block text-title-sm font-semibold text-gray-400">0</span>;
    return (
      <span className="mt-2 inline-flex items-baseline gap-1">
        <strong className="text-title-sm font-semibold tabular-nums text-gray-900 dark:text-white/90">
          {value}
        </strong>
        {unit ? <span className="text-theme-sm text-gray-500">{unit}</span> : null}
      </span>
    );
  };

  return (
    <div
      className={cn(
        "rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
    >
      <span className="text-theme-sm text-gray-500">{label}</span>
      {renderValue()}
      {delta && status === "ready" ? (
        <Badge variant="light" className={cn("mt-2", deltaClass[deltaTone])}>
          {delta}
        </Badge>
      ) : null}
    </div>
  );
}
