import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { IconButton } from "@/components/ui/button";

export type ActionBarProps = {
  selectedCount: number;
  onClear: () => void;
  actions?: React.ReactNode;
  className?: string;
};

/**
 * 表格批量操作浮条 — selectedCount > 0 时自底部居中滑入。
 */
export function ActionBar({ selectedCount, onClear, actions, className }: ActionBarProps) {
  const open = selectedCount > 0;

  return (
    <div
      role="toolbar"
      aria-hidden={!open}
      data-state={open ? "open" : "closed"}
      className={cn(
        "fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3 shadow-theme-lg transition-all duration-300 ease-out dark:border-gray-800 dark:bg-gray-dark",
        open
          ? "pointer-events-auto translate-y-0 opacity-100"
          : "pointer-events-none translate-y-4 opacity-0",
        className,
      )}
    >
      <span className="text-theme-sm font-medium whitespace-nowrap text-gray-700 dark:text-gray-300">
        已选 {selectedCount} 项
      </span>

      <IconButton
        type="button"
        variant="ghost"
        size="xs"
        aria-label="清除选择"
        onClick={onClear}
      >
        <X className="size-4" />
      </IconButton>

      {actions ? (
        <>
          <span
            aria-hidden="true"
            className="h-5 w-px shrink-0 bg-gray-200 dark:bg-gray-700"
          />
          <div className="flex items-center gap-2">{actions}</div>
        </>
      ) : null}
    </div>
  );
}
