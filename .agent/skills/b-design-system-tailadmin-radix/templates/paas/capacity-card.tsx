import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

export type CapacityMetric =
  | "cpu"
  | "memory"
  | "disk"
  | "qps"
  | "latency"
  | "replica";

export type CapacityLevel = "normal" | "warning" | "critical";

export type CapacityCardProps = {
  metric: CapacityMetric;
  label?: string;
  value: string | number;
  unit?: string;
  percent?: number;
  trend?: string;
  level?: CapacityLevel;
  hint?: string;
  className?: string;
};

const metricDefaults: Record<CapacityMetric, { label: string; unit?: string }> = {
  cpu: { label: "CPU 使用率", unit: "%" },
  memory: { label: "内存使用率", unit: "%" },
  disk: { label: "磁盘使用率", unit: "%" },
  qps: { label: "QPS", unit: "req/s" },
  latency: { label: "P95 延迟", unit: "ms" },
  replica: { label: "副本数", unit: "" },
};

const levelBadge: Record<CapacityLevel, { label: string; color: "success" | "warning" | "error" }> = {
  normal: { label: "正常", color: "success" },
  warning: { label: "预警", color: "warning" },
  critical: { label: "严重", color: "error" },
};

/**
 * 健康/容量指标卡 — CPU、Memory、Disk、QPS、Latency、Replica。
 * @see references/component-styles/paas-template.md
 */
export function CapacityCard({
  metric,
  label,
  value,
  unit,
  percent,
  trend,
  level = "normal",
  hint,
  className,
}: CapacityCardProps) {
  const defaults = metricDefaults[metric];
  const displayLabel = label ?? defaults.label;
  const displayUnit = unit ?? defaults.unit;
  const badge = levelBadge[level];

  return (
    <article
      className={cn(
        "flex min-w-0 flex-col gap-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900",
        className,
      )}
      aria-label={displayLabel}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-theme-xs font-medium text-gray-500">{displayLabel}</p>
          <p className="mt-1 truncate text-xl font-semibold tabular-nums text-gray-900 dark:text-white">
            {value}
            {displayUnit ? (
              <span className="ml-1 text-theme-sm font-medium text-gray-500">{displayUnit}</span>
            ) : null}
          </p>
        </div>
        <Badge variant="light" color={badge.color} size="sm">
          {badge.label}
        </Badge>
      </div>
      {typeof percent === "number" ? (
        <Progress value={percent} className="h-2" aria-label={`${displayLabel} ${percent}%`} />
      ) : null}
      <div className="flex flex-wrap items-center justify-between gap-2 text-theme-xs text-gray-500">
        {trend ? <span>{trend}</span> : <span />}
        {hint ? <span className="truncate">{hint}</span> : null}
      </div>
    </article>
  );
}
