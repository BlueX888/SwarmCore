import * as React from "react";
import { Activity, Radar, Search } from "lucide-react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  EndpointProbeTable,
  type EndpointProbeRow,
} from "../../../gateway/endpoint-probe-table";
import {
  endpointProbeEvents,
  endpointProbeKpi,
  endpointProbeRows,
  probeActionLabel,
  probeResultLabel,
  type EndpointProbeEvent,
  type EndpointProbeKpi,
} from "./mock-data";

export type EndpointProbeListPageProps = {
  kpi?: EndpointProbeKpi;
  rows?: EndpointProbeRow[];
  events?: EndpointProbeEvent[];
  searchQuery?: string;
  statusFilter?: "all" | "ready" | "failed" | "unknown";
  batchProbing?: boolean;
  onSearchChange?: (query: string) => void;
  onStatusFilterChange?: (filter: "all" | "ready" | "failed" | "unknown") => void;
  onProbe?: (rowId: string) => void;
  onBatchProbe?: () => void;
  className?: string;
};

const statusFilterOptions: Array<{
  value: "all" | "ready" | "failed" | "unknown";
  label: string;
}> = [
  { value: "all", label: "全部" },
  { value: "ready", label: "就绪" },
  { value: "failed", label: "失败" },
  { value: "unknown", label: "未知" },
];

const resultColor: Record<EndpointProbeEvent["result"], "success" | "error" | "warning"> = {
  ready: "success",
  failed: "error",
  unknown: "warning",
};

/**
 * S02-G07 端点探测列表 — 全页 EndpointProbeTable + 批量探测 + debounce + 状态 Badge。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g07
 * @see references/layout-patterns/control-plane.md
 */
export function EndpointProbeListPage({
  kpi = endpointProbeKpi,
  rows = endpointProbeRows,
  events = endpointProbeEvents,
  searchQuery = "",
  statusFilter = "all",
  batchProbing = false,
  onSearchChange,
  onStatusFilterChange,
  onProbe,
  onBatchProbe,
  className,
}: EndpointProbeListPageProps) {
  const filteredRows = React.useMemo(() => {
    const normalized = searchQuery.trim().toLowerCase();
    return rows.filter((row) => {
      const matchesStatus = statusFilter === "all" || row.status === statusFilter;
      if (!matchesStatus) return false;
      if (!normalized) return true;
      return (
        row.endpoint.toLowerCase().includes(normalized) ||
        row.instanceId.toLowerCase().includes(normalized) ||
        (row.hint?.toLowerCase().includes(normalized) ?? false)
      );
    });
  }, [rows, searchQuery, statusFilter]);

  return (
    <div className={cn("w-full space-y-6", className)} data-scenario-page="endpoint-probe-list">
      <header className="space-y-1">
        <div className="inline-flex items-center gap-2 text-brand-600 dark:text-brand-400">
          <Radar className="size-4" aria-hidden="true" />
          <span className="text-theme-xs font-medium uppercase tracking-wide">Gateway 端点探测台</span>
        </div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">端点探测列表</h1>
        <p className="text-theme-sm text-gray-500">
          批量或单点探测已注册 API 端点，debounce 防抖后更新 ready / failed / unknown 状态 Badge。
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">端点总数</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-gray-800 dark:text-white/90">
            {kpi.total}
          </p>
          <p className="mt-1 text-theme-xs text-gray-500">{kpi.regionLabel}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">就绪</p>
          <div className="mt-2">
            <Badge variant="light" color="success" size="sm">
              {kpi.readyCount} 个
            </Badge>
          </div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">失败</p>
          <div className="mt-2">
            <Badge variant="light" color="error" size="sm">
              {kpi.failedCount} 个
            </Badge>
          </div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">未知</p>
          <div className="mt-2 flex items-center gap-2">
            <Badge variant="light" color="warning" size="sm">
              {kpi.unknownCount} 个
            </Badge>
            <span className="text-theme-xs text-gray-500">上次批量 {kpi.lastBatchProbeAt}</span>
          </div>
        </div>
      </div>

      <section className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div className="flex min-w-[240px] flex-1 flex-wrap items-center gap-3">
            <div className="relative min-w-[200px] flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
              <Input
                type="search"
                placeholder="搜索端点、实例或提示…"
                value={searchQuery}
                onChange={(event) => onSearchChange?.(event.target.value)}
                className="pl-9"
                data-audit="endpoint-probe-search"
              />
            </div>
            <div className="flex flex-wrap gap-2" data-audit="endpoint-probe-status-filter">
              {statusFilterOptions.map((option) => (
                <Button
                  key={option.value}
                  type="button"
                  variant={statusFilter === option.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => onStatusFilterChange?.(option.value)}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>
          {onBatchProbe ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={batchProbing}
              onClick={onBatchProbe}
              data-audit="endpoint-probe-batch"
            >
              <Activity className={cn("size-3.5", batchProbing && "animate-pulse")} />
              {batchProbing ? "批量探测中…" : "全部探测"}
            </Button>
          ) : null}
        </div>

        <EndpointProbeTable rows={filteredRows} debounceMs={300} onProbe={onProbe} />
      </section>

      <section className="rounded-xl border border-gray-200 bg-white dark:border-white/[0.05] dark:bg-white/[0.03]">
        <div className="border-b border-gray-100 px-4 py-3 dark:border-gray-800">
          <h2 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">探测事件审计</h2>
          <p className="mt-1 text-theme-xs text-gray-500">单点与批量探测留痕，供排障与 SLA 复核。</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-theme-sm">
            <thead>
              <tr className="border-b border-gray-100 text-theme-xs text-gray-500 dark:border-gray-800">
                <th className="px-4 py-2.5 font-medium">时间</th>
                <th className="px-4 py-2.5 font-medium">端点</th>
                <th className="px-4 py-2.5 font-medium">实例</th>
                <th className="px-4 py-2.5 font-medium">动作</th>
                <th className="px-4 py-2.5 font-medium">结果</th>
                <th className="px-4 py-2.5 font-medium">说明</th>
              </tr>
            </thead>
            <tbody>
              {events.map((entry) => (
                <tr
                  key={entry.id}
                  className="border-b border-gray-50 last:border-0 dark:border-white/[0.03]"
                >
                  <td className="px-4 py-3 tabular-nums text-gray-600 dark:text-gray-400">
                    {entry.occurredAt}
                  </td>
                  <td className="max-w-[200px] truncate px-4 py-3 font-mono text-xs text-gray-800 dark:text-gray-200">
                    {entry.endpoint}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600 dark:text-gray-400">
                    {entry.instanceId}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                    {probeActionLabel[entry.action]}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="light" color={resultColor[entry.result]} size="sm">
                      {probeResultLabel[entry.result]}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{entry.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default EndpointProbeListPage;
