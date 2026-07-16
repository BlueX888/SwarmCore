import * as React from "react";
import * as CheckboxPrimitive from "@radix-ui/react-checkbox";
import { Check, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

export type CheckboxProps = React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root> & {
  indeterminate?: boolean;
};

const Checkbox = React.forwardRef<
  React.ElementRef<typeof CheckboxPrimitive.Root>,
  CheckboxProps
>(({ className, indeterminate, checked, ...props }, ref) => {
  const resolvedChecked = indeterminate ? "indeterminate" : checked;

  return (
    <CheckboxPrimitive.Root
      ref={ref}
      checked={resolvedChecked}
      className={cn(
        "peer size-5 shrink-0 rounded-md border border-gray-300 bg-transparent shadow-theme-xs transition-colors focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 disabled:cursor-not-allowed disabled:opacity-60 data-[state=checked]:border-transparent data-[state=checked]:bg-brand-500 data-[state=indeterminate]:border-transparent data-[state=indeterminate]:bg-brand-500 dark:border-gray-700",
        className,
      )}
      {...props}
    >
      <CheckboxPrimitive.Indicator className="flex items-center justify-center text-white">
        {resolvedChecked === "indeterminate" ? (
          <Minus className="size-3.5" strokeWidth={2.5} />
        ) : (
          <Check className="size-3.5" strokeWidth={2.5} />
        )}
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
});
Checkbox.displayName = CheckboxPrimitive.Root.displayName;

export { Checkbox };
