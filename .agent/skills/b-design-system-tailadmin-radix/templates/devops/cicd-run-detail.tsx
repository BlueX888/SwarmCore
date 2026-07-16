import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { PipelineStageBar, type PipelineStage } from "./pipeline-stage-bar";
import { LogStreamPanel, type LogLine } from "./log-stream-panel";
import { ArtifactTable, type ArtifactRow } from "./artifact-table";
import { DangerZone, type DangerAction } from "./danger-zone";

export type RunMetadataItem = {
  label: string;
  value: React.ReactNode;
};

export type CicdRunDetailProps = {
  runId: string;
  stages: PipelineStage[];
  logs: LogLine[];
  artifacts: ArtifactRow[];
  metadata?: RunMetadataItem[];
  dangerActions?: DangerAction[];
  onRetry?: () => void;
  onCancel?: () => void;
  onDangerAction?: (actionId: string) => void;
  className?: string;
};

/**
 * CI/CD Run Detail page composition — stage bar + logs + artifacts + metadata sidebar.
 * @see references/layout-patterns/cicd-release.md
 * @see templates/devops/pipeline-stage-bar.tsx
 * @see templates/devops/log-stream-panel.tsx
 * @see templates/devops/artifact-table.tsx
 */
export function CicdRunDetail({
  runId,
  stages,
  logs,
  artifacts,
  metadata = [],
  dangerActions = [],
  onRetry,
  onCancel,
  onDangerAction,
  className,
}: CicdRunDetailProps) {
  const [paused, setPaused] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const [severity, setSeverity] = React.useState<"all" | "info" | "warn" | "error">("all");

  return (
    <div className={cn("grid grid-cols-1 gap-6 xl:grid-cols-3", className)}>
      <div className="flex flex-col gap-6 xl:col-span-2">
        <section>
          <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">
            Pipeline stages
          </h2>
          <PipelineStageBar stages={stages} />
        </section>

        <section>
          <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">
            Build logs
          </h2>
          <LogStreamPanel
            lines={logs}
            height={180}
            paused={paused}
            onPauseToggle={() => setPaused((p) => !p)}
            search={search}
            onSearchChange={setSearch}
            severityFilter={severity}
            onSeverityFilterChange={setSeverity}
          />
        </section>

        <section>
          <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">
            Artifacts
          </h2>
          <ArtifactTable artifacts={artifacts} />
        </section>
      </div>

      <div className="flex flex-col gap-6">
        <section className="rounded-xl border border-gray-200 p-4 dark:border-gray-800">
          <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">
            Run details
          </h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-theme-xs text-gray-500">运行 ID</dt>
              <dd className="font-mono text-theme-sm">{runId}</dd>
            </div>
            {metadata.map((item) => (
              <div key={item.label}>
                <dt className="text-theme-xs text-gray-500">{item.label}</dt>
                <dd className="text-theme-sm text-gray-800 dark:text-white/90">{item.value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="rounded-xl border border-gray-200 p-4 dark:border-gray-800">
          <h2 className="mb-3 text-theme-sm font-semibold text-gray-800 dark:text-white/90">
            Actions
          </h2>
          <div className="flex flex-col gap-2">
            <Button type="button" variant="outline" size="sm" onClick={onRetry}>
              Retry job
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={onCancel}>
              Cancel run
            </Button>
          </div>
        </section>

        {dangerActions.length > 0 ? (
          <DangerZone actions={dangerActions} onAction={onDangerAction} />
        ) : null}
      </div>
    </div>
  );
}
