import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ApprovalTimeline } from "../../../devops/approval-timeline";
import { ArtifactTable } from "../../../devops/artifact-table";
import { RollbackDialog } from "../../../devops/danger-zone";
import { LogStreamPanel } from "../../../devops/log-stream-panel";
import { PipelineStageBar } from "../../../devops/pipeline-stage-bar";
import { pipelineRunDetailMock, type PipelineRunDetailMock } from "./mock-data";

export type PipelineRunDetailPageProps = {
  data?: PipelineRunDetailMock;
  logsLoading?: boolean;
  onRetry?: () => void;
  onRollback?: () => void;
  onArtifactDownload?: (artifactId: string) => void;
};

const statusBadge: Record<
  PipelineRunDetailMock["status"],
  { label: string; color: "primary" | "success" | "error" | "warning" }
> = {
  running: { label: "运行中", color: "primary" },
  success: { label: "成功", color: "success" },
  failed: { label: "失败", color: "error" },
  canceled: { label: "已取消", color: "warning" },
};

/**
 * S03-D03 流水线运行详情 — 阶段条 + 日志联动 + 制品表 + 审批时间线。
 * @see docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S03-devops.md#s03-d03
 */
export function PipelineRunDetailPage({
  data = pipelineRunDetailMock,
  logsLoading = false,
  onRetry,
  onRollback,
  onArtifactDownload,
}: PipelineRunDetailPageProps) {
  const failedStage = data.stages.find((stage) => stage.status === "failed");
  const initialStageId = failedStage?.id ?? data.stages[0]?.id ?? "checkout";

  const [selectedStageId, setSelectedStageId] = React.useState(initialStageId);
  const [paused, setPaused] = React.useState(false);
  const [autoScroll, setAutoScroll] = React.useState(true);
  const [logSearch, setLogSearch] = React.useState("");
  const [rollbackOpen, setRollbackOpen] = React.useState(false);
  const [retrying, setRetrying] = React.useState(false);

  const currentLogs = data.logsByStage[selectedStageId] ?? [];
  const badge = statusBadge[data.status];

  const handleRetry = () => {
    setRetrying(true);
    onRetry?.();
    window.setTimeout(() => setRetrying(false), 1200);
  };

  return (
    <div className="space-y-6" data-scenario-page="pipeline-run-detail">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">
              {data.pipelineName}
            </h1>
            <span className="font-mono text-theme-sm text-gray-500">#{data.runId}</span>
            <Badge variant="light" color={badge.color} size="sm">
              {badge.label}
            </Badge>
          </div>
          <p className="text-theme-sm text-gray-500">
            分支 {data.branch} · 触发人 {data.triggerBy} · 开始于 {data.startedAt} · 耗时 {data.duration}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" size="sm" disabled={retrying} onClick={handleRetry}>
            {retrying ? "重试中…" : "重试"}
          </Button>
          <Button type="button" variant="destructive" size="sm" onClick={() => setRollbackOpen(true)}>
            回滚
          </Button>
        </div>
      </header>

      <section>
        <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">流水线阶段</h2>
        <PipelineStageBar
          stages={data.stages}
          activeStageId={selectedStageId}
          onStageSelect={setSelectedStageId}
        />
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="flex flex-col gap-4 xl:col-span-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">
              构建日志
              <span className="ml-2 font-normal text-gray-500">
                （{data.stages.find((s) => s.id === selectedStageId)?.label ?? "—"}）
              </span>
            </h2>
            <label className="flex items-center gap-2 text-theme-xs text-gray-500">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(event) => setAutoScroll(event.target.checked)}
              />
              自动滚动
            </label>
          </div>
          {logsLoading ? (
            <div className="flex h-[220px] items-center justify-center rounded-xl border border-gray-200 bg-gray-50 text-theme-sm text-gray-500 dark:border-gray-800 dark:bg-white/[0.02]">
              日志加载中…
            </div>
          ) : (
            <LogStreamPanel
              lines={currentLogs}
              height={220}
              paused={paused}
              onPauseToggle={() => setPaused((value) => !value)}
              search={logSearch}
              onSearchChange={setLogSearch}
              autoScroll={autoScroll}
            />
          )}
          <p className="text-theme-xs text-gray-500">
            点击阶段切换日志；支持暂停、搜索与自动滚动开关。
          </p>
        </div>

        <div>
          <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">制品列表</h2>
          <ArtifactTable artifacts={data.artifacts} onDownload={onArtifactDownload} />
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">审批记录</h2>
        <ApprovalTimeline events={data.approvals} />
      </section>

      <RollbackDialog
        open={rollbackOpen}
        onOpenChange={setRollbackOpen}
        currentVersion={data.currentVersion}
        targetVersion={data.targetRollbackVersion}
        environment={data.environment}
        objectName={data.runId}
        onConfirm={() => {
          onRollback?.();
          setRollbackOpen(false);
        }}
      />
    </div>
  );
}

export default PipelineRunDetailPage;
