import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExportMenu, type ExportContext, type ExportFormat } from "./export-menu";
import { ExportJobPanel, type ExportJob } from "./export-job-panel";

export type SubscriptionFrequency = "daily" | "weekly" | "monthly";

export type SubscriptionStatus = "active" | "paused" | "failed";

export type ReportSubscription = {
  id: string;
  name: string;
  frequency: SubscriptionFrequency;
  format: ExportFormat;
  recipients: string;
  nextRunAt: string;
  status: SubscriptionStatus;
};

const frequencyLabel: Record<SubscriptionFrequency, string> = {
  daily: "每日",
  weekly: "每周",
  monthly: "每月",
};

const subscriptionStatusLabel: Record<SubscriptionStatus, string> = {
  active: "运行中",
  paused: "已暂停",
  failed: "发送失败",
};

export type ExportSubscriptionDashboardProps = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  exportContext?: ExportContext;
  dataScreenSize?: string;
  theme?: "light" | "dark" | "current";
  exportLoading?: boolean;
  jobs: ExportJob[];
  subscriptions?: ReportSubscription[];
  onExport?: (format: ExportFormat) => void;
  onDownloadJob?: (job: ExportJob) => void;
  onRetryJob?: (job: ExportJob) => void;
  onCancelJob?: (job: ExportJob) => void;
  onEditSubscription?: (sub: ReportSubscription) => void;
  onToggleSubscription?: (sub: ReportSubscription) => void;
  renderMain: () => React.ReactNode;
  className?: string;
};

/**
 * BI 导出与订阅仪表盘 — ExportMenu + 任务面板 + 定时订阅列表。
 * @see references/layout-patterns/bi-export-subscription.md
 */
export function ExportSubscriptionDashboard({
  title = "报表导出与订阅",
  description,
  exportContext = "dashboard",
  dataScreenSize,
  theme = "current",
  exportLoading = false,
  jobs,
  subscriptions = [],
  onExport,
  onDownloadJob,
  onRetryJob,
  onCancelJob,
  onEditSubscription,
  onToggleSubscription,
  renderMain,
  className,
}: ExportSubscriptionDashboardProps) {
  return (
    <div className={cn("flex flex-col gap-4", className)}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          {title ? (
            <h2 className="text-title-sm font-semibold text-gray-900 dark:text-white/90">{title}</h2>
          ) : null}
          {description ? (
            <p className="mt-1 text-theme-sm text-gray-500">{description}</p>
          ) : null}
        </div>
        <ExportMenu
          context={exportContext}
          dataScreenSize={dataScreenSize}
          theme={theme}
          loading={exportLoading}
          onExport={onExport}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="min-w-0">{renderMain()}</div>
        <aside className="flex flex-col gap-4">
          <ExportJobPanel
            jobs={jobs}
            onDownload={onDownloadJob}
            onRetry={onRetryJob}
            onCancel={onCancelJob}
          />
          {subscriptions.length > 0 ? (
            <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
              <div className="border-b border-gray-100 px-5 py-4 dark:border-white/[0.05]">
                <h3 className="text-theme-sm font-semibold text-gray-900 dark:text-white/90">
                  定时订阅
                </h3>
                <p className="mt-0.5 text-theme-xs text-gray-500">邮件推送报表与快照</p>
              </div>
              <ul className="divide-y divide-gray-100 dark:divide-white/[0.05]">
                {subscriptions.map((sub) => (
                  <li key={sub.id} className="flex flex-col gap-2 px-5 py-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate text-theme-sm font-medium text-gray-900 dark:text-white/90">
                          {sub.name}
                        </p>
                        <p className="mt-0.5 text-theme-xs text-gray-500">
                          {frequencyLabel[sub.frequency]} · {sub.format.toUpperCase()} · {sub.recipients}
                        </p>
                      </div>
                      <Badge variant={sub.status === "active" ? "success" : "secondary"}>
                        {subscriptionStatusLabel[sub.status]}
                      </Badge>
                    </div>
                    <p className="text-theme-xs text-gray-500">下次发送：{sub.nextRunAt}</p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        type="button"
                        onClick={() => onEditSubscription?.(sub)}
                      >
                        编辑
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        type="button"
                        onClick={() => onToggleSubscription?.(sub)}
                      >
                        {sub.status === "active" ? "暂停" : "启用"}
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}
