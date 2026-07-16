import * as React from "react";
import * as SeparatorPrimitive from "@radix-ui/react-separator";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const separatorVariants = cva("shrink-0 bg-gray-200 dark:bg-gray-800", {
  variants: {
    orientation: {
      horizontal: "h-px w-full",
      vertical: "h-full w-px min-h-4",
    },
  },
  defaultVariants: { orientation: "horizontal" },
});

export interface SeparatorProps
  extends React.ComponentPropsWithoutRef<typeof SeparatorPrimitive.Root>,
    VariantProps<typeof separatorVariants> {}

const Separator = React.forwardRef<
  React.ElementRef<typeof SeparatorPrimitive.Root>,
  SeparatorProps
>(({ className, orientation = "horizontal", decorative = true, ...props }, ref) => (
  <SeparatorPrimitive.Root
    ref={ref}
    decorative={decorative}
    orientation={orientation}
    className={cn(separatorVariants({ orientation }), className)}
    {...props}
  />
));
Separator.displayName = SeparatorPrimitive.Root.displayName;

type SeparatorWithLabelProps = {
  label: React.ReactNode;
  labelPosition?: "start" | "center" | "end";
  orientation?: "horizontal" | "vertical";
  className?: string;
};

function SeparatorWithLabel({
  label,
  labelPosition = "center",
  orientation = "horizontal",
  className,
}: SeparatorWithLabelProps) {
  if (orientation === "vertical") {
    return <Separator orientation="vertical" className={className} />;
  }

  const justify =
    labelPosition === "start" ? "justify-start" : labelPosition === "end" ? "justify-end" : "justify-center";

  return (
    <div className={cn("flex items-center gap-3", justify, className)}>
      {labelPosition !== "start" ? <Separator className="flex-1" /> : null}
      <span className="text-theme-xs text-gray-500 dark:text-gray-400">{label}</span>
      {labelPosition !== "end" ? <Separator className="flex-1" /> : null}
    </div>
  );
}

export { Separator, SeparatorWithLabel, separatorVariants };
