import type * as React from "react";
import { cn } from "@/lib/utils";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 形状变体：默认圆角矩形；circle 为圆形 */
  variant?: "rect" | "circle" | "text";
}

export function Skeleton({ className, variant = "rect", ...props }: SkeletonProps) {
  return (
    <div
      aria-hidden
      className={cn(
        "animate-pulse bg-gray-200 dark:bg-gray-800",
        variant === "rect" && "rounded-lg",
        variant === "circle" && "rounded-full",
        variant === "text" && "h-4 rounded",
        className,
      )}
      {...props}
    />
  );
}
