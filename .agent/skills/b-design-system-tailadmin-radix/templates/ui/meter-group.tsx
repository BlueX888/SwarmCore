import * as React from "react";
import { cn } from "@/lib/utils";

export type MeterGroupItem = {
  label: React.ReactNode;
  value: number;
  color?: "brand" | "success" | "warning" | "error" | "info" | "neutral";
};

export type MeterGroupProps = {
  items: MeterGroupItem[];
  max?: number;
  className?: string;
  showLegend?: boolean;
};

const colorClass: Record<NonNullable<MeterGroupItem["color"]>, string> = {
  brand: "bg-brand-500",
  success: "bg-success-500",
  warning: "bg-warning-500",
  error: "bg-error-500",
  info: "bg-blue-light-500",
  neutral: "bg-gray-400",
};

export function MeterGroup({
  items,
  max: maxProp,
  className,
  showLegend = true,
}: MeterGroupProps) {
  const total = items.reduce((sum, item) => sum + item.value, 0);
  const max = maxProp ?? total;

  return (
    <div className={cn("space-y-2", className)}>
      <div
        className="flex h-3 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-white/10"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={total}
      >
        {items.map((item, index) => {
          const width = max > 0 ? (item.value / max) * 100 : 0;
          const color = item.color ?? "brand";
          return (
            <div
              key={index}
              className={cn("h-full transition-all", colorClass[color])}
              style={{ width: `${width}%` }}
              title={`${item.label}: ${item.value}`}
            />
          );
        })}
      </div>
      {showLegend ? (
        <ul className="flex flex-wrap gap-x-4 gap-y-1 text-theme-xs text-gray-500 dark:text-gray-400">
          {items.map((item, index) => {
            const color = item.color ?? "brand";
            return (
              <li key={index} className="inline-flex items-center gap-1.5">
                <span className={cn("size-2 rounded-full", colorClass[color])} />
                <span>{item.label}</span>
                <span className="font-medium text-gray-700 dark:text-white/80">
                  {item.value}
                </span>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}
