import * as React from "react";
import { ArrowRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { BalanceQuotaSummary } from "../../../gateway/balance-quota-summary";
import { EndpointProbeTable } from "../../../gateway/endpoint-probe-table";
import { SyncHealthPanel } from "../../../gateway/sync-health-panel";
import {
  controlPlaneDashboardEndpoints,
  controlPlaneDashboardKpi,
  controlPlaneDashboardSyncTracks,
  controlPlaneQuickLinks,
} from "./mock-data";

export type ControlPlaneDashboardPageProps = {
  kpi?: typeof controlPlaneDashboardKpi;
  syncTracks?: typeof controlPlaneDashboardSyncTracks;
  endpoints?: typeof controlPlaneDashboardEndpoints;
  balanceCents?: number;
  quotaPercent?: number;
  onProbe?: (rowId: string) => void;
  onSyncRetry?: (trackId: string) => void;
  onQuickLink?: (targetId: string) => void;
};

const syncStatusColor: Record<
  (typeof controlPlaneDashboardKpi)["syncStatus"],
  "success" | "warning" | "error"
> = {
  正常: "success",
  过期: "warning",
  异常: "error",
};

/**
 * S02-G01 控制面总览 — 从 ControlPlaneHub 拆出的 Dashboard 视图（无 Hub 嵌套）。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g01
 */
export function ControlPlaneDashboardPage({
  kpi = controlPlaneDashboardKpi,
  syncTracks = controlPlaneDashboardSyncTracks,
  endpoints = controlPlaneDashboardEndpoints,
  balanceCents = 1248000,
  quotaPercent = 84,
  onProbe,
  onSyncRetry,
  onQuickLink,
}: ControlPlaneDashboardPageProps) {
  return (
    <div className="space-y-6" data-scenario-page="control-plane-dashboard">
      <header className="space-y-1">
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">控制面总览</h1>
        <p className="text-theme-sm text-gray-500">
          一眼查看同步、配额、健康与待处理事项；快捷进入部署、端点与密钥管理。
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">同步状态</p>
          <div className="mt-2 flex items-center gap-2">
            <Badge variant="light" color={syncStatusColor[kpi.syncStatus]} size="sm">
              {kpi.syncStatus}
            </Badge>
            <span className="text-theme-xs text-gray-500">四轨监控</span>
          </div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">在线端点</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-gray-800 dark:text-white/90">
            {kpi.onlineEndpoints}
          </p>
          <p className="mt-1 text-theme-xs text-gray-500">已注册实例</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">配额余量</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-gray-800 dark:text-white/90">
            {kpi.quotaRemainingPercent}%
          </p>
          <p className="mt-1 text-theme-xs text-warning-600 dark:text-warning-500">建议关注用量趋势</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">今日调用</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-gray-800 dark:text-white/90">
            {kpi.todayCalls}
          </p>
          <p className="mt-1 text-theme-xs text-success-600 dark:text-success-500">较昨日 +6.2%</p>
        </div>
      </div>

      <SyncHealthPanel tracks={syncTracks} onRetry={onSyncRetry} />

      <section className="space-y-3">
        <h2 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">配额摘要</h2>
        <BalanceQuotaSummary
          balanceCents={balanceCents}
          quotaPercent={quotaPercent}
          quotaUsed="840K"
          quotaLimit="1M"
          licenseEdition="企业版"
          licenseExpiresAt="2026年12月"
          instanceCount={6}
          degradedCount={1}
          quotaState="low"
        />
      </section>

      <EndpointProbeTable rows={endpoints.slice(0, 5)} onProbe={onProbe} />

      <section className="space-y-3">
        <h2 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">快捷入口</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {controlPlaneQuickLinks.map((link) => (
            <button
              key={link.id}
              type="button"
              className="flex flex-col gap-2 rounded-xl border border-gray-200 bg-white p-4 text-left transition hover:border-brand-300 hover:shadow-theme-xs dark:border-white/[0.05] dark:bg-white/[0.03] dark:hover:border-brand-500/40"
              onClick={() => onQuickLink?.(link.targetId)}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-theme-sm font-medium text-gray-800 dark:text-white/90">
                  {link.title}
                </span>
                <ArrowRight className="size-4 text-gray-400" />
              </div>
              <p className="text-theme-xs text-gray-500">{link.desc}</p>
              <span className="text-theme-xs text-brand-600 dark:text-brand-400">{link.targetId}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

export default ControlPlaneDashboardPage;
