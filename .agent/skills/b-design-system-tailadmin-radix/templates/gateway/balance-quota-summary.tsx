import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert } from "@/components/ui/alert";

export type QuotaState = "normal" | "low" | "critical" | "frozen";

export type BalanceQuotaSummaryProps = {
  balanceCents?: number;
  currencySymbol?: string;
  quotaPercent?: number;
  quotaUsed?: string;
  quotaLimit?: string;
  licenseEdition?: string;
  licenseExpiresAt?: string;
  instanceCount?: number;
  degradedCount?: number;
  quotaState?: QuotaState;
  className?: string;
};

function formatBalance(cents: number, symbol: string): string {
  return `${symbol}${(cents / 100).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

const quotaStateMeta: Record<QuotaState, { label: string; color: "success" | "warning" | "error" }> = {
  normal: { label: "健康", color: "success" },
  low: { label: "余额偏低", color: "warning" },
  critical: { label: "严重不足", color: "error" },
  frozen: { label: "已冻结", color: "error" },
};

/**
 * Balance / quota KPI summary — balance, quota, low balance, frozen states.
 * @see references/layout-patterns/control-plane.md
 */
export function BalanceQuotaSummary({
  balanceCents,
  currencySymbol = "¥",
  quotaPercent = 0,
  quotaUsed,
  quotaLimit,
  licenseEdition = "企业版",
  licenseExpiresAt,
  instanceCount = 0,
  degradedCount = 0,
  quotaState = "normal",
  className,
}: BalanceQuotaSummaryProps) {
  const quotaMeta = quotaStateMeta[quotaState];

  return (
    <div className={cn("space-y-4", className)}>
      {quotaState === "frozen" ? (
        <Alert variant="error" title="配额已冻结">
          同步错误解决前，余额更新将被阻止。
        </Alert>
      ) : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">余额</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-gray-800 dark:text-white/90">
            {balanceCents !== undefined ? formatBalance(balanceCents, currencySymbol) : "—"}
          </p>
          {quotaState === "low" || quotaState === "critical" ? (
            <Badge variant="light" color={quotaMeta.color} size="sm" className="mt-2">
              {quotaMeta.label}
            </Badge>
          ) : (
            <p className="mt-1 text-theme-xs text-success-600 dark:text-success-500">余额预警未触发</p>
          )}
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">API 配额</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-gray-800 dark:text-white/90">
            {quotaPercent}%
          </p>
          {quotaUsed && quotaLimit ? (
            <p className="mt-1 text-theme-xs text-gray-500">
              {quotaUsed} / {quotaLimit} req
            </p>
          ) : null}
          <Progress value={quotaPercent} className="mt-3 h-2" />
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">License</p>
          <p className="mt-1 text-base font-semibold text-gray-800 dark:text-white/90">{licenseEdition}</p>
          {licenseExpiresAt ? (
            <p className="mt-1 text-theme-xs text-success-600 dark:text-success-500">
              有效期至 {licenseExpiresAt}
            </p>
          ) : null}
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">实例数</p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-gray-800 dark:text-white/90">
            {instanceCount}
          </p>
          {degradedCount > 0 ? (
            <p className="mt-1 text-theme-xs text-warning-600 dark:text-warning-500">
              {degradedCount} 个异常
            </p>
          ) : (
            <p className="mt-1 text-theme-xs text-gray-500">全部健康</p>
          )}
        </div>
      </div>
    </div>
  );
}
