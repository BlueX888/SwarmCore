import * as React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  DataTableColumnFilter,
  type ColumnFilterConfig,
} from "@/components/ui/data-table-column-filter";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
  type TableSize,
  type TableVariant,
} from "@/components/ui/table";

export type { ColumnFilterConfig };

export type TableSorter = { field: string; order: "asc" | "desc" } | null;
export type TablePagination = { current: number; pageSize: number; total?: number };
export type TableFilters = Record<string, unknown>;

export type DataTableChangePayload = {
  pagination: TablePagination;
  filters: TableFilters;
  sorter: TableSorter;
};

export type RowSelectionConfig = {
  type: "checkbox" | "radio";
  selectedKeys: string[];
  onChange: (keys: string[]) => void;
  getRowKey: (record: unknown) => string;
};

export type ExpandableConfig<T> = {
  expandedRowRender: (record: T) => React.ReactNode;
  rowExpandable?: (record: T) => boolean;
  expandedKeys?: string[];
  onExpandedKeysChange?: (keys: string[]) => void;
};

export type DataTableColumn<T> = {
  key: string;
  title: React.ReactNode;
  dataIndex?: keyof T & string;
  render?: (value: unknown, record: T, index: number) => React.ReactNode;
  sortable?: boolean;
  filter?: ColumnFilterConfig;
  filteredValue?: unknown;
};

export type DataTableVirtualConfig = {
  rowHeight: number;
  overscan?: number;
};

export type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  dataSource: T[];
  size?: TableSize;
  variant?: TableVariant;
  stickyHeader?: boolean;
  rowSelection?: RowSelectionConfig;
  expandable?: ExpandableConfig<T>;
  pagination?: TablePagination;
  onChange?: (payload: DataTableChangePayload) => void;
  summary?: React.ReactNode;
  className?: string;
  /** 启用行虚拟滚动（peer: `@tanstack/react-virtual`）。与 `stickyHeader` 同开时表头 sticky 可能降级。 */
  virtual?: DataTableVirtualConfig;
};

const DataTableVirtualBody = React.lazy(() =>
  import("@/components/ui/data-table-virtual-body").then((module) => ({
    default: module.DataTableVirtualBody,
  })),
);

const DEFAULT_PAGINATION: TablePagination = { current: 1, pageSize: 10 };

function getCellValue<T>(column: DataTableColumn<T>, record: T): unknown {
  if (column.dataIndex != null) {
    return record[column.dataIndex];
  }
  return undefined;
}

function renderCell<T>(
  column: DataTableColumn<T>,
  record: T,
  index: number,
): React.ReactNode {
  const value = getCellValue(column, record);
  if (column.render) {
    return column.render(value, record, index);
  }
  if (value == null) {
    return null;
  }
  return String(value);
}

function SortIndicator({ order }: { order: "asc" | "desc" | null }) {
  if (order === "asc") {
    return <ChevronUp className="size-3.5 text-brand-500" aria-hidden />;
  }
  if (order === "desc") {
    return <ChevronDown className="size-3.5 text-brand-500" aria-hidden />;
  }
  return (
    <span className="inline-flex flex-col opacity-40" aria-hidden>
      <ChevronUp className="-mb-1 size-3" />
      <ChevronDown className="size-3" />
    </span>
  );
}

export function TableSummary({ children }: { children: React.ReactNode }) {
  return (
    <TableFooter>
      <TableRow>{children}</TableRow>
    </TableFooter>
  );
}

export function DataTable<T>({
  columns,
  dataSource,
  size,
  variant,
  stickyHeader,
  rowSelection,
  expandable,
  pagination,
  onChange,
  summary,
  className,
  virtual,
}: DataTableProps<T>) {
  const [sorter, setSorter] = React.useState<TableSorter>(null);
  const [internalExpandedKeys, setInternalExpandedKeys] = React.useState<string[]>([]);
  const [internalPagination, setInternalPagination] =
    React.useState<TablePagination>(DEFAULT_PAGINATION);

  const resolvedPagination = pagination ?? internalPagination;

  const filters = React.useMemo(() => {
    const next: TableFilters = {};
    for (const column of columns) {
      if (
        column.filteredValue !== undefined &&
        column.filteredValue !== null &&
        column.filteredValue !== ""
      ) {
        next[column.key] = column.filteredValue;
      }
    }
    return next;
  }, [columns]);

  const virtualFilterWarnedRef = React.useRef(false);

  React.useEffect(() => {
    if (
      virtual &&
      columns.some((column) => column.filter) &&
      !virtualFilterWarnedRef.current
    ) {
      console.warn(
        "[DataTable] 虚拟滚动模式下列头 filter 已禁用，请改用工具栏筛选。",
      );
      virtualFilterWarnedRef.current = true;
    }
  }, [virtual, columns]);

  const expandedKeys = expandable?.expandedKeys ?? internalExpandedKeys;

  React.useEffect(() => {
    if (pagination) {
      setInternalPagination(pagination);
    }
  }, [pagination]);

  const emitChange = React.useCallback(
    (next: Partial<DataTableChangePayload>) => {
      onChange?.({
        pagination: next.pagination ?? resolvedPagination,
        filters: next.filters ?? filters,
        sorter: next.sorter !== undefined ? next.sorter : sorter,
      });
    },
    [filters, onChange, resolvedPagination, sorter],
  );

  const handleSort = (field: string) => {
    let nextSorter: TableSorter;
    if (sorter?.field !== field) {
      nextSorter = { field, order: "asc" };
    } else if (sorter.order === "asc") {
      nextSorter = { field, order: "desc" };
    } else {
      nextSorter = null;
    }
    setSorter(nextSorter);
    emitChange({ sorter: nextSorter });
  };

  const handleFilterApply = (field: string, value: unknown) => {
    const nextFilters = { ...filters };
    if (value === undefined || value === null || value === "") {
      delete nextFilters[field];
    } else {
      nextFilters[field] = value;
    }
    emitChange({ filters: nextFilters });
  };

  const pageRowKeys = React.useMemo(
    () => (rowSelection ? dataSource.map((record) => rowSelection.getRowKey(record)) : []),
    [dataSource, rowSelection],
  );

  const allPageSelected =
    pageRowKeys.length > 0 &&
    pageRowKeys.every((key) => rowSelection?.selectedKeys.includes(key));
  const somePageSelected =
    !allPageSelected &&
    pageRowKeys.some((key) => rowSelection?.selectedKeys.includes(key));

  const headerCheckboxState: boolean | "indeterminate" = allPageSelected
    ? true
    : somePageSelected
      ? "indeterminate"
      : false;

  const toggleSelectAll = () => {
    if (!rowSelection || rowSelection.type !== "checkbox") {
      return;
    }
    if (allPageSelected) {
      const remaining = rowSelection.selectedKeys.filter(
        (key) => !pageRowKeys.includes(key),
      );
      rowSelection.onChange(remaining);
      return;
    }
    const merged = [...new Set([...rowSelection.selectedKeys, ...pageRowKeys])];
    rowSelection.onChange(merged);
  };

  const toggleRowSelection = (key: string) => {
    if (!rowSelection) {
      return;
    }
    if (rowSelection.type === "radio") {
      rowSelection.onChange([key]);
      return;
    }
    const selected = rowSelection.selectedKeys.includes(key);
    rowSelection.onChange(
      selected
        ? rowSelection.selectedKeys.filter((k) => k !== key)
        : [...rowSelection.selectedKeys, key],
    );
  };

  const toggleExpanded = (key: string) => {
    if (!expandable) {
      return;
    }
    const next = expandedKeys.includes(key)
      ? expandedKeys.filter((k) => k !== key)
      : [...expandedKeys, key];
    if (expandable.expandedKeys == null) {
      setInternalExpandedKeys(next);
    }
    expandable.onExpandedKeysChange?.(next);
  };

  const extraColumnCount =
    (expandable ? 1 : 0) + (rowSelection ? 1 : 0);

  const useVirtualBody = Boolean(virtual) && rowSelection?.type !== "radio";

  return (
    <Table
      size={size}
      variant={variant}
      stickyHeader={stickyHeader && !virtual}
      className={className}
      wrapperClassName={virtual ? "max-h-[min(70vh,640px)]" : undefined}
    >
      <TableHeader>
        <TableRow>
          {expandable ? (
            <TableHead className="w-10 px-3">
              <span className="sr-only">展开</span>
            </TableHead>
          ) : null}
          {rowSelection?.type === "checkbox" ? (
            <TableHead className="w-12 px-3">
              <Checkbox
                checked={allPageSelected}
                indeterminate={headerCheckboxState === "indeterminate"}
                onCheckedChange={toggleSelectAll}
                aria-label="全选当前页"
              />
            </TableHead>
          ) : rowSelection?.type === "radio" ? (
            <TableHead className="w-12 px-3">
              <span className="sr-only">选择</span>
            </TableHead>
          ) : null}
          {columns.map((column) => {
            const activeOrder =
              sorter?.field === column.key ? sorter.order : null;
            const showFilter = Boolean(column.filter) && !virtual;

            return (
              <TableHead key={column.key}>
                <div className="inline-flex items-center gap-0.5">
                  {column.sortable ? (
                    <button
                      type="button"
                      className="inline-flex items-center gap-1.5 text-left font-medium text-gray-500 transition-colors hover:text-brand-500 dark:text-gray-400 dark:hover:text-brand-400"
                      onClick={() => handleSort(column.key)}
                      aria-label={`按${String(column.title)}排序${
                        activeOrder === "asc"
                          ? "，当前升序"
                          : activeOrder === "desc"
                            ? "，当前降序"
                            : ""
                      }`}
                    >
                      {column.title}
                      <SortIndicator order={activeOrder} />
                    </button>
                  ) : (
                    <span className="font-medium text-gray-500 dark:text-gray-400">
                      {column.title}
                    </span>
                  )}
                  {showFilter && column.filter ? (
                    <DataTableColumnFilter
                      config={column.filter}
                      value={column.filteredValue}
                      columnTitle={column.title}
                      onApply={(value) => handleFilterApply(column.key, value)}
                    />
                  ) : null}
                </div>
              </TableHead>
            );
          })}
        </TableRow>
      </TableHeader>

      {useVirtualBody && virtual ? (
        <React.Suspense
          fallback={
            <TableBody>
              <TableRow>
                <TableCell colSpan={columns.length + extraColumnCount} className="h-24 text-center text-gray-500">
                  加载虚拟列表…
                </TableCell>
              </TableRow>
            </TableBody>
          }
        >
          <DataTableVirtualBody
            dataSource={dataSource}
            columns={columns}
            rowSelection={rowSelection}
            expandable={expandable}
            expandedKeys={expandedKeys}
            extraColumnCount={extraColumnCount}
            virtual={virtual}
            renderCell={renderCell}
            toggleExpanded={toggleExpanded}
            toggleRowSelection={toggleRowSelection}
          />
        </React.Suspense>
      ) : (
      <TableBody>
        {rowSelection?.type === "radio" ? (
          <RadioGroup
            value={rowSelection.selectedKeys[0] ?? ""}
            onValueChange={(value) => rowSelection.onChange([value])}
            className="contents"
          >
            {dataSource.map((record, index) => {
              const rowKey = rowSelection.getRowKey(record);
              const isSelected = rowSelection.selectedKeys.includes(rowKey);
              const canExpand = expandable?.rowExpandable?.(record) ?? true;
              const isExpanded = expandedKeys.includes(rowKey);

              return (
                <React.Fragment key={rowKey}>
                  <TableRow data-state={isSelected ? "selected" : undefined}>
                    {expandable ? (
                      <TableCell className="w-10 px-3">
                        {canExpand ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="xs"
                            className="size-8 p-0 text-gray-500 hover:text-brand-500"
                            onClick={() => toggleExpanded(rowKey)}
                            aria-expanded={isExpanded}
                            aria-label={isExpanded ? "收起行" : "展开行"}
                          >
                            <ChevronDown
                              className={cn(
                                "size-4 transition-transform duration-200",
                                isExpanded && "rotate-180",
                              )}
                            />
                          </Button>
                        ) : null}
                      </TableCell>
                    ) : null}
                    <TableCell className="w-12 px-3">
                      <RadioGroupItem
                        value={rowKey}
                        aria-label={`选择第 ${index + 1} 行`}
                      />
                    </TableCell>
                    {columns.map((column) => (
                      <TableCell key={column.key}>
                        {renderCell(column, record, index)}
                      </TableCell>
                    ))}
                  </TableRow>
                  {expandable && isExpanded && canExpand ? (
                    <TableRow className="bg-gray-50/80 hover:bg-gray-50/80 dark:bg-white/[0.02] dark:hover:bg-white/[0.02]">
                      <TableCell colSpan={columns.length + extraColumnCount}>
                        {expandable.expandedRowRender(record)}
                      </TableCell>
                    </TableRow>
                  ) : null}
                </React.Fragment>
              );
            })}
          </RadioGroup>
        ) : (
          dataSource.map((record, index) => {
            const rowKey = rowSelection?.getRowKey(record) ?? String(index);
            const isSelected = rowSelection?.selectedKeys.includes(rowKey) ?? false;
            const canExpand = expandable?.rowExpandable?.(record) ?? true;
            const isExpanded = expandedKeys.includes(rowKey);

            return (
              <React.Fragment key={rowKey}>
                <TableRow data-state={isSelected ? "selected" : undefined}>
                  {expandable ? (
                    <TableCell className="w-10 px-3">
                      {canExpand ? (
                        <Button
                          type="button"
                          variant="ghost"
                          size="xs"
                          className="size-8 p-0 text-gray-500 hover:text-brand-500"
                          onClick={() => toggleExpanded(rowKey)}
                          aria-expanded={isExpanded}
                          aria-label={isExpanded ? "收起行" : "展开行"}
                        >
                          <ChevronDown
                            className={cn(
                              "size-4 transition-transform duration-200",
                              isExpanded && "rotate-180",
                            )}
                          />
                        </Button>
                      ) : null}
                    </TableCell>
                  ) : null}
                  {rowSelection?.type === "checkbox" ? (
                    <TableCell className="w-12 px-3">
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => toggleRowSelection(rowKey)}
                        aria-label={`选择第 ${index + 1} 行`}
                      />
                    </TableCell>
                  ) : null}
                  {columns.map((column) => (
                    <TableCell key={column.key}>
                      {renderCell(column, record, index)}
                    </TableCell>
                  ))}
                </TableRow>
                {expandable && isExpanded && canExpand ? (
                  <TableRow className="bg-gray-50/80 hover:bg-gray-50/80 dark:bg-white/[0.02] dark:hover:bg-white/[0.02]">
                    <TableCell colSpan={columns.length + extraColumnCount}>
                      {expandable.expandedRowRender(record)}
                    </TableCell>
                  </TableRow>
                ) : null}
              </React.Fragment>
            );
          })
        )}
      </TableBody>
      )}

      {summary}
    </Table>
  );
}
