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
import { Download, FileWarning } from "lucide-react";

export type ArtifactStatus = "available" | "expired" | "scanning" | "failed";

export type ArtifactRow = {
  id: string;
  name: string;
  digest: string;
  size: string;
  expiresAt?: string;
  status: ArtifactStatus;
  scanReportUrl?: string;
};

export type ArtifactTableProps = {
  artifacts: ArtifactRow[];
  onDownload?: (id: string) => void;
  onViewScan?: (id: string) => void;
  className?: string;
};

const statusBadge: Record<
  ArtifactStatus,
  { label: string; color: "success" | "warning" | "error" | "primary" }
> = {
  available: { label: "可下载", color: "success" },
  expired: { label: "已过期", color: "warning" },
  scanning: { label: "扫描中", color: "primary" },
  failed: { label: "失败", color: "error" },
};

/**
 * CI/CD artifact table — digest, size, expire, download, scan report.
 * @see references/layout-patterns/cicd-release.md
 */
export function ArtifactTable({
  artifacts,
  onDownload,
  onViewScan,
  className,
}: ArtifactTableProps) {
  return (
    <div className={cn("overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800", className)}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>名称</TableHead>
            <TableHead>摘要</TableHead>
            <TableHead>大小</TableHead>
            <TableHead>过期时间</TableHead>
            <TableHead>状态</TableHead>
            <TableHead className="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {artifacts.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="py-8 text-center text-theme-sm text-gray-500">
                本次运行暂无制品。
              </TableCell>
            </TableRow>
          ) : (
            artifacts.map((row) => {
              const badge = statusBadge[row.status];
              const canDownload = row.status === "available";

              return (
                <TableRow key={row.id}>
                  <TableCell className="max-w-[160px] truncate font-medium">{row.name}</TableCell>
                  <TableCell className="max-w-[120px] truncate font-mono text-theme-xs text-gray-500">
                    {row.digest}
                  </TableCell>
                  <TableCell className="tabular-nums">{row.size}</TableCell>
                  <TableCell className="text-theme-xs text-gray-500">{row.expiresAt ?? "—"}</TableCell>
                  <TableCell>
                    <Badge variant="light" color={badge.color} size="sm">
                      {badge.label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="h-7 gap-1 px-2"
                        disabled={!canDownload}
                        onClick={() => onDownload?.(row.id)}
                      >
                        <Download className="size-3" />
                        下载
                      </Button>
                      {row.scanReportUrl ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          className="h-7 gap-1 px-2"
                          onClick={() => onViewScan?.(row.id)}
                        >
                          <FileWarning className="size-3" />
                          扫描报告
                        </Button>
                      ) : null}
                    </div>
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
