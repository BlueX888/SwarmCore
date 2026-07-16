import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";
import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", {
  variants: {
    color: {
      primary: "bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400",
      success: "bg-success-50 text-success-600 dark:bg-success-500/15 dark:text-success-500",
      error: "bg-error-50 text-error-600 dark:bg-error-500/15 dark:text-error-500",
      warning: "bg-warning-50 text-warning-600 dark:bg-warning-500/15 dark:text-warning-500",
      neutral: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
    },
  },
  defaultVariants: { color: "neutral" },
});

export interface BadgeProps extends Omit<React.HTMLAttributes<HTMLSpanElement>, "color">, VariantProps<typeof badgeVariants> {}
export function Badge({ className, color, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ color }), className)} {...props} />;
}
