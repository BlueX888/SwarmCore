import * as React from "react";
import { Activity, RefreshCw } from "lucide-react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SyncHealthPanel } from "../../../gateway/sync-health-panel";
import type { SyncTrack } from "../../../gateway/sync-health-panel";
import {
  syncActionLabel,
  syncEventEntries,
  syncHealthKpi,
  syncHealthTracks,
  syncResultLabel,
  type SyncEventEntry,
  type SyncHealthKpi,
} from "./mock-data";

export type SyncHealthMonitorPageProps = {
  kpi?: SyncHealthKpi;
  tracks?: SyncTrack[];
  events?: SyncEventEntry[];
  frozen?: boolean;
  refreshing?: boolean;
  onRefreshAll?: () => void;
  onRetry?: (trackId: string) => void;
  className?: string;
};

const overallMeta: Record<
  SyncHealthKpi["overallStatus"],
  { label: string; color: "success" | "warning" | "error" }
> = {
  healthy: { label: "健康", color: "success" },
  degraded: { label: "降级", color: "warning" },
  frozen: { label: "冻结", color: "error" },
};

const resultColor: Record<SyncEventEntry["result"], "success" | "error" | "light"> = {
  success: "success",
  error: "error",
  skipped: "light",
};

/**
 * S02-G06 同步健康监控 — 四轨状态面板 + 全部刷新 + 事件审计。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g06
 * @see references/layout-patterns/control-plane.md
 */
export function SyncHealthMonitorPage({
  kpi = syncHealthKpi,
  tracks = syncHealthTracks,
  events = syncEventEntries,
  frozen = kpi.overallStatus === "frozen",
  refreshing = false,
  onRefreshAll,
  onRetry,
  className,
}: SyncHealthMonitorPageProps) {
  const overall = overallMeta[kpi.overallStatus];

  return (
    <div className={cn("w-full space-y-6", className)} data-scenario-page="sync-health-monitor">
      <header className="space-y-1">
        <div className="inline-flex items-center gap-2 text-brand-600 dark:text-brand-400">
          <Activity className="size-4" aria-hidden="true" />
          <span className="text-theme-xs font-medium uppercase tracking-wide">Gateway 同步监控台</span>
        </div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">同步健康监控</h1>
        <p className="text-theme-sm text-gray-500">
          监控配额、报表、HMAC 心跳与实例心跳四轨同步状态，支持全部刷新与单轨重试。
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">综合健康</p>
          <div className="mt-2">
            <Badge variant="light" color={overall.color} size="sm">
              {overall.label}
            </Badge>
          </div>
          <p className="mt-2 text-theme-xs text-gray-500">
            {kpi.degradedCount > 0 ? `${kpi.degradedCount} 条轨道需关注` : "四轨均正常"}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">绑定实例</p>
          <p className="mt-1 truncate font-mono text-theme-sm text-gray-900 dark:text-white">
            {kpi.instanceId}
          </p>
          <p className="mt-1 text-theme-xs text-gray-500">{kpi.orgName}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">上次全量同步</p>
          <p className="mt-1 font-mono text-theme-sm tabular-nums text-gray-900 dark:text-white">
            {kpi.lastFullSync}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">下次计划同步</p>
          <p className="mt-1 font-mono text-theme-sm tabular-nums text-gray-900 dark:text-white">
            {kpi.nextScheduledSync}
          </p>
        </div>
      </div>

      <section className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">四轨同步状态</h2>
            <p className="mt-1 text-theme-xs text-gray-500">
              quota / report / HMAC / heartbeat 独立监控，错误轨可单独重试。
            </p>
          </div>
          {onRefreshAll ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={refreshing}
              onClick={onRefreshAll}
              data-audit="sync-health-refresh-all"
            >
              <RefreshCw className={cn("size-3.5", refreshing && "animate-spin")} />
              {refreshing ? "刷新中…" : "全部刷新"}
            </Button>
          ) : null}
        </div>
        <SyncHealthPanel
          tracks={tracks}
          frozen={frozen}
          onRetry={onRetry}
          className="space-y-0"
        />
      </section>

      <section className="rounded-xl border border-gray-200 bg-white dark:border-white/[0.05] dark:bg-white/[0.03]">
        <div className="border-b border-gray-100 px-4 py-3 dark:border-gray-800">
          <h2 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">同步事件审计</h2>
          <p className="mt-1 text-theme-xs text-gray-500">最近同步动作留痕，供排障与合规复核。</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-theme-sm">
            <thead>
              <tr className="border-b border-gray-100 text-theme-xs text-gray-500 dark:border-gray-800">
                <th className="px-4 py-2.5 font-medium">时间</th>
                <th className="px-4 py-2.5 font-medium">轨道</th>
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
                  <td className="px-4 py-3 text-gray-800 dark:text-gray-200">{entry.trackLabel}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                    {syncActionLabel[entry.action]}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="light" color={resultColor[entry.result]} size="sm">
                      {syncResultLabel[entry.result]}
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

export default SyncHealthMonitorPage;
