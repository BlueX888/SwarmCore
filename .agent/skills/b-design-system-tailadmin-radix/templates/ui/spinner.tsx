import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const spinnerVariants = cva("animate-spin text-brand-500", {
  variants: {
    size: {
      sm: "size-5",
      md: "size-8",
      lg: "size-10",
    },
  },
  defaultVariants: {
    size: "md",
  },
});

export interface SpinnerProps
  extends React.ComponentPropsWithoutRef<typeof Loader2>,
    VariantProps<typeof spinnerVariants> {}

const Spinner = React.forwardRef<
  React.ElementRef<typeof Loader2>,
  SpinnerProps
>(({ className, size, ...props }, ref) => (
  <Loader2
    ref={ref}
    className={cn(spinnerVariants({ size }), className)}
    aria-hidden={props["aria-label"] ? undefined : true}
    {...props}
  />
));
Spinner.displayName = "Spinner";

export { Spinner, spinnerVariants };
