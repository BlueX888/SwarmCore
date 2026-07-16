import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

export interface ProgressProps
  extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  indicatorClassName?: string;
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ className, value, indicatorClassName, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn(
      "relative h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-800",
      className,
    )}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className={cn(
        "h-full w-full flex-1 rounded-full bg-brand-500 transition-all duration-300 ease-out",
        indicatorClassName,
      )}
      style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
    />
  </ProgressPrimitive.Root>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

const progressCircleVariants = cva("relative inline-flex items-center justify-center", {
  variants: {
    size: {
      sm: "size-10 text-theme-xs",
      md: "size-14 text-sm",
      lg: "size-20 text-base",
    },
  },
  defaultVariants: { size: "md" },
});

export type ProgressCircleProps = VariantProps<typeof progressCircleVariants> & {
  value?: number;
  indeterminate?: boolean;
  label?: React.ReactNode;
  className?: string;
};

function ProgressCircle({
  value = 0,
  indeterminate = false,
  size = "md",
  label,
  className,
}: ProgressCircleProps) {
  const radius = 18;
  const circumference = 2 * Math.PI * radius;
  const offset = indeterminate ? circumference * 0.25 : circumference - (value / 100) * circumference;

  return (
    <div
      className={cn(progressCircleVariants({ size }), className)}
      role="progressbar"
      aria-valuenow={indeterminate ? undefined : value}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-busy={indeterminate || undefined}
    >
      <svg className={cn("size-full -rotate-90", indeterminate && "animate-spin")} viewBox="0 0 44 44">
        <circle
          cx="22"
          cy="22"
          r={radius}
          fill="none"
          className="stroke-gray-200 dark:stroke-gray-800"
          strokeWidth="4"
        />
        <circle
          cx="22"
          cy="22"
          r={radius}
          fill="none"
          className="stroke-brand-500"
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      {!indeterminate ? (
        <span className="absolute font-semibold text-gray-800 dark:text-white/90">
          {label ?? `${value}%`}
        </span>
      ) : null}
    </div>
  );
}

export { Progress, ProgressCircle, progressCircleVariants };
