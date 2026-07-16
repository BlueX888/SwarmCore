import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { RefreshCw } from "lucide-react";

export type SyncTrackStatus = "ok" | "pending" | "error" | "stale" | "frozen";

export type SyncTrack = {
  id: string;
  label: string;
  status: SyncTrackStatus;
  lastSuccess?: string;
  lastError?: string;
  hint?: string;
};

export type SyncHealthPanelProps = {
  tracks: SyncTrack[];
  frozen?: boolean;
  onRetry?: (trackId: string) => void;
  onSyncAll?: () => void;
  className?: string;
};

const statusMeta: Record<
  SyncTrackStatus,
  { label: string; color: "success" | "warning" | "error" | "light" | "dark"; textClass: string }
> = {
  ok: { label: "正常", color: "success", textClass: "text-success-600 dark:text-success-500" },
  pending: { label: "等待中", color: "light", textClass: "text-gray-500" },
  error: { label: "错误", color: "error", textClass: "text-error-600 dark:text-error-500" },
  stale: { label: "过期", color: "warning", textClass: "text-warning-600 dark:text-warning-500" },
  frozen: { label: "冻结", color: "error", textClass: "text-error-600 dark:text-error-500" },
};

/**
 * Sync health panel — quota/report/HMAC/heartbeat multi-track status.
 * @see references/layout-patterns/control-plane.md
 */
export function SyncHealthPanel({
  tracks,
  frozen = false,
  onRetry,
  onSyncAll,
  className,
}: SyncHealthPanelProps) {
  return (
    <section className={cn("space-y-4", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">同步健康度</h3>
        {onSyncAll ? (
          <Button type="button" variant="outline" size="sm" onClick={onSyncAll}>
            <RefreshCw className="size-3.5" />
            全部同步
          </Button>
        ) : null}
      </div>

      {frozen ? (
        <Alert variant="error" title="配额已冻结">
          同步失败阻止了配额更新，请进入同步页签重试失败轨道。
        </Alert>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        {tracks.map((track) => {
          const meta = statusMeta[track.status];
          return (
            <div
              key={track.id}
              className="flex flex-col gap-2 rounded-xl border border-gray-200 bg-white p-3 dark:border-white/[0.05] dark:bg-white/[0.03]"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-theme-sm font-medium text-gray-800 dark:text-white/90">
                  {track.label}
                </span>
                <Badge variant="light" color={meta.color} size="sm">
                  {meta.label}
                </Badge>
              </div>
              {track.lastSuccess ? (
                <p className={cn("text-theme-xs tabular-nums", meta.textClass)}>
                  {track.status === "ok" || track.status === "stale"
                    ? `上次成功 · ${track.lastSuccess}`
                    : track.status === "pending"
                      ? "等待首次同步"
                      : `上次尝试 · ${track.lastSuccess}`}
                </p>
              ) : null}
              {track.lastError ? (
                <p className="text-theme-xs text-error-600 dark:text-error-500">{track.lastError}</p>
              ) : null}
              {track.hint ? (
                <p className="text-theme-xs text-gray-500">{track.hint}</p>
              ) : null}
              {track.status === "error" && onRetry ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="self-start"
                  onClick={() => onRetry(track.id)}
                >
                  重试
                </Button>
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}
