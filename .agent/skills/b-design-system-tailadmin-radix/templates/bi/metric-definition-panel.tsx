import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";

export type MetricLifecycleStatus =
  | "active"
  | "draft"
  | "pending_review"
  | "deprecated"
  | "conflict";

export type MetricDefinition = {
  id: string;
  name: string;
  displayName: string;
  formula?: string;
  aggregation?: string;
  unit?: string;
  granularity?: string;
  owner?: string;
  status?: MetricLifecycleStatus;
  impactedCharts?: number;
  description?: string;
};

export type DimensionDefinition = {
  id: string;
  name: string;
  displayName: string;
  dataType?: string;
  description?: string;
};

export type MetricDefinitionPanelProps = {
  metrics: MetricDefinition[];
  dimensions?: DimensionDefinition[];
  selectedMetricId?: string;
  onSelectMetric?: (id: string) => void;
  onReview?: (id: string) => void;
  className?: string;
};

const statusMeta: Record<
  MetricLifecycleStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  active: { label: "已发布", variant: "default" },
  draft: { label: "草稿", variant: "secondary" },
  pending_review: { label: "待审核", variant: "outline" },
  deprecated: { label: "已废弃", variant: "secondary" },
  conflict: { label: "口径冲突", variant: "destructive" },
};

/**
 * BI 语义层 — 指标/维度定义、公式、聚合、owner 与影响范围。
 * @see references/layout-patterns/bi-semantic-layer.md
 */
export function MetricDefinitionPanel({
  metrics,
  dimensions = [],
  selectedMetricId,
  onSelectMetric,
  onReview,
  className,
}: MetricDefinitionPanelProps) {
  const selected =
    metrics.find((m) => m.id === selectedMetricId) ?? metrics[0];
  const status = selected?.status ?? "active";
  const meta = statusMeta[status];

  return (
    <div
      className={cn(
        "grid min-h-[420px] grid-cols-1 rounded-xl border border-gray-200 dark:border-gray-800 lg:grid-cols-[minmax(280px,34%)_minmax(0,1fr)]",
        className,
      )}
    >
      <div className="border-b border-gray-200 lg:border-b-0 lg:border-r dark:border-gray-800">
        <div className="border-b border-gray-200 px-4 py-3 dark:border-gray-800">
          <h3 className="text-theme-sm font-semibold text-gray-900 dark:text-white/90">
            指标目录 ({metrics.length})
          </h3>
        </div>
        <ul className="max-h-[380px] overflow-y-auto">
          {metrics.map((metric) => {
            const sm = statusMeta[metric.status ?? "active"];
            return (
              <li key={metric.id}>
                <button
                  type="button"
                  onClick={() => onSelectMetric?.(metric.id)}
                  className={cn(
                    "flex w-full flex-col gap-1 border-b border-gray-100 px-4 py-3 text-left dark:border-white/[0.05]",
                    selected?.id === metric.id &&
                      "border-l-[3px] border-l-brand-500 bg-brand-50/50 pl-[13px] dark:bg-brand-500/10",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate font-medium text-gray-900 dark:text-white/90">
                      {metric.displayName}
                    </span>
                    <Badge variant={sm.variant} className="shrink-0 text-[10px]">
                      {sm.label}
                    </Badge>
                  </div>
                  <span className="truncate text-theme-xs text-gray-500">
                    {metric.name}
                    {metric.unit ? ` · ${metric.unit}` : ""}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="flex flex-col">
        {selected ? (
          <>
            <div className="flex flex-wrap items-start justify-between gap-3 border-b border-gray-200 px-5 py-4 dark:border-gray-800">
              <div className="min-w-0">
                <h4 className="text-title-sm font-semibold text-gray-900 dark:text-white/90">
                  {selected.displayName}
                </h4>
                <p className="mt-0.5 text-theme-xs text-gray-500">{selected.name}</p>
              </div>
              <Badge variant={meta.variant}>{meta.label}</Badge>
            </div>

            {status === "conflict" ? (
              <div className="px-5 pt-4">
                <Alert
                  variant="warning"
                  title="口径冲突"
                  description="与「订单 GMV」指标存在重复定义，请合并或废弃其一后再发布。"
                />
              </div>
            ) : null}

            <dl className="grid gap-4 px-5 py-4 sm:grid-cols-2">
              <div>
                <dt className="text-theme-xs font-medium text-gray-500">聚合方式</dt>
                <dd className="mt-1 text-theme-sm text-gray-900 dark:text-white/90">
                  {selected.aggregation ?? "—"}
                </dd>
              </div>
              <div>
                <dt className="text-theme-xs font-medium text-gray-500">统计粒度</dt>
                <dd className="mt-1 text-theme-sm text-gray-900 dark:text-white/90">
                  {selected.granularity ?? "—"}
                </dd>
              </div>
              <div>
                <dt className="text-theme-xs font-medium text-gray-500">单位</dt>
                <dd className="mt-1 text-theme-sm text-gray-900 dark:text-white/90">
                  {selected.unit ?? "—"}
                </dd>
              </div>
              <div>
                <dt className="text-theme-xs font-medium text-gray-500">负责人</dt>
                <dd className="mt-1 text-theme-sm text-gray-900 dark:text-white/90">
                  {selected.owner ?? "—"}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-theme-xs font-medium text-gray-500">计算公式</dt>
                <dd className="mt-1 rounded-lg bg-gray-50 px-3 py-2 font-mono text-theme-sm text-gray-800 dark:bg-white/[0.03] dark:text-white/90">
                  {selected.formula ?? "—"}
                </dd>
              </div>
              {selected.description ? (
                <div className="sm:col-span-2">
                  <dt className="text-theme-xs font-medium text-gray-500">口径说明</dt>
                  <dd className="mt-1 text-theme-sm text-gray-700 dark:text-gray-300">
                    {selected.description}
                  </dd>
                </div>
              ) : null}
              {selected.impactedCharts !== undefined ? (
                <div className="sm:col-span-2">
                  <dt className="text-theme-xs font-medium text-gray-500">影响范围</dt>
                  <dd className="mt-1 text-theme-sm text-gray-900 dark:text-white/90">
                    关联 {selected.impactedCharts} 个图表/仪表盘
                  </dd>
                </div>
              ) : null}
            </dl>

            {dimensions.length > 0 ? (
              <div className="border-t border-gray-200 px-5 py-4 dark:border-gray-800">
                <h5 className="mb-2 text-theme-xs font-semibold uppercase tracking-wide text-brand-500">
                  关联维度
                </h5>
                <div className="flex flex-wrap gap-2">
                  {dimensions.map((dim) => (
                    <Badge key={dim.id} variant="light">
                      {dim.displayName}
                      {dim.dataType ? ` · ${dim.dataType}` : ""}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : null}

            {status === "pending_review" && onReview ? (
              <div className="mt-auto flex justify-end gap-2 border-t border-gray-200 px-5 py-4 dark:border-gray-800">
                <Button variant="outline" size="sm" onClick={() => onReview(selected.id)}>
                  驳回
                </Button>
                <Button size="sm" onClick={() => onReview(selected.id)}>
                  通过审核
                </Button>
              </div>
            ) : null}
          </>
        ) : (
          <div className="flex flex-1 items-center justify-center p-8 text-theme-sm text-gray-500">
            请选择指标查看口径详情
          </div>
        )}
      </div>
    </div>
  );
}
