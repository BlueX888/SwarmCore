import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import type { ExportFormat } from "./export-menu";

export type ExportJobStatus =
  | "exporting"
  | "queued"
  | "failed"
  | "expired"
  | "ready";

export type ExportJob = {
  id: string;
  name: string;
  format: ExportFormat;
  status: ExportJobStatus;
  progress?: number;
  createdAt: string;
  expiresAt?: string;
  fileSize?: string;
  errorMessage?: string;
  /** 大屏导出时记录画布与主题 */
  captureMeta?: string;
};

const statusLabel: Record<ExportJobStatus, string> = {
  queued: "排队中",
  exporting: "导出中",
  ready: "可下载",
  failed: "失败",
  expired: "已过期",
};

const statusVariant: Record<
  ExportJobStatus,
  "default" | "secondary" | "success" | "warning" | "destructive"
> = {
  queued: "secondary",
  exporting: "default",
  ready: "success",
  failed: "destructive",
  expired: "secondary",
};

const formatLabel: Record<ExportFormat, string> = {
  png: "PNG",
  pdf: "PDF",
  excel: "Excel",
  csv: "CSV",
};

export type ExportJobPanelProps = {
  title?: React.ReactNode;
  jobs: ExportJob[];
  onDownload?: (job: ExportJob) => void;
  onRetry?: (job: ExportJob) => void;
  onCancel?: (job: ExportJob) => void;
  className?: string;
};

/**
 * BI 导出任务面板 — queued / exporting / ready / failed / expired 状态列表。
 * @see references/layout-patterns/bi-export-subscription.md
 */
export function ExportJobPanel({
  title = "导出任务",
  jobs,
  onDownload,
  onRetry,
  onCancel,
  className,
}: ExportJobPanelProps) {
  return (
    <div
      className={cn(
        "flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
    >
      <div className="border-b border-gray-100 px-5 py-4 dark:border-white/[0.05]">
        <h3 className="text-theme-sm font-semibold text-gray-900 dark:text-white/90">{title}</h3>
        <p className="mt-0.5 text-theme-xs text-gray-500">异步导出任务与下载链接</p>
      </div>
      <ul className="divide-y divide-gray-100 dark:divide-white/[0.05]">
        {jobs.length === 0 ? (
          <li className="px-5 py-8 text-center text-theme-sm text-gray-500">暂无导出任务</li>
        ) : (
          jobs.map((job) => (
            <li key={job.id} className="flex flex-col gap-2 px-5 py-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-theme-sm font-medium text-gray-900 dark:text-white/90">
                    {job.name}
                  </p>
                  <p className="mt-0.5 text-theme-xs text-gray-500">
                    {formatLabel[job.format]} · {job.createdAt}
                    {job.captureMeta ? ` · ${job.captureMeta}` : null}
                  </p>
                </div>
                <Badge variant={statusVariant[job.status]}>{statusLabel[job.status]}</Badge>
              </div>

              {job.status === "exporting" ? (
                <div className="flex items-center gap-3">
                  <div className="h-1 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
                    <div
                      className="h-full rounded-full bg-brand-500 transition-all"
                      style={{ width: `${job.progress ?? 40}%` }}
                    />
                  </div>
                  <span className="flex items-center gap-1 text-theme-xs text-gray-500">
                    <Spinner className="size-3" />
                    {job.progress ?? 0}%
                  </span>
                </div>
              ) : null}

              {job.status === "failed" && job.errorMessage ? (
                <p className="text-theme-xs text-error-500">{job.errorMessage}</p>
              ) : null}

              {job.status === "expired" ? (
                <p className="text-theme-xs text-gray-500">
                  下载链接已于 {job.expiresAt ?? "24 小时前"} 过期，请重新导出。
                </p>
              ) : null}

              {job.status === "ready" && job.fileSize ? (
                <p className="text-theme-xs text-gray-500">
                  文件大小 {job.fileSize}
                  {job.expiresAt ? ` · 有效期至 ${job.expiresAt}` : null}
                </p>
              ) : null}

              <div className="flex flex-wrap gap-2">
                {job.status === "ready" ? (
                  <Button size="sm" type="button" onClick={() => onDownload?.(job)}>
                    下载
                  </Button>
                ) : null}
                {job.status === "failed" ? (
                  <Button size="sm" variant="outline" type="button" onClick={() => onRetry?.(job)}>
                    重试
                  </Button>
                ) : null}
                {job.status === "queued" ? (
                  <Button size="sm" variant="ghost" type="button" onClick={() => onCancel?.(job)}>
                    取消
                  </Button>
                ) : null}
                {job.status === "expired" ? (
                  <Button size="sm" variant="outline" type="button" onClick={() => onRetry?.(job)}>
                    重新导出
                  </Button>
                ) : null}
              </div>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
