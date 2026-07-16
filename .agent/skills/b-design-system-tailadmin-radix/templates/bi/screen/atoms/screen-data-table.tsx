import * as React from "react";

import { cn } from "../lib/cn";

export type ScreenDataTableProps = {
  columns: { key: string; title: string; width?: string }[];
  rows: Record<string, React.ReactNode>[];
  maxHeight?: number;
  striped?: boolean;
  variant?: "dark" | "light";
};

export function ScreenDataTable({
  columns,
  rows,
  maxHeight = 220,
  striped = true,
  variant = "dark",
}: ScreenDataTableProps) {
  const isDark = variant === "dark";

  return (
    <div
      className={cn("overflow-auto rounded-md border", isDark ? "border-white/10" : "border-slate-200")}
      style={{ maxHeight }}
      data-screen-data-table
    >
      <table className="w-full min-w-full text-left text-xs">
        <thead className={cn("sticky top-0 z-10", isDark ? "bg-white/5" : "bg-slate-50")}>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={cn(
                  "px-3 py-2 font-medium",
                  isDark ? "text-white/70" : "text-slate-600",
                )}
                style={column.width ? { width: column.width } : undefined}
              >
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={index}
              className={cn(
                "border-t",
                isDark ? "border-white/10" : "border-slate-100",
                striped && index % 2 === 1 && (isDark ? "bg-white/[0.02]" : "bg-slate-50/80"),
              )}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn(
                    "px-3 py-2",
                    column.key === "input" && "font-mono text-[11px]",
                    isDark ? "text-white/85" : "text-slate-700",
                  )}
                >
                  {row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
