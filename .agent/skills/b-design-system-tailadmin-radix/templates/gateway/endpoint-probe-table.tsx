import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Activity } from "lucide-react";

export type EndpointProbeStatus = "ready" | "failed" | "unknown" | "testing";

export type EndpointProbeRow = {
  id: string;
  endpoint: string;
  instanceId: string;
  status: EndpointProbeStatus;
  latency?: string;
  hint?: string;
};

export type EndpointProbeTableProps = {
  rows: EndpointProbeRow[];
  debounceMs?: number;
  onProbe?: (rowId: string) => void;
  className?: string;
};

const statusMeta: Record<
  EndpointProbeStatus,
  { label: string; color: "success" | "error" | "warning" | "primary" }
> = {
  ready: { label: "就绪", color: "success" },
  failed: { label: "失败", color: "error" },
  unknown: { label: "未知", color: "warning" },
  testing: { label: "探测中", color: "primary" },
};

/**
 * Endpoint probe table — ready/failed/unknown/testing with debounced row probe.
 * @see references/layout-patterns/control-plane.md
 */
export function EndpointProbeTable({
  rows,
  debounceMs = 300,
  onProbe,
  className,
}: EndpointProbeTableProps) {
  const [probing, setProbing] = React.useState<Record<string, boolean>>({});
  const timers = React.useRef<Record<string, number>>({});

  const handleProbe = (rowId: string) => {
    if (probing[rowId]) return;
    setProbing((prev) => ({ ...prev, [rowId]: true }));
    window.clearTimeout(timers.current[rowId]);
    timers.current[rowId] = window.setTimeout(() => {
      onProbe?.(rowId);
      setProbing((prev) => ({ ...prev, [rowId]: false }));
    }, debounceMs);
  };

  React.useEffect(() => {
    const current = timers.current;
    return () => {
      Object.values(current).forEach((id) => window.clearTimeout(id));
    };
  }, []);

  return (
    <section className={cn("space-y-3", className)}>
      <h3 className="text-theme-sm font-semibold text-gray-800 dark:text-white/90">端点探测</h3>
      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-white/[0.05]">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>端点</TableHead>
              <TableHead>实例</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>延迟</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => {
              const meta = statusMeta[row.status];
              const isTesting = row.status === "testing" || probing[row.id];
              return (
                <TableRow key={row.id}>
                  <TableCell className="max-w-[220px]">
                    <span className="block truncate font-mono text-xs" title={row.endpoint}>
                      {row.endpoint}
                    </span>
                    {row.hint ? (
                      <span className="mt-1 block truncate text-theme-xs text-gray-500" title={row.hint}>
                        {row.hint}
                      </span>
                    ) : null}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{row.instanceId}</TableCell>
                  <TableCell>
                    <Badge variant="light" color={isTesting ? "primary" : meta.color} size="sm">
                      {isTesting ? "探测中" : meta.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="tabular-nums text-theme-xs text-gray-600 dark:text-gray-400">
                    {row.latency ?? "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={isTesting}
                      onClick={() => handleProbe(row.id)}
                      aria-label={`探测 ${row.endpoint}`}
                    >
                      <Activity className="size-3.5" />
                      探测
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
