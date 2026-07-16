import * as React from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  TableBody,
  TableCell,
  TableRow,
} from "@/components/ui/table";
import type { DataTableColumn, ExpandableConfig, RowSelectionConfig } from "@/components/ui/data-table";

type VirtualBodyProps<T> = {
  dataSource: T[];
  columns: DataTableColumn<T>[];
  rowSelection?: RowSelectionConfig;
  expandable?: ExpandableConfig<T>;
  expandedKeys: string[];
  extraColumnCount: number;
  virtual: { rowHeight: number; overscan?: number };
  renderCell: (
    column: DataTableColumn<T>,
    record: T,
    index: number,
  ) => React.ReactNode;
  toggleExpanded: (key: string) => void;
  toggleRowSelection: (key: string) => void;
};

export function DataTableVirtualBody<T>({
  dataSource,
  columns,
  rowSelection,
  expandable,
  expandedKeys,
  extraColumnCount,
  virtual,
  renderCell,
  toggleExpanded,
  toggleRowSelection,
}: VirtualBodyProps<T>) {
  const bodyRef = React.useRef<HTMLTableSectionElement>(null);

  const getScrollElement = React.useCallback(
    () =>
      bodyRef.current?.closest<HTMLElement>("[class*='overflow-auto']") ??
      bodyRef.current?.parentElement?.parentElement ??
      null,
    [],
  );

  const rowVirtualizer = useVirtualizer({
    count: dataSource.length,
    getScrollElement,
    estimateSize: () => virtual.rowHeight,
    overscan: virtual.overscan ?? 5,
  });

  const virtualRows = rowVirtualizer.getVirtualItems();
  const totalSize = rowVirtualizer.getTotalSize();
  const paddingTop = virtualRows.length > 0 ? virtualRows[0].start : 0;
  const paddingBottom =
    virtualRows.length > 0
      ? totalSize - virtualRows[virtualRows.length - 1].end
      : 0;

  return (
    <TableBody ref={bodyRef}>
      {paddingTop > 0 ? (
        <tr aria-hidden>
          <td colSpan={columns.length + extraColumnCount} style={{ height: paddingTop, padding: 0, border: 0 }} />
        </tr>
      ) : null}
      {virtualRows.map((virtualRow) => {
        const index = virtualRow.index;
        const record = dataSource[index];
        const rowKey = rowSelection?.getRowKey(record) ?? String(index);
        const isSelected = rowSelection?.selectedKeys.includes(rowKey) ?? false;
        const canExpand = expandable?.rowExpandable?.(record) ?? true;
        const isExpanded = expandedKeys.includes(rowKey);

        return (
          <React.Fragment key={rowKey}>
            <TableRow
              data-state={isSelected ? "selected" : undefined}
              style={{ height: virtual.rowHeight }}
            >
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
      })}
      {paddingBottom > 0 ? (
        <tr aria-hidden>
          <td colSpan={columns.length + extraColumnCount} style={{ height: paddingBottom, padding: 0, border: 0 }} />
        </tr>
      ) : null}
    </TableBody>
  );
}
