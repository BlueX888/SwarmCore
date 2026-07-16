import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const countBadgeVariants = cva(
  "absolute flex items-center justify-center rounded-full font-semibold leading-none ring-2 ring-white dark:ring-gray-900",
  {
    variants: {
      variant: {
        count: "min-w-5 px-1",
        dot: "size-2.5 p-0",
        status: "size-2.5 p-0",
      },
      color: {
        brand: "bg-brand-500 text-white",
        success: "bg-success-500 text-white",
        error: "bg-error-500 text-white",
        warning: "bg-warning-500 text-white",
        info: "bg-blue-light-500 text-white",
        neutral: "bg-gray-500 text-white",
      },
      size: {
        sm: "text-[10px]",
        md: "text-theme-xs",
      },
      placement: {
        "top-right": "right-0 top-0 translate-x-1/3 -translate-y-1/3",
        "top-left": "left-0 top-0 -translate-x-1/3 -translate-y-1/3",
        "bottom-right": "bottom-0 right-0 translate-x-1/3 translate-y-1/3",
        "bottom-left": "bottom-0 left-0 -translate-x-1/3 translate-y-1/3",
      },
    },
    defaultVariants: {
      variant: "count",
      color: "error",
      size: "sm",
      placement: "top-right",
    },
  },
);

export interface CountBadgeProps
  extends Omit<React.HTMLAttributes<HTMLSpanElement>, "children">,
    VariantProps<typeof countBadgeVariants> {
  count?: number;
  max?: number;
  showZero?: boolean;
  invisible?: boolean;
}

function CountBadge({
  className,
  variant = "count",
  color,
  size,
  placement,
  count = 0,
  max = 99,
  showZero = false,
  invisible = false,
  ...props
}: CountBadgeProps) {
  if (invisible) return null;
  if (variant === "count" && count <= 0 && !showZero) return null;

  const label =
    variant === "count"
      ? count > max
        ? `${max}+`
        : String(count)
      : undefined;

  return (
    <span
      className={cn(countBadgeVariants({ variant, color, size, placement }), className)}
      aria-hidden={variant !== "count"}
      aria-label={variant === "count" ? `${count} 条未读` : undefined}
      {...props}
    >
      {variant === "count" ? label : null}
    </span>
  );
}

function CountBadgeAnchor({
  className,
  children,
  badge,
}: {
  className?: string;
  children: React.ReactNode;
  badge: React.ReactNode;
}) {
  return (
    <span className={cn("relative inline-flex", className)}>
      {children}
      {badge}
    </span>
  );
}

export { CountBadge, CountBadgeAnchor, countBadgeVariants };
