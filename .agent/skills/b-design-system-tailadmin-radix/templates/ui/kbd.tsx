import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const kbdVariants = cva(
  "inline-flex items-center rounded border border-gray-200 bg-gray-50 font-mono text-gray-600 shadow-theme-xs dark:border-gray-700 dark:bg-white/5 dark:text-gray-400",
  {
    variants: {
      size: {
        sm: "px-1 py-0.5 text-[10px]",
        md: "px-1.5 py-0.5 text-theme-xs",
      },
    },
    defaultVariants: {
      size: "md",
    },
  },
);

export type KbdProps = React.ComponentProps<"kbd"> & VariantProps<typeof kbdVariants>;

export function Kbd({ className, size, ...props }: KbdProps) {
  return <kbd className={cn(kbdVariants({ size }), className)} {...props} />;
}

export { kbdVariants };
