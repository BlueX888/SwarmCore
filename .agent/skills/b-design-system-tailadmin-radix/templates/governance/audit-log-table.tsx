import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Download, Search } from "lucide-react";

export type AuditSeverity = "info" | "warning" | "critical";

export type AuditLogRow = {
  id: string;
  timestamp: string;
  actor: string;
  object: string;
  action: string;
  severity?: AuditSeverity;
  ip?: string;
};

export type AuditLogTableProps = {
  rows: AuditLogRow[];
  loading?: boolean;
  onExport?: () => void;
  onRowClick?: (id: string) => void;
  onSearch?: (query: string) => void;
  className?: string;
};

const severityBadge: Record<
  AuditSeverity,
  { label: string; color: "primary" | "warning" | "error" }
> = {
  info: { label: "信息", color: "primary" },
  warning: { label: "警告", color: "warning" },
  critical: { label: "高危", color: "error" },
};

/**
 * 审计日志表 — 时间范围、操作者、对象、动作、导出、详情抽屉入口。
 * @see references/component-styles/governance-template.md
 */
export function AuditLogTable({
  rows,
  loading = false,
  onExport,
  onRowClick,
  onSearch,
  className,
}: AuditLogTableProps) {
  const [query, setQuery] = React.useState("");

  return (
    <section className={cn("space-y-4", className)} aria-label="审计日志">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
          <Input
            className="pl-9"
            placeholder="搜索操作者、对象或动作…"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              onSearch?.(event.target.value);
            }}
            aria-label="搜索审计日志"
          />
        </div>
        <Button type="button" variant="outline" size="sm" onClick={onExport}>
          <Download className="size-4" />
          导出 CSV
        </Button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-800">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-[160px]">时间</TableHead>
              <TableHead>操作者</TableHead>
              <TableHead>对象</TableHead>
              <TableHead>动作</TableHead>
              <TableHead>级别</TableHead>
              <TableHead className="text-right">IP</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="py-10 text-center text-theme-sm text-gray-500">
                  加载审计记录…
                </TableCell>
              </TableRow>
            ) : rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-10 text-center text-theme-sm text-gray-500">
                  当前时间范围内无审计记录
                </TableCell>
              </TableRow>
            ) : (
              rows.map((row) => {
                const severity = row.severity ?? "info";
                const meta = severityBadge[severity];
                return (
                  <TableRow
                    key={row.id}
                    className={onRowClick ? "cursor-pointer hover:bg-gray-50 dark:hover:bg-white/[0.02]" : undefined}
                    onClick={() => onRowClick?.(row.id)}
                  >
                    <TableCell className="tabular-nums text-theme-xs text-gray-500">
                      {row.timestamp}
                    </TableCell>
                    <TableCell className="font-medium">{row.actor}</TableCell>
                    <TableCell className="max-w-[200px] truncate font-mono text-theme-sm">
                      {row.object}
                    </TableCell>
                    <TableCell>{row.action}</TableCell>
                    <TableCell>
                      <Badge variant="light" color={meta.color} size="sm">
                        {meta.label}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono text-theme-xs text-gray-500">
                      {row.ip ?? "—"}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
      <p className="text-theme-xs text-gray-500">
        点击行可打开详情抽屉查看请求体、变更前后与关联会话。
      </p>
    </section>
  );
}
