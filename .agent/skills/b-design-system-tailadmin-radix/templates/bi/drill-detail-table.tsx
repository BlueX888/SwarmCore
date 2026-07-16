import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DataTableCard } from "@/templates/ui/data-table-card";
import type { QueryStatus } from "@/components/ui/query-shell";

export type DrillDetailColumn<T = Record<string, unknown>> = {
  id: string;
  header: string;
  accessor: (row: T) => React.ReactNode;
  /** 默认可见 */
  visible?: boolean;
  align?: "left" | "right" | "center";
};

export type DrillExportStatus = "idle" | "exporting" | "queued" | "failed" | "ready";

export type DrillDetailTableProps<T = Record<string, unknown>> = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  columns: DrillDetailColumn<T>[];
  rows: T[];
  status?: QueryStatus;
  page?: number;
  pageSize?: number;
  total?: number;
  exportStatus?: DrillExportStatus;
  hiddenColumnIds?: string[];
  onPageChange?: (page: number) => void;
  onExport?: () => void;
  onToggleColumn?: (columnId: string) => void;
  onRetry?: () => void;
  onRequestAccess?: () => void;
  className?: string;
};

const exportLabel: Record<DrillExportStatus, string> = {
  idle: "导出 CSV",
  exporting: "导出中…",
  queued: "排队中…",
  failed: "导出失败",
  ready: "下载就绪",
};

/**
 * BI 下钻明细表 — 分页、导出、列显隐、权限错误与空态。
 * @see references/layout-patterns/bi-drill-down.md
 */
export function DrillDetailTable<T>({
  title = "明细数据",
  description,
  columns,
  rows,
  status = "success",
  page = 1,
  pageSize = 20,
  total,
  exportStatus = "idle",
  hiddenColumnIds = [],
  onPageChange,
  onExport,
  onToggleColumn,
  onRetry,
  onRequestAccess,
  className,
}: DrillDetailTableProps<T>) {
  const visibleColumns = columns.filter((c) => c.visible !== false && !hiddenColumnIds.includes(c.id));
  const totalPages = total != null ? Math.max(1, Math.ceil(total / pageSize)) : 1;
  const exportDisabled = exportStatus === "exporting" || exportStatus === "queued";

  const filterSlot = (
    <div className="flex flex-wrap items-center gap-2">
      {columns.length > 3 && onToggleColumn ? (
        <Button variant="outline" size="sm" type="button">
          列设置
        </Button>
      ) : null}
      {onExport ? (
        <Button
          variant="outline"
          size="sm"
          type="button"
          disabled={exportDisabled}
          onClick={onExport}
        >
          {exportLabel[exportStatus]}
        </Button>
      ) : null}
    </div>
  );

  const footer =
    status === "success" && total != null ? (
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-3 text-theme-sm text-gray-500">
        <span>
          共 {total} 条 · 第 {page} / {totalPages} 页
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPageChange?.(page - 1)}
          >
            上一页
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => onPageChange?.(page + 1)}
          >
            下一页
          </Button>
        </div>
      </div>
    ) : null;

  return (
    <DataTableCard
      title={title}
      description={description}
      status={status}
      filterSlot={filterSlot}
      footer={footer}
      queryProps={{
        emptyTitle: "当前筛选无明细数据",
        emptyDescription: "尝试放宽日期或区域筛选，或返回上一级图表查看汇总。",
        errorTitle: "明细加载失败",
        forbiddenTitle: "无权查看明细",
        forbiddenDescription: "您没有访问行级明细的权限，请联系数据管理员申请。",
        onRetry,
        onForbiddenAction: onRequestAccess,
        forbiddenActionLabel: "申请权限",
      }}
      className={cn(className)}
    >
      {status === "success" && visibleColumns.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              {visibleColumns.map((col) => (
                <TableHead
                  key={col.id}
                  className={cn(
                    col.align === "right" && "text-right",
                    col.align === "center" && "text-center",
                  )}
                >
                  {col.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row, rowIndex) => (
              <TableRow key={rowIndex}>
                {visibleColumns.map((col) => (
                  <TableCell
                    key={col.id}
                    className={cn(
                      col.align === "right" && "text-right tabular-nums",
                      col.align === "center" && "text-center",
                    )}
                  >
                    {col.accessor(row)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </DataTableCard>
  );
}
