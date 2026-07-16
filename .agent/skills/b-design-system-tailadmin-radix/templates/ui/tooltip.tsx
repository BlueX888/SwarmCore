import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const tooltipContentVariants = cva(
  "z-99999 overflow-hidden rounded-lg px-3.5 py-2 text-xs font-medium shadow-md animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
  {
    variants: {
      variant: {
        default:
          "border border-gray-200 bg-white text-gray-700 dark:border-gray-700 dark:bg-gray-dark dark:text-white/90",
        inverted: "border border-gray-800 bg-gray-900 text-white dark:border-gray-700 dark:bg-gray-800",
        minimal: "bg-white text-gray-700 shadow-lg dark:bg-gray-900 dark:text-white/90",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

const TooltipProvider = TooltipPrimitive.Provider;
const Tooltip = TooltipPrimitive.Root;
const TooltipTrigger = TooltipPrimitive.Trigger;

const TooltipContent = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content> &
    VariantProps<typeof tooltipContentVariants> & {
      showArrow?: boolean;
    }
>(({ className, variant, sideOffset = 6, showArrow, children, ...props }, ref) => {
  const arrowOn = showArrow ?? variant !== "minimal";

  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        ref={ref}
        sideOffset={sideOffset}
        className={cn(tooltipContentVariants({ variant }), className)}
        {...props}
      >
        {children}
        {arrowOn ? (
          <TooltipPrimitive.Arrow
            className={cn(
              variant === "inverted"
                ? "fill-gray-900 dark:fill-gray-800"
                : "fill-white dark:fill-gray-dark",
            )}
          />
        ) : null}
      </TooltipPrimitive.Content>
    </TooltipPrimitive.Portal>
  );
});
TooltipContent.displayName = TooltipPrimitive.Content.displayName;

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider, tooltipContentVariants };
