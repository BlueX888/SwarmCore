import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const sliderRootVariants = cva("relative flex touch-none select-none items-center", {
  variants: {
    orientation: {
      horizontal: "w-full",
      vertical: "h-48 flex-col",
    },
    size: {
      sm: "",
      md: "",
      lg: "",
    },
  },
  defaultVariants: {
    orientation: "horizontal",
    size: "md",
  },
});

const sliderTrackVariants = cva("relative grow overflow-hidden rounded-full bg-gray-200 dark:bg-gray-800", {
  variants: {
    orientation: {
      horizontal: "h-1.5 w-full",
      vertical: "h-full w-1.5",
    },
    size: {
      sm: "",
      md: "",
      lg: "",
    },
  },
  compoundVariants: [
    { orientation: "horizontal", size: "sm", className: "h-1" },
    { orientation: "horizontal", size: "lg", className: "h-2" },
    { orientation: "vertical", size: "sm", className: "w-1" },
    { orientation: "vertical", size: "lg", className: "w-2" },
  ],
  defaultVariants: {
    orientation: "horizontal",
    size: "md",
  },
});

const sliderThumbVariants = cva(
  "block rounded-full border border-brand-500 bg-white shadow-theme-xs transition-colors focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 disabled:pointer-events-none disabled:opacity-50 dark:bg-gray-900",
  {
    variants: {
      size: {
        sm: "size-3.5",
        md: "size-4",
        lg: "size-5",
      },
    },
    defaultVariants: { size: "md" },
  },
);

export interface SliderProps
  extends React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>,
    VariantProps<typeof sliderRootVariants> {}

const Slider = React.forwardRef<React.ElementRef<typeof SliderPrimitive.Root>, SliderProps>(
  ({ className, orientation = "horizontal", size = "md", defaultValue, value, ...props }, ref) => {
    const thumbCount = Math.max(value?.length ?? defaultValue?.length ?? 1, 1);

    return (
      <SliderPrimitive.Root
        ref={ref}
        orientation={orientation}
        defaultValue={defaultValue}
        value={value}
        className={cn(sliderRootVariants({ orientation, size }), className)}
        {...props}
      >
        <SliderPrimitive.Track className={cn(sliderTrackVariants({ orientation, size }))}>
          <SliderPrimitive.Range className="absolute h-full bg-brand-500" />
        </SliderPrimitive.Track>
        {Array.from({ length: thumbCount }).map((_, index) => (
          <SliderPrimitive.Thumb key={index} className={cn(sliderThumbVariants({ size }))} />
        ))}
      </SliderPrimitive.Root>
    );
  },
);
Slider.displayName = SliderPrimitive.Root.displayName;

export { Slider, sliderRootVariants };
