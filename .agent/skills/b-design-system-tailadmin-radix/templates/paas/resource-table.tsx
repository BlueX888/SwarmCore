import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { MoreHorizontal } from "lucide-react";

export type ResourceKind = "k8s" | "elasticsearch" | "mysql" | "redis" | "host";

export type ResourceStatus =
  | "running"
  | "degraded"
  | "stopped"
  | "creating"
  | "failed"
  | "maintenance";

export type ResourceRow = {
  id: string;
  name: string;
  kind: ResourceKind;
  namespace?: string;
  version?: string;
  spec?: string;
  usage?: string;
  status: ResourceStatus;
  region?: string;
};

export type ResourceTableProps = {
  resources: ResourceRow[];
  onRowClick?: (id: string) => void;
  onAction?: (id: string, action: string) => void;
  className?: string;
};

const kindLabel: Record<ResourceKind, string> = {
  k8s: "Kubernetes",
  elasticsearch: "Elasticsearch",
  mysql: "MySQL",
  redis: "Redis",
  host: "主机",
};

const statusBadge: Record<
  ResourceStatus,
  { label: string; color: "success" | "warning" | "error" | "primary" | "light" }
> = {
  running: { label: "运行中", color: "success" },
  degraded: { label: "降级", color: "warning" },
  stopped: { label: "已停止", color: "light" },
  creating: { label: "创建中", color: "primary" },
  failed: { label: "失败", color: "error" },
  maintenance: { label: "维护中", color: "warning" },
};

/**
 * PaaS 资源列表 — K8s/ES/MySQL/Redis/Host 通用状态列。
 * @see references/layout-patterns/paas-resource.md
 */
export function ResourceTable({
  resources,
  onRowClick,
  onAction,
  className,
}: ResourceTableProps) {
  return (
    <div className={cn("overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800", className)}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>资源名称</TableHead>
            <TableHead>类型</TableHead>
            <TableHead>命名空间</TableHead>
            <TableHead>版本</TableHead>
            <TableHead>规格</TableHead>
            <TableHead>用量</TableHead>
            <TableHead>状态</TableHead>
            <TableHead className="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {resources.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="py-8 text-center text-theme-sm text-gray-500">
                当前租户暂无资源实例。
              </TableCell>
            </TableRow>
          ) : (
            resources.map((row) => {
              const badge = statusBadge[row.status];
              return (
                <TableRow
                  key={row.id}
                  className="cursor-pointer"
                  onClick={() => onRowClick?.(row.id)}
                >
                  <TableCell className="max-w-[180px] truncate font-medium">{row.name}</TableCell>
                  <TableCell className="text-theme-xs text-gray-500">{kindLabel[row.kind]}</TableCell>
                  <TableCell className="max-w-[120px] truncate font-mono text-theme-xs text-gray-500">
                    {row.namespace ?? "—"}
                  </TableCell>
                  <TableCell className="tabular-nums text-theme-xs">{row.version ?? "—"}</TableCell>
                  <TableCell className="text-theme-xs text-gray-500">{row.spec ?? "—"}</TableCell>
                  <TableCell className="tabular-nums text-theme-xs">{row.usage ?? "—"}</TableCell>
                  <TableCell>
                    <Badge variant="light" color={badge.color} size="sm">
                      {badge.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="h-7 w-7 p-0"
                      onClick={(e) => {
                        e.stopPropagation();
                        onAction?.(row.id, "menu");
                      }}
                      aria-label={`${row.name} 更多操作`}
                    >
                      <MoreHorizontal className="size-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </div>
  );
}
