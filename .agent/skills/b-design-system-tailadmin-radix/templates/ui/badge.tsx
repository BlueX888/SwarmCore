import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center justify-center gap-1 rounded-full font-medium",
  {
    variants: {
      variant: {
        light: "",
        solid: "",
        outline: "border bg-transparent",
        subtle: "",
        surface: "border",
      },
      color: {
        primary: "",
        success: "",
        error: "",
        warning: "",
        info: "",
        light: "",
        dark: "",
      },
      size: {
        sm: "px-2 py-0.5 text-theme-xs",
        md: "px-2.5 py-0.5 text-sm",
      },
    },
    compoundVariants: [
      {
        variant: "light",
        color: "primary",
        className:
          "bg-brand-50 text-brand-500 dark:bg-brand-500/15 dark:text-brand-400",
      },
      {
        variant: "light",
        color: "success",
        className:
          "bg-success-50 text-success-600 dark:bg-success-500/15 dark:text-success-500",
      },
      {
        variant: "light",
        color: "error",
        className:
          "bg-error-50 text-error-600 dark:bg-error-500/15 dark:text-error-500",
      },
      {
        variant: "light",
        color: "warning",
        className:
          "bg-warning-50 text-warning-600 dark:bg-warning-500/15 dark:text-orange-400",
      },
      {
        variant: "light",
        color: "info",
        className:
          "bg-blue-light-50 text-blue-light-500 dark:bg-blue-light-500/15 dark:text-blue-light-500",
      },
      {
        variant: "light",
        color: "light",
        className: "bg-gray-100 text-gray-700 dark:bg-white/5 dark:text-white/80",
      },
      {
        variant: "light",
        color: "dark",
        className: "bg-gray-500 text-white dark:bg-white/5 dark:text-white",
      },
      {
        variant: "solid",
        color: "primary",
        className: "bg-brand-500 text-white",
      },
      {
        variant: "solid",
        color: "success",
        className: "bg-success-500 text-white",
      },
      {
        variant: "solid",
        color: "error",
        className: "bg-error-500 text-white",
      },
      {
        variant: "solid",
        color: "warning",
        className: "bg-warning-500 text-white",
      },
      {
        variant: "solid",
        color: "info",
        className: "bg-blue-light-500 text-white",
      },
      {
        variant: "solid",
        color: "light",
        className: "bg-gray-400 text-white dark:bg-white/5 dark:text-white/80",
      },
      {
        variant: "solid",
        color: "dark",
        className: "bg-gray-700 text-white",
      },
      {
        variant: "outline",
        color: "primary",
        className: "border-brand-500 text-brand-600 dark:text-brand-400",
      },
      {
        variant: "outline",
        color: "success",
        className: "border-success-500 text-success-600 dark:text-success-400",
      },
      {
        variant: "outline",
        color: "error",
        className: "border-error-500 text-error-600 dark:text-error-400",
      },
      {
        variant: "outline",
        color: "warning",
        className: "border-warning-500 text-warning-600 dark:text-warning-400",
      },
      {
        variant: "outline",
        color: "info",
        className: "border-blue-light-500 text-blue-light-600 dark:text-blue-light-400",
      },
      {
        variant: "outline",
        color: "light",
        className: "border-gray-300 text-gray-600 dark:border-gray-700 dark:text-gray-300",
      },
      {
        variant: "outline",
        color: "dark",
        className: "border-gray-600 text-gray-700 dark:border-gray-500 dark:text-gray-300",
      },
      {
        variant: "subtle",
        color: "primary",
        className:
          "bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-400",
      },
      {
        variant: "subtle",
        color: "success",
        className:
          "bg-success-50 text-success-600 dark:bg-success-500/15 dark:text-success-500",
      },
      {
        variant: "subtle",
        color: "error",
        className:
          "bg-error-50 text-error-600 dark:bg-error-500/15 dark:text-error-500",
      },
      {
        variant: "subtle",
        color: "warning",
        className:
          "bg-warning-50 text-warning-600 dark:bg-warning-500/15 dark:text-orange-400",
      },
      {
        variant: "subtle",
        color: "info",
        className:
          "bg-blue-light-50 text-blue-light-600 dark:bg-blue-light-500/15 dark:text-blue-light-500",
      },
      {
        variant: "subtle",
        color: "light",
        className: "bg-gray-100 text-gray-700 dark:bg-white/5 dark:text-white/80",
      },
      {
        variant: "subtle",
        color: "dark",
        className: "bg-gray-200 text-gray-700 dark:bg-white/10 dark:text-white/80",
      },
      {
        variant: "surface",
        color: "primary",
        className:
          "border-brand-200 bg-brand-50/50 text-brand-600 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-400",
      },
      {
        variant: "surface",
        color: "success",
        className:
          "border-success-200 bg-success-50/50 text-success-600 dark:border-success-500/30 dark:bg-success-500/10 dark:text-success-500",
      },
      {
        variant: "surface",
        color: "error",
        className:
          "border-error-200 bg-error-50/50 text-error-600 dark:border-error-500/30 dark:bg-error-500/10 dark:text-error-500",
      },
      {
        variant: "surface",
        color: "warning",
        className:
          "border-warning-200 bg-warning-50/50 text-warning-600 dark:border-warning-500/30 dark:bg-warning-500/10 dark:text-orange-400",
      },
      {
        variant: "surface",
        color: "info",
        className:
          "border-blue-light-200 bg-blue-light-50/50 text-blue-light-600 dark:border-blue-light-500/30 dark:bg-blue-light-500/10 dark:text-blue-light-500",
      },
      {
        variant: "surface",
        color: "light",
        className:
          "border-gray-200 bg-gray-50 text-gray-700 dark:border-gray-700 dark:bg-white/5 dark:text-white/80",
      },
      {
        variant: "surface",
        color: "dark",
        className:
          "border-gray-300 bg-gray-100 text-gray-800 dark:border-gray-600 dark:bg-white/10 dark:text-white/90",
      },
    ],
    defaultVariants: {
      variant: "light",
      color: "primary",
      size: "md",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  startIcon?: React.ReactNode;
  endIcon?: React.ReactNode;
}

function Badge({
  className,
  variant,
  color,
  size,
  startIcon,
  endIcon,
  children,
  ...props
}: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, color, size }), className)} {...props}>
      {startIcon}
      {children}
      {endIcon}
    </span>
  );
}

export { Badge, badgeVariants };
