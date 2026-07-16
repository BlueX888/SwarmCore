import * as React from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ChevronRight, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import type { HierarchicalNode } from "@/components/ui/hierarchical-picker/types";
import type { useHierarchicalPicker } from "@/components/ui/hierarchical-picker/use-hierarchical-picker";
import type { DataTableColumn, RowSelectionConfig } from "@/components/ui/data-table";
import type { FlatTreeRow } from "@/lib/flatten-tree-rows";
import {
  TableBody,
  TableCell,
  TableRow,
} from "@/components/ui/table";

type Picker = ReturnType<typeof useHierarchicalPicker>;

export type TreeTableVirtualBodyProps<T extends HierarchicalNode> = {
  rows: FlatTreeRow<T>[];
  virtual: { rowHeight: number; overscan?: number };
  showCheckboxCol: boolean;
  showRowSelection: boolean;
  rowSelection?: RowSelectionConfig;
  checkedKeys: string[];
  dataColumns: DataTableColumn<T>[];
  treeCol?: DataTableColumn<T>;
  picker: Picker;
  rowKey: (node: T) => string;
  loadData?: (node: HierarchicalNode) => Promise<void>;
  getCellValue: (
    column: DataTableColumn<T>,
    node: T,
    index: number,
  ) => React.ReactNode;
};

export function TreeTableVirtualBody<T extends HierarchicalNode>({
  rows,
  virtual,
  showCheckboxCol,
  showRowSelection,
  rowSelection,
  checkedKeys,
  dataColumns,
  treeCol,
  picker,
  rowKey,
  loadData,
  getCellValue,
}: TreeTableVirtualBodyProps<T>) {
  const bodyRef = React.useRef<HTMLTableSectionElement>(null);

  const getScrollElement = React.useCallback(
    () =>
      bodyRef.current?.closest<HTMLElement>("[data-tree-table-scroll]") ??
      bodyRef.current?.parentElement?.parentElement ??
      null,
    [],
  );

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement,
    estimateSize: () => virtual.rowHeight,
    overscan: virtual.overscan ?? 5,
  });

  React.useEffect(() => {
    rowVirtualizer.measure();
  }, [rows.length, rowVirtualizer]);

  const virtualRows = rowVirtualizer.getVirtualItems();
  const totalSize = rowVirtualizer.getTotalSize();
  const paddingTop = virtualRows.length > 0 ? virtualRows[0].start : 0;
  const paddingBottom =
    virtualRows.length > 0
      ? totalSize - virtualRows[virtualRows.length - 1].end
      : 0;

  const colSpan =
    dataColumns.length + 1 + (showCheckboxCol ? 1 : 0) + (showRowSelection ? 1 : 0);

  return (
    <TableBody ref={bodyRef}>
      {paddingTop > 0 ? (
        <tr aria-hidden>
          <td colSpan={colSpan} style={{ height: paddingTop, padding: 0, border: 0 }} />
        </tr>
      ) : null}
      {virtualRows.map((virtualRow) => {
        const index = virtualRow.index;
        const { node, depth, hasChildren, isExpanded } = rows[index];
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
            style={{ height: virtual.rowHeight }}
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
              <TableCell key={column.key}>
                {getCellValue(column, node, index)}
              </TableCell>
            ))}
          </TableRow>
        );
      })}
      {paddingBottom > 0 ? (
        <tr aria-hidden>
          <td colSpan={colSpan} style={{ height: paddingBottom, padding: 0, border: 0 }} />
        </tr>
      ) : null}
    </TableBody>
  );
}
