import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  CardAction,
} from "@/components/ui/card";
import {
  DataTable,
  type DataTableChangePayload,
  type DataTableColumn,
  type ExpandableConfig,
  type RowSelectionConfig,
  type TablePagination,
} from "@/components/ui/data-table";
import { Input } from "@/components/ui/input";
import {
  PaginationBar,
} from "@/components/ui/pagination-bar";
import { QueryShell, type QueryShellProps, type QueryStatus } from "@/components/ui/query-shell";
import type { TableSize, TableVariant } from "@/components/ui/table";

export type DataTableCardProps<T = unknown> = {
  title: React.ReactNode;
  description?: React.ReactNode;
  status?: QueryStatus;
  queryProps?: Omit<QueryShellProps, "status" | "children" | "className">;
  toolbar?: React.ReactNode;
  filterSlot?: React.ReactNode;
  actions?: React.ReactNode;
  bulkActions?: React.ReactNode;
  selectedCount?: number;
  onClearSelection?: () => void;
  children?: React.ReactNode;
  footer?: React.ReactNode;
  dense?: boolean;
  className?: string;
  flush?: boolean;
  columns?: DataTableColumn<T>[];
  dataSource?: T[];
  size?: TableSize;
  variant?: TableVariant;
  stickyHeader?: boolean;
  rowSelection?: RowSelectionConfig;
  expandable?: ExpandableConfig<T>;
  pagination?: TablePagination;
  onTableChange?: (payload: DataTableChangePayload) => void;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  pageSizeOptions?: number[];
  summary?: React.ReactNode;
};

function buildPaginationFooter(
  pagination: TablePagination,
  onTableChange: ((payload: DataTableChangePayload) => void) | undefined,
  showSizeChanger: boolean,
  showQuickJumper: boolean,
  pageSizeOptions: number[],
) {
  const total = pagination.total ?? pagination.pageSize;

  return (
    <PaginationBar
      current={pagination.current}
      pageSize={pagination.pageSize}
      total={total}
      showSizeChanger={showSizeChanger}
      showQuickJumper={showQuickJumper}
      pageSizeOptions={pageSizeOptions}
      onChange={(page, pageSize) => {
        onTableChange?.({
          pagination: { ...pagination, current: page, pageSize },
          filters: {},
          sorter: null,
        });
      }}
    />
  );
}

/**
 * DataTableCard — toolbar + filter + bulk action + flush table + pagination.
 * Aligns with gateway-visual DataTableCard rules (flush header, no double border).
 */
export function DataTableCard<T = unknown>({
  title,
  description,
  status = "success",
  queryProps,
  toolbar,
  filterSlot,
  actions,
  bulkActions,
  selectedCount: selectedCountProp,
  onClearSelection,
  children,
  footer,
  dense = false,
  className,
  flush = true,
  columns,
  dataSource,
  size,
  variant,
  stickyHeader,
  rowSelection,
  expandable,
  pagination,
  onTableChange,
  showSizeChanger = false,
  showQuickJumper = false,
  pageSizeOptions = [10, 20, 50, 100],
  summary,
}: DataTableCardProps<T>) {
  const selectedCount = selectedCountProp ?? rowSelection?.selectedKeys.length ?? 0;
  const hasSelection = selectedCount > 0;
  const usesBuiltInTable = columns != null && dataSource != null;

  const tableNode = usesBuiltInTable ? (
    <DataTable
      columns={columns}
      dataSource={dataSource}
      size={size}
      variant={variant}
      stickyHeader={stickyHeader}
      rowSelection={rowSelection}
      expandable={expandable}
      pagination={pagination}
      onChange={onTableChange}
      summary={summary}
    />
  ) : (
    children
  );

  const resolvedFooter =
    footer ??
    (pagination
      ? buildPaginationFooter(pagination, onTableChange, showSizeChanger, showQuickJumper, pageSizeOptions)
      : null);

  const handleClearSelection = () => {
    if (onClearSelection) {
      onClearSelection();
      return;
    }
    rowSelection?.onChange([]);
  };

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader>
        <div className="min-w-0 flex-1">
          <CardTitle>{title}</CardTitle>
          {description ? <CardDescription>{description}</CardDescription> : null}
        </div>
        {actions ? <CardAction>{actions}</CardAction> : null}
      </CardHeader>

      {(toolbar || filterSlot) && (
        <div className="flex flex-col gap-3 border-b border-gray-100 px-6 pb-4 dark:border-white/[0.05] sm:flex-row sm:items-center sm:justify-between">
          {toolbar ?? (
            <Input
              type="search"
              placeholder="搜索..."
              className="max-w-xs"
              aria-label="搜索表格"
            />
          )}
          {filterSlot ?? (
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm">
                筛选
              </Button>
              <Button variant="outline" size="sm">
                导出
              </Button>
            </div>
          )}
        </div>
      )}

      {hasSelection && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-brand-500/20 bg-brand-50 px-6 py-3 dark:bg-brand-500/10">
          <div className="flex items-center gap-3 text-theme-sm text-gray-700 dark:text-gray-300">
            <Checkbox checked aria-label={`${selectedCount} 行已选择`} />
            <span>
              <strong>{selectedCount}</strong> 项已选
            </span>
            {onClearSelection || rowSelection ? (
              <button
                type="button"
                onClick={handleClearSelection}
                className="text-brand-500 hover:text-brand-600"
              >
                清空
              </button>
            ) : null}
          </div>
          {bulkActions}
        </div>
      )}

      <CardContent className={cn(flush && "p-0 pt-0", dense && "text-theme-xs")}>
        <QueryShell status={status} minHeight={200} {...queryProps}>
          <div
            className={cn(
              flush && "[&_table]:rounded-none [&_table]:border-0",
              dense && "[&_th]:px-4 [&_th]:py-2 [&_td]:px-4 [&_td]:py-2.5",
            )}
          >
            {tableNode}
          </div>
        </QueryShell>
      </CardContent>

      {resolvedFooter ? (
        <CardFooter className="justify-between gap-4">{resolvedFooter}</CardFooter>
      ) : null}
    </Card>
  );
}
