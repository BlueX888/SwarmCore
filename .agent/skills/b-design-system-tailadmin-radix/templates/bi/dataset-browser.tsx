import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { QueryShell, type QueryStatus } from "@/components/ui/query-shell";
import { FieldListPanel, type BiFieldDef } from "./field-list-panel";

export type DatasetSummary = {
  id: string;
  name: string;
  source: string;
  rowCount?: number;
  status?: "ready" | "syncing" | "error";
};

export type ConnectionTestState = "idle" | "testing" | "success" | "error" | "forbidden";

export type DatasetBrowserProps = {
  datasets: DatasetSummary[];
  selectedId?: string;
  onSelect?: (id: string) => void;
  connectionState?: ConnectionTestState;
  onTestConnection?: () => void;
  fields?: BiFieldDef[];
  fieldsStatus?: QueryStatus;
  className?: string;
};

const connBadge: Record<ConnectionTestState, { label: string; variant: "default" | "secondary" | "destructive" }> = {
  idle: { label: "Not tested", variant: "secondary" },
  testing: { label: "Testing…", variant: "secondary" },
  success: { label: "Connected", variant: "default" },
  error: { label: "Failed", variant: "destructive" },
  forbidden: { label: "Denied", variant: "destructive" },
};

/**
 * Dataset list + field browser — master-detail for BI data sources.
 * @see references/layout-patterns/bi-dataset-management.md
 */
export function DatasetBrowser({
  datasets,
  selectedId,
  onSelect,
  connectionState = "idle",
  onTestConnection,
  fields = [],
  fieldsStatus = "success",
  className,
}: DatasetBrowserProps) {
  const selected = datasets.find((d) => d.id === selectedId) ?? datasets[0];
  const badge = connBadge[connectionState];

  return (
    <div className={cn("grid min-h-[400px] grid-cols-1 lg:grid-cols-[minmax(280px,34%)_minmax(0,1fr)] rounded-xl border border-gray-200 dark:border-gray-800", className)}>
      <div className="border-b border-gray-200 lg:border-b-0 lg:border-r dark:border-gray-800">
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-800">
          <h3 className="text-theme-sm font-semibold">Datasets ({datasets.length})</h3>
          <Button variant="outline" size="sm" onClick={onTestConnection} disabled={connectionState === "testing"}>
            {connectionState === "testing" ? <Spinner className="mr-2 size-4" /> : null}
            Test
          </Button>
        </div>
        <ul className="max-h-[360px] overflow-y-auto">
          {datasets.map((ds) => (
            <li key={ds.id}>
              <button
                type="button"
                onClick={() => onSelect?.(ds.id)}
                className={cn(
                  "flex w-full items-center justify-between gap-2 border-b border-gray-100 px-4 py-3 text-left text-theme-sm dark:border-white/[0.05]",
                  selected?.id === ds.id && "border-l-[3px] border-l-brand-500 bg-brand-50/50 pl-[13px] dark:bg-brand-500/10",
                )}
              >
                <div className="min-w-0">
                  <span className="block truncate font-medium text-gray-900 dark:text-white/90">{ds.name}</span>
                  <span className="text-theme-xs text-gray-500">{ds.source}</span>
                </div>
                {ds.status === "syncing" ? <Spinner className="size-4 shrink-0" /> : null}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex min-w-0 flex-col">
        <div className="flex items-center justify-between gap-2 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
          <div className="min-w-0">
            <h3 className="truncate text-theme-sm font-semibold">{selected?.name ?? "请选择数据集"}</h3>
            <p className="text-theme-xs text-gray-500">{selected?.rowCount?.toLocaleString() ?? "—"} rows</p>
          </div>
          <Badge variant={badge.variant}>{badge.label}</Badge>
        </div>
        <QueryShell status={fieldsStatus} minHeight={320} className="flex-1">
          <FieldListPanel fields={fields} className="min-h-[320px] border-0" />
        </QueryShell>
      </div>
    </div>
  );
}
