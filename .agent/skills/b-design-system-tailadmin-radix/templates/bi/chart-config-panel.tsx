import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export type EncodingSlot = "x" | "y" | "color" | "size" | "filter" | "sort" | "limit";

export type EncodingValue = {
  slot: EncodingSlot;
  fieldName?: string;
  fieldType?: string;
};

export type ChartConfigPanelProps = {
  encodings: EncodingValue[];
  onDrop?: (slot: EncodingSlot, fieldName: string) => void;
  onClear?: (slot: EncodingSlot) => void;
  className?: string;
};

const slotLabels: Record<EncodingSlot, string> = {
  x: "X 轴",
  y: "Y 轴",
  color: "颜色",
  size: "尺寸",
  filter: "筛选",
  sort: "排序",
  limit: "限制",
};

/**
 * Chart encoding slots — X/Y/Color/Size/Filter/Sort/Limit.
 * @see references/layout-patterns/bi-chart-builder.md
 */
export function ChartConfigPanel({ encodings, onClear, className }: ChartConfigPanelProps) {
  const bySlot = React.useMemo(() => {
    const map = new Map<EncodingSlot, EncodingValue>();
    for (const e of encodings) map.set(e.slot, e);
    return map;
  }, [encodings]);

  return (
    <div className={cn("flex flex-col border-l border-gray-200 dark:border-gray-800", className)}>
      <div className="border-b border-gray-200 px-4 py-3 dark:border-gray-800">
        <h3 className="text-theme-sm font-semibold text-gray-900 dark:text-white/90">图表编码</h3>
      </div>
      <div className="space-y-3 p-4">
        {(Object.keys(slotLabels) as EncodingSlot[]).map((slot) => {
          const enc = bySlot.get(slot);
          return (
            <div key={slot}>
              <label className="mb-1.5 block text-theme-xs font-medium text-gray-500">
                {slotLabels[slot]}
              </label>
              <div
                className={cn(
                  "flex min-h-[40px] items-center justify-between gap-2 rounded-lg border border-dashed px-3 py-2",
                  enc?.fieldName
                    ? "border-brand-200 bg-brand-50/50 dark:border-brand-500/30 dark:bg-brand-500/10"
                    : "border-gray-200 dark:border-gray-700",
                )}
              >
                {enc?.fieldName ? (
                  <>
                    <span className="min-w-0 truncate text-theme-sm font-medium">{enc.fieldName}</span>
                    {enc.fieldType ? (
                      <Badge variant="light" className="shrink-0">
                        {enc.fieldType}
                      </Badge>
                    ) : null}
                    {onClear ? (
                      <button
                        type="button"
                        onClick={() => onClear(slot)}
                        className="shrink-0 text-theme-xs text-gray-400 hover:text-error-500"
                        aria-label={`清空${slotLabels[slot]}`}
                      >
                        ×
                      </button>
                    ) : null}
                  </>
                ) : (
                  <span className="text-theme-xs text-gray-400">拖入字段</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
