import * as React from "react";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

export type StatTrendProps = {
  direction: "up" | "down" | "flat";
  value: React.ReactNode;
  className?: string;
};

export function StatTrend({ direction, value, className }: StatTrendProps) {
  const tone =
    direction === "up"
      ? "text-success-500"
      : direction === "down"
        ? "text-error-500"
        : "text-gray-500";
  const Icon =
    direction === "up" ? TrendingUp : direction === "down" ? TrendingDown : Minus;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-theme-sm font-medium",
        tone,
        className,
      )}
    >
      <Icon className="size-4" aria-hidden />
      {value}
    </span>
  );
}
