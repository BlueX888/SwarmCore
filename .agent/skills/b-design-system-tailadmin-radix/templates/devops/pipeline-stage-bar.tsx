import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Check, X, Minus, Ban } from "lucide-react";

export type PipelineStageStatus =
  | "queued"
  | "running"
  | "success"
  | "failed"
  | "skipped"
  | "canceled";

export type PipelineStage = {
  id: string;
  label: string;
  status: PipelineStageStatus;
  duration?: string;
};

export type PipelineStageBarProps = {
  stages: PipelineStage[];
  activeStageId?: string;
  onStageSelect?: (stageId: string) => void;
  className?: string;
};

const statusMeta: Record<
  PipelineStageStatus,
  { icon: React.ReactNode; badge: "primary" | "success" | "error" | "warning" | "light" | "dark" }
> = {
  queued: { icon: <Minus className="size-3.5" />, badge: "light" },
  running: { icon: <Spinner className="size-3.5" />, badge: "primary" },
  success: { icon: <Check className="size-3.5" />, badge: "success" },
  failed: { icon: <X className="size-3.5" />, badge: "error" },
  skipped: { icon: <Minus className="size-3.5" />, badge: "warning" },
  canceled: { icon: <Ban className="size-3.5" />, badge: "dark" },
};

const stageSurfaceClass = (isSelected: boolean, isFailed: boolean) =>
  cn(
    "flex min-w-[120px] flex-1 flex-col gap-1 rounded-lg border px-3 py-2 text-left transition-colors",
    isSelected
      ? "border-brand-500/40 bg-brand-50/50 dark:border-brand-500/30 dark:bg-brand-500/10"
      : isFailed
        ? "border-error-200/80 bg-error-50/40 dark:border-error-500/30 dark:bg-error-500/10"
        : "border-gray-100 bg-gray-50/50 dark:border-white/[0.05] dark:bg-white/[0.02]",
  );

/**
 * Horizontal pipeline stage bar — queued/running/success/failed/skipped/canceled.
 * @see references/layout-patterns/cicd-release.md
 */
export function PipelineStageBar({
  stages,
  activeStageId,
  onStageSelect,
  className,
}: PipelineStageBarProps) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-stretch gap-2 overflow-x-auto rounded-xl border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
      role="list"
      aria-label="流水线阶段"
    >
      {stages.map((stage, index) => {
        const meta = statusMeta[stage.status];
        const isSelected = stage.id === activeStageId;
        const isFailed = stage.status === "failed";

        const content = (
          <>
            <div className="flex items-center justify-between gap-2">
              <span className="truncate text-theme-xs font-medium text-gray-800 dark:text-white/90">
                {stage.label}
              </span>
              <span className="shrink-0 text-gray-500">{meta.icon}</span>
            </div>
            <div className="flex items-center justify-between gap-2">
              <Badge variant="light" color={meta.badge} size="sm">
                {stage.status}
              </Badge>
              {stage.duration ? (
                <span className="text-theme-xs tabular-nums text-gray-500">{stage.duration}</span>
              ) : null}
            </div>
          </>
        );

        return (
          <React.Fragment key={stage.id}>
            {onStageSelect ? (
              <button
                type="button"
                role="listitem"
                className={stageSurfaceClass(isSelected, isFailed)}
                aria-pressed={isSelected}
                onClick={() => onStageSelect(stage.id)}
              >
                {content}
              </button>
            ) : (
              <div role="listitem" className={stageSurfaceClass(isSelected, isFailed)}>
                {content}
              </div>
            )}
            {index < stages.length - 1 ? (
              <div className="hidden w-4 shrink-0 self-center border-t border-dashed border-gray-300 dark:border-gray-700 sm:block" />
            ) : null}
          </React.Fragment>
        );
      })}
    </div>
  );
}
