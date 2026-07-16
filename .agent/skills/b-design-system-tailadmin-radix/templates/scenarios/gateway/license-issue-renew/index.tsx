import * as React from "react";
import { FileKey2 } from "lucide-react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { LicenseIssuePanel } from "../../../gateway/license-issue-panel";
import { DangerZone } from "../../../devops/danger-zone";
import {
  auditActionLabel,
  licenseAuditEntries,
  licenseDangerActions,
  licenseSummary,
  type LicenseAuditEntry,
  type LicenseSummaryStatus,
} from "./mock-data";

export type LicenseIssueRenewPageProps = {
  summary?: typeof licenseSummary;
  auditEntries?: LicenseAuditEntry[];
  issuedLicense?: string | null;
  onIssue?: () => void;
  onRenew?: (license: string) => void;
  onDangerAction?: (actionId: string) => void;
  onCopyLicense?: () => void;
  className?: string;
};

const statusMeta: Record<LicenseSummaryStatus, { label: string; color: "success" | "warning" | "error" }> = {
  valid: { label: "有效", color: "success" },
  expiring: { label: "即将到期", color: "warning" },
  expired: { label: "已过期", color: "error" },
};

/**
 * S02-G05 License 签发续期 — 运营代签 + 一次性复制 + DangerZone 续期确认。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g05
 * @see references/layout-patterns/control-plane.md
 */
export function LicenseIssueRenewPage({
  summary = licenseSummary,
  auditEntries = licenseAuditEntries,
  issuedLicense = null,
  onIssue,
  onRenew,
  onDangerAction,
  onCopyLicense,
  className,
}: LicenseIssueRenewPageProps) {
  const status = statusMeta[summary.status];

  return (
    <div className={cn("w-full space-y-6", className)} data-scenario-page="license-issue-renew">
      <header className="space-y-1">
        <div className="inline-flex items-center gap-2 text-brand-600 dark:text-brand-400">
          <FileKey2 className="size-4" aria-hidden="true" />
          <span className="text-theme-xs font-medium uppercase tracking-wide">Gateway License 运营台</span>
        </div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">License 签发续期</h1>
        <p className="text-theme-sm text-gray-500">
          为企业实例代签离线 License、一次性复制交付，并通过危险区确认续期或吊销操作。
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">License 版本</p>
          <p className="mt-1 text-theme-sm font-semibold text-gray-900 dark:text-white">{summary.edition}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">当前状态</p>
          <div className="mt-2">
            <Badge variant="light" color={status.color} size="sm">
              {status.label}
            </Badge>
          </div>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">有效期至</p>
          <p className="mt-1 font-mono text-theme-sm tabular-nums text-gray-900 dark:text-white">
            {summary.expiresAt}
          </p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-white/[0.05] dark:bg-white/[0.03]">
          <p className="text-theme-xs text-gray-500">绑定实例</p>
          <p className="mt-1 truncate font-mono text-theme-sm text-gray-900 dark:text-white">
            {summary.boundInstance}
          </p>
          <p className="mt-1 text-theme-xs text-gray-500">
            {summary.orgName} · {summary.seats} 席位
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <LicenseIssuePanel
          mode="issue"
          edition={summary.edition}
          status={summary.status === "expired" ? "expired" : summary.status === "expiring" ? "expiring" : "valid"}
          expiresAt={summary.expiresAt}
          issuedLicense={issuedLicense}
          showOnce
          onIssue={onIssue}
          onCopy={onCopyLicense}
        />
        <LicenseIssuePanel
          mode="renew"
          edition={summary.edition}
          status={summary.status === "expired" ? "expired" : "expiring"}
          expiresAt={summary.expiresAt}
          onRenew={onRenew}
        />
      </div>

      <DangerZone
        title="危险操作区"
        description="吊销或强制续期将立即影响实例写入权限，操作前请确认已与租户沟通。"
        actions={licenseDangerActions}
        onAction={onDangerAction}
      />

      <section className="rounded-xl border border-gray-200 bg-white dark:border-white/[0.05] dark:bg-white/[0.03]">
        <div className="border-b border-gray-100 px-4 py-3 dark:border-gray-800">
          <h2 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">签发与续期审计</h2>
          <p className="mt-1 text-theme-xs text-gray-500">最近 30 天运营操作留痕，供合规复核。</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-theme-sm">
            <thead>
              <tr className="border-b border-gray-100 text-theme-xs text-gray-500 dark:border-gray-800">
                <th className="px-4 py-2.5 font-medium">时间</th>
                <th className="px-4 py-2.5 font-medium">操作</th>
                <th className="px-4 py-2.5 font-medium">操作人</th>
                <th className="px-4 py-2.5 font-medium">目标实例</th>
                <th className="px-4 py-2.5 font-medium">备注</th>
              </tr>
            </thead>
            <tbody>
              {auditEntries.map((entry) => (
                <tr
                  key={entry.id}
                  className="border-b border-gray-50 last:border-0 dark:border-white/[0.03]"
                >
                  <td className="px-4 py-3 tabular-nums text-gray-600 dark:text-gray-400">{entry.occurredAt}</td>
                  <td className="px-4 py-3">
                    <Badge
                      variant="light"
                      color={entry.action === "revoke" ? "error" : entry.action === "renew" ? "warning" : "success"}
                      size="sm"
                    >
                      {auditActionLabel[entry.action]}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-gray-800 dark:text-gray-200">{entry.operator}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-700 dark:text-gray-300">
                    {entry.targetInstance}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{entry.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default LicenseIssueRenewPage;
