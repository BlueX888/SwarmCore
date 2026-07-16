import * as React from "react";
import { ChevronRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  collectExpandableIds,
  flattenTreeRows,
  type FlatTreeRow,
} from "@/lib/flatten-tree-rows";
import type { CheckStrategy, HierarchicalNode, LoadDataFn } from "@/components/ui/hierarchical-picker/types";
import { useHierarchicalPicker } from "@/components/ui/hierarchical-picker/use-hierarchical-picker";
import {
  type DataTableChangePayload,
  type DataTableColumn,
  type RowSelectionConfig,
  type TableFilters,
  type TablePagination,
  type TableSorter,
} from "@/components/ui/data-table";
import { DataTableColumnFilter } from "@/components/ui/data-table-column-filter";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  type TableSize,
  type TableVariant,
} from "@/components/ui/table";
import { ContentState } from "@/components/ui/content-state";

const TreeTableVirtualBody = React.lazy(() =>
  import("@/components/ui/tree-table-virtual-body").then((module) => ({
    default: module.TreeTableVirtualBody,
  })),
);

export type TreeTableVirtualConfig = {
  rowHeight?: number;
  overscan?: number;
};

export type TreeTableRowKey = string;

export type TreeTableProps<T extends HierarchicalNode = HierarchicalNode> = {
  dataSource: T[];
  columns: DataTableColumn<T>[];
  treeColumnTitle?: React.ReactNode;
  treeColumnKey?: string;
  rowKey?: (node: T) => TreeTableRowKey;

  expandedKeys?: string[];
  defaultExpandedKeys?: string[];
  onExpandedKeysChange?: (keys: string[]) => void;
  defaultExpandAll?: boolean;
  loadData?: LoadDataFn;

  checkable?: boolean;
  checkedKeys?: string[];
  defaultCheckedKeys?: string[];
  onCheckedKeysChange?: (keys: string[]) => void;
  checkStrategy?: CheckStrategy;

  size?: TableSize;
  variant?: TableVariant;
  stickyHeader?: boolean;
  pagination?: TablePagination;
  onChange?: (payload: DataTableChangePayload) => void;
  rowSelection?: RowSelectionConfig;
  summary?: React.ReactNode;
  loading?: boolean;
  emptyMessage?: React.ReactNode;
  className?: string;
  /** 扁平行虚拟滚动（peer: `@tanstack/react-virtual`） */
  virtual?: boolean | TreeTableVirtualConfig;
  scroll?: { y: number };
};

function getCellValue<T extends HierarchicalNode>(
  column: DataTableColumn<T>,
  node: T,
  index: number,
): React.ReactNode {
  if (column.render) {
    return column.render(
      column.dataIndex ? node[column.dataIndex as keyof T] : undefined,
      node,
      index,
    );
  }
  if (column.dataIndex) {
    const value = node[column.dataIndex as keyof T];
    return value == null ? "—" : String(value);
  }
  return "—";
}

function rowMatchesFilters<T extends HierarchicalNode>(
  node: T,
  columns: DataTableColumn<T>[],
  filters: TableFilters,
): boolean {
  for (const [key, filterValue] of Object.entries(filters)) {
    const column = columns.find((c) => c.key === key);
    if (!column?.dataIndex) continue;
    const raw = node[column.dataIndex as keyof T];
    const cellValue = raw == null ? "" : String(raw);
    if (column.filter?.type === "text") {
      if (!cellValue.toLowerCase().includes(String(filterValue).toLowerCase())) {
        return false;
      }
    } else if (cellValue !== String(filterValue)) {
      return false;
    }
  }
  return true;
}

function resolveVirtualConfig(
  virtual: TreeTableProps["virtual"],
): TreeTableVirtualConfig | null {
  if (!virtual) return null;
  if (virtual === true) return { rowHeight: 48, overscan: 5 };
  return { rowHeight: virtual.rowHeight ?? 48, overscan: virtual.overscan ?? 5 };
}

export function TreeTable<T extends HierarchicalNode = HierarchicalNode>({
  dataSource,
  columns,
  treeColumnTitle = "名称",
  treeColumnKey = "__tree__",
  rowKey = (node) => node.id,
  expandedKeys: expandedKeysProp,
  defaultExpandedKeys,
  onExpandedKeysChange,
  defaultExpandAll = false,
  loadData,
  checkable = false,
  checkedKeys: checkedKeysProp,
  defaultCheckedKeys = [],
  onCheckedKeysChange,
  checkStrategy = "child",
  size,
  variant,
  stickyHeader,
  pagination,
  onChange,
  rowSelection,
  summary,
  loading = false,
  emptyMessage = "暂无数据",
  className,
  virtual,
  scroll,
}: TreeTableProps<T>) {
  const [internalChecked, setInternalChecked] = React.useState<string[]>(defaultCheckedKeys);
  const checkedKeys = checkedKeysProp ?? internalChecked;
  const setCheckedKeys = (keys: string[]) => {
    if (checkedKeysProp == null) setInternalChecked(keys);
    onCheckedKeysChange?.(keys);
  };

  const initialExpanded = React.useMemo(() => {
    if (defaultExpandedKeys?.length) return defaultExpandedKeys;
    if (defaultExpandAll) return collectExpandableIds(dataSource);
    return [];
  }, [defaultExpandedKeys, defaultExpandAll, dataSource]);

  const [internalExpanded, setInternalExpanded] = React.useState<string[]>(initialExpanded);
  const expandedKeys = expandedKeysProp ?? internalExpanded;
  const setExpandedKeys = (keys: string[]) => {
    if (expandedKeysProp == null) setInternalExpanded(keys);
    onExpandedKeysChange?.(keys);
  };

  const picker = useHierarchicalPicker({
    nodes: dataSource,
    expandedKeys,
    onExpandedKeysChange: setExpandedKeys,
    checkedKeys: checkable && !rowSelection ? checkedKeys : [],
    onCheckedKeysChange: checkable && !rowSelection ? setCheckedKeys : undefined,
    checkStrategy,
    loadData,
  });

  const flatRows = React.useMemo(
    () => flattenTreeRows(picker.nodes as T[], new Set(picker.expandedKeys)),
    [picker.nodes, picker.expandedKeys],
  );

  const [sorter, setSorter] = React.useState<TableSorter>(null);

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

  const filteredRows = React.useMemo(() => {
    if (Object.keys(filters).length === 0) return flatRows;
    return flatRows.filter(({ node }) => rowMatchesFilters(node, columns, filters));
  }, [flatRows, columns, filters]);

  const sortedRows = React.useMemo(() => {
    if (!sorter) return filteredRows;
    const { field, order } = sorter;
    const col = columns.find((c) => c.key === field);
    if (!col) return filteredRows;
    const factor = order === "asc" ? 1 : -1;
    return [...filteredRows].sort((a, b) => {
      const av = col.dataIndex ? String(a.node[col.dataIndex as keyof T] ?? "") : "";
      const bv = col.dataIndex ? String(b.node[col.dataIndex as keyof T] ?? "") : "";
      return av.localeCompare(bv, "zh-CN") * factor;
    });
  }, [filteredRows, sorter, columns]);

  const pagedRows = React.useMemo(() => {
    if (!pagination) return sortedRows;
    const start = (pagination.current - 1) * pagination.pageSize;
    return sortedRows.slice(start, start + pagination.pageSize);
  }, [sortedRows, pagination]);

  const resolvedPagination = pagination ?? { current: 1, pageSize: 10, total: sortedRows.length };

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

  const handleSort = (key: string) => {
    const next: TableSorter =
      sorter?.field === key
        ? sorter.order === "asc"
          ? { field: key, order: "desc" }
          : sorter.order === "desc"
            ? null
            : { field: key, order: "asc" }
        : { field: key, order: "asc" };
    setSorter(next);
    emitChange({ sorter: next });
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

  const virtualConfig = resolveVirtualConfig(virtual);
  const displayRows = pagedRows;
  const showCheckboxCol = checkable && !rowSelection;
  const showRowSelection = Boolean(rowSelection);
  const extraCols = (showCheckboxCol ? 1 : 0) + (showRowSelection ? 1 : 0);
  const dataColumns = columns.filter((c) => c.key !== treeColumnKey);
  const treeCol = columns.find((c) => c.key === treeColumnKey);

  const renderBodyRow = (
    { node, depth, hasChildren, isExpanded }: FlatTreeRow<T>,
    index: number,
  ) => {
    const key = rowKey(node);
    const isLoading = picker.loadingKeys.has(node.id);
    const isChecked = rowSelection
      ? rowSelection.selectedKeys.includes(key)
      : checkedKeys.includes(key);

    return (
      <TableRow
        key={key}
        data-state={isChecked ? "selected" : undefined}
        className={cn(isChecked && "bg-brand-50/50 dark:bg-brand-500/10")}
      >
        {showCheckboxCol ? (
          <TableCell className="w-11 px-3">
            <Checkbox
              checked={checkedKeys.includes(key)}
              disabled={node.disabled}
              onCheckedChange={() => picker.toggleCheck(node)}
              aria-label={`选择 ${typeof node.label === "string" ? node.label : key}`}
            />
          </TableCell>
        ) : null}
        {showRowSelection && rowSelection ? (
          <TableCell className="w-11 px-3">
            <Checkbox
              checked={rowSelection.selectedKeys.includes(key)}
              onCheckedChange={() => {
                const selected = rowSelection.selectedKeys.includes(key);
                rowSelection.onChange(
                  selected
                    ? rowSelection.selectedKeys.filter((k) => k !== key)
                    : [...rowSelection.selectedKeys, key],
                );
              }}
              aria-label={`选择行 ${key}`}
            />
          </TableCell>
        ) : null}
        <TableCell className="min-w-[200px]">
          <div
            className="flex items-center gap-1"
            style={{ paddingInlineStart: `${depth * 1.25}rem` }}
            role="treeitem"
            aria-level={depth + 1}
            aria-expanded={hasChildren ? isExpanded : undefined}
          >
            {hasChildren || (!node.isLeaf && loadData) ? (
              <Button
                type="button"
                variant="ghost"
                size="xs"
                className="size-8 shrink-0 p-0"
                disabled={node.disabled || isLoading}
                onClick={() => picker.toggleExpand(node)}
                aria-expanded={isExpanded}
                aria-label={isExpanded ? "收起" : "展开"}
              >
                {isLoading ? (
                  <Loader2 className="size-4 animate-spin text-gray-400" />
                ) : (
                  <ChevronRight
                    className={cn(
                      "size-4 text-gray-400 transition-transform",
                      isExpanded && "rotate-90",
                    )}
                  />
                )}
              </Button>
            ) : (
              <span className="inline-block size-8 shrink-0" aria-hidden />
            )}
            <span className="min-w-0 truncate text-gray-800 dark:text-white/90">
              {treeCol ? getCellValue(treeCol, node, index) : node.label}
            </span>
          </div>
        </TableCell>
        {dataColumns.map((column) => (
          <TableCell key={column.key}>{getCellValue(column, node, index)}</TableCell>
        ))}
      </TableRow>
    );
  };

  if (loading) {
    return (
      <div className={cn("rounded-xl border border-gray-200 p-8 dark:border-gray-800", className)} aria-busy="true">
        <ContentState variant="loading" title="加载中" />
      </div>
    );
  }

  if (!dataSource.length) {
    return (
      <div className={cn("rounded-xl border border-gray-200 p-8 dark:border-gray-800", className)}>
        <ContentState variant="empty" title={emptyMessage} />
      </div>
    );
  }

  const scrollStyle = scroll?.y ? { maxHeight: scroll.y, overflow: "auto" as const } : undefined;

  return (
    <div data-tree-table-scroll={virtualConfig ? "" : undefined} style={scrollStyle}>
      <Table
        size={size}
        variant={variant}
        stickyHeader={stickyHeader && !virtualConfig}
        className={className}
        wrapperClassName={virtualConfig || scroll?.y ? "!overflow-visible" : undefined}
      >
        <TableHeader>
          <TableRow>
            {showCheckboxCol ? (
              <TableHead className="w-11 px-3">
                <span className="sr-only">选择</span>
              </TableHead>
            ) : null}
            {showRowSelection ? (
              <TableHead className="w-11 px-3">
                <span className="sr-only">选择</span>
              </TableHead>
            ) : null}
            <TableHead className="min-w-[200px]">{treeColumnTitle}</TableHead>
            {dataColumns.map((column) => (
              <TableHead key={column.key}>
                <div className="flex items-center gap-1">
                  {column.sortable ? (
                    <button
                      type="button"
                      className="font-medium text-gray-500 hover:text-brand-500 dark:text-gray-400"
                      onClick={() => handleSort(column.key)}
                    >
                      {column.title}
                    </button>
                  ) : (
                    <span>{column.title}</span>
                  )}
                  {column.filter ? (
                    <DataTableColumnFilter
                      config={column.filter}
                      value={column.filteredValue}
                      columnTitle={column.title}
                      onApply={(value) => handleFilterApply(column.key, value)}
                    />
                  ) : null}
                </div>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        {virtualConfig ? (
          <React.Suspense
            fallback={
              <TableBody>
                <TableRow>
                  <TableCell colSpan={dataColumns.length + 1 + extraCols}>
                    <ContentState variant="loading" title="加载虚拟列表…" />
                  </TableCell>
                </TableRow>
              </TableBody>
            }
          >
            <TreeTableVirtualBody
              rows={displayRows}
              virtual={{
                rowHeight: virtualConfig.rowHeight ?? 48,
                overscan: virtualConfig.overscan,
              }}
              showCheckboxCol={showCheckboxCol}
              showRowSelection={showRowSelection}
              rowSelection={rowSelection}
              checkedKeys={checkedKeys}
              dataColumns={dataColumns}
              treeCol={treeCol}
              picker={picker}
              rowKey={rowKey}
              loadData={loadData}
              getCellValue={getCellValue}
            />
          </React.Suspense>
        ) : (
          <TableBody>
            {displayRows.map((row, index) => renderBodyRow(row, index))}
          </TableBody>
        )}
        {summary ? (
          <tfoot>
            <tr>
              <td colSpan={dataColumns.length + 1 + extraCols}>{summary}</td>
            </tr>
          </tfoot>
        ) : null}
      </Table>
    </div>
  );
}

export type { DataTableColumn, DataTableChangePayload, TablePagination };
