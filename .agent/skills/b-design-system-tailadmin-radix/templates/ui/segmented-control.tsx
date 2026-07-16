import * as React from "react";
import * as ToggleGroupPrimitive from "@radix-ui/react-toggle-group";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const segmentedControlVariants = cva("items-center rounded-lg bg-gray-100 dark:bg-gray-900", {
  variants: {
    size: {
      sm: "gap-0.5 p-0.5",
      md: "gap-1 p-1",
      lg: "gap-1.5 p-1.5",
    },
    orientation: {
      horizontal: "inline-flex flex-row",
      vertical: "inline-flex flex-col",
    },
    block: {
      true: "flex w-full",
      false: "inline-flex w-auto",
    },
  },
  defaultVariants: { size: "md", orientation: "horizontal", block: false },
});

const segmentedItemVariants = cva(
  "inline-flex flex-1 items-center justify-center rounded-md font-medium text-gray-500 transition-colors hover:text-gray-800 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500/20 disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-white data-[state=on]:text-gray-900 data-[state=on]:shadow-theme-xs dark:text-gray-400 dark:hover:text-gray-200 dark:data-[state=on]:bg-white/[0.06] dark:data-[state=on]:text-white",
  {
    variants: {
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-9 px-4 text-sm",
        lg: "h-11 px-5 text-base",
      },
    },
    defaultVariants: { size: "md" },
  },
);

type SegmentedControlSingleProps = Omit<
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root>,
  "type" | "value" | "defaultValue" | "onValueChange"
> &
  VariantProps<typeof segmentedControlVariants> & {
    type?: "single";
    value?: string;
    defaultValue?: string;
    onValueChange?: (value: string) => void;
  };

type SegmentedControlMultipleProps = Omit<
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Root>,
  "type" | "value" | "defaultValue" | "onValueChange"
> &
  VariantProps<typeof segmentedControlVariants> & {
    type: "multiple";
    value?: string[];
    defaultValue?: string[];
    onValueChange?: (value: string[]) => void;
  };

type SegmentedControlProps = SegmentedControlSingleProps | SegmentedControlMultipleProps;

function SegmentedControl({
  className,
  size,
  orientation,
  block,
  type = "single",
  onValueChange,
  ...props
}: SegmentedControlProps) {
  const handleSingleChange = React.useCallback(
    (value: string) => {
      if (type !== "single" || value === "") return;
      (onValueChange as SegmentedControlSingleProps["onValueChange"])?.(value);
    },
    [type, onValueChange],
  );

  if (type === "multiple") {
    return (
      <ToggleGroupPrimitive.Root
        type="multiple"
        className={cn(segmentedControlVariants({ size, orientation, block }), className)}
        onValueChange={onValueChange as SegmentedControlMultipleProps["onValueChange"]}
        {...props}
      />
    );
  }

  return (
    <ToggleGroupPrimitive.Root
      type="single"
      className={cn(segmentedControlVariants({ size, orientation, block }), className)}
      onValueChange={handleSingleChange}
      {...props}
    />
  );
}

const SegmentedControlItem = React.forwardRef<
  React.ElementRef<typeof ToggleGroupPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof ToggleGroupPrimitive.Item> &
    VariantProps<typeof segmentedItemVariants>
>(({ className, size, ...props }, ref) => (
  <ToggleGroupPrimitive.Item
    ref={ref}
    className={cn(segmentedItemVariants({ size }), className)}
    {...props}
  />
));
SegmentedControlItem.displayName = "SegmentedControlItem";

export {
  SegmentedControl,
  SegmentedControlItem,
  segmentedControlVariants,
  segmentedItemVariants,
};
