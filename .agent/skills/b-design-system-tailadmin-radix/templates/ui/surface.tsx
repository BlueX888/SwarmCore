import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const surfaceVariants = cva("bg-white dark:bg-gray-900", {
  variants: {
    variant: {
      elevated: "",
      outlined: "border border-gray-200 dark:border-gray-800",
    },
    elevation: {
      0: "shadow-none",
      1: "shadow-theme-xs",
      2: "shadow-theme-sm",
      4: "shadow-theme-md",
      8: "shadow-theme-lg",
    },
    square: {
      true: "rounded-none",
      false: "rounded-2xl",
    },
  },
  defaultVariants: { variant: "elevated", elevation: 1, square: false },
});

export type SurfaceProps = React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof surfaceVariants>;

export const Surface = React.forwardRef<HTMLDivElement, SurfaceProps>(
  ({ className, variant, elevation, square, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(surfaceVariants({ variant, elevation, square }), className)}
      {...props}
    />
  ),
);
Surface.displayName = "Surface";

export { surfaceVariants };
