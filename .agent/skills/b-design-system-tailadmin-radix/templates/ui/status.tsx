import * as React from "react";
import { cn } from "@/lib/utils";

export type StatusValue = "healthy" | "degraded" | "down" | "unknown" | "maintenance";

const statusDotClass: Record<StatusValue, string> = {
  healthy: "bg-success-500",
  degraded: "bg-warning-500",
  down: "bg-error-500",
  unknown: "bg-gray-400",
  maintenance: "bg-brand-500",
};

const statusLabel: Record<StatusValue, string> = {
  healthy: "健康",
  degraded: "降级",
  down: "不可用",
  unknown: "未知",
  maintenance: "维护中",
};

export type StatusProps = {
  value: StatusValue;
  label?: React.ReactNode;
  size?: "sm" | "md";
  className?: string;
};

export function Status({ value, label, size = "md", className }: StatusProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 text-gray-700 dark:text-gray-300",
        size === "sm" ? "text-xs" : "text-sm",
        className,
      )}
    >
      <span
        className={cn(
          "rounded-full",
          size === "sm" ? "size-2" : "size-2.5",
          statusDotClass[value],
        )}
        aria-hidden
      />
      <span>{label ?? statusLabel[value]}</span>
    </span>
  );
}
