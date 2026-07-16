import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const skeletonVariants = cva("animate-pulse bg-gray-200 dark:bg-gray-800", {
  variants: {
    variant: {
      rectangular: "rounded-md",
      text: "h-4 rounded-md",
      circular: "rounded-full",
    },
  },
  defaultVariants: {
    variant: "rectangular",
  },
});

export interface SkeletonProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof skeletonVariants> {}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, variant, ...props }, ref) => (
    <div ref={ref} className={cn(skeletonVariants({ variant }), className)} {...props} />
  ),
);
Skeleton.displayName = "Skeleton";

export { Skeleton, skeletonVariants };
