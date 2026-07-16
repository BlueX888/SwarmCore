import * as React from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

export type RatingProps = {
  value?: number;
  onChange?: (value: number) => void;
  count?: number;
  allowHalf?: boolean;
  readOnly?: boolean;
  disabled?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
};

const sizeClasses = {
  sm: "size-4",
  md: "size-5",
  lg: "size-6",
} as const;

function clampRating(value: number, count: number, allowHalf: boolean): number {
  const min = allowHalf ? 0.5 : 1;
  const clamped = Math.min(count, Math.max(min, value));
  return allowHalf ? Math.round(clamped * 2) / 2 : Math.round(clamped);
}

export function Rating({
  value = 0,
  onChange,
  count = 5,
  allowHalf = false,
  readOnly = false,
  disabled = false,
  size = "md",
  className,
}: RatingProps) {
  const [hoverValue, setHoverValue] = React.useState<number | null>(null);
  const interactive = !readOnly && !disabled;
  const displayValue = hoverValue ?? value;
  const starSize = sizeClasses[size];

  const commitValue = (next: number) => {
    if (!interactive) return;
    onChange?.(clampRating(next, count, allowHalf));
  };

  const resolveStarValue = (index: number, event?: React.MouseEvent<HTMLButtonElement>) => {
    const starNumber = index + 1;
    if (!allowHalf || !event) return starNumber;
    const rect = event.currentTarget.getBoundingClientRect();
    const isLeftHalf = event.clientX - rect.left < rect.width / 2;
    return isLeftHalf ? starNumber - 0.5 : starNumber;
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (!interactive) return;

    if (event.key === "ArrowRight" || event.key === "ArrowUp") {
      event.preventDefault();
      const step = allowHalf ? 0.5 : 1;
      commitValue(Math.min(count, value + step));
    } else if (event.key === "ArrowLeft" || event.key === "ArrowDown") {
      event.preventDefault();
      const step = allowHalf ? 0.5 : 1;
      commitValue(Math.max(allowHalf ? 0.5 : 0, value - step));
    }
  };

  return (
    <div
      role="slider"
      aria-valuemin={allowHalf ? 0.5 : 0}
      aria-valuemax={count}
      aria-valuenow={value}
      aria-readonly={readOnly || undefined}
      aria-disabled={disabled || undefined}
      tabIndex={interactive ? 0 : -1}
      onKeyDown={handleKeyDown}
      className={cn("inline-flex items-center gap-0.5", disabled && "opacity-40", className)}
      onMouseLeave={() => setHoverValue(null)}
    >
      {Array.from({ length: count }, (_, index) => {
        const starValue = index + 1;
        const filled = displayValue >= starValue;
        const halfFilled = allowHalf && displayValue >= starValue - 0.5 && displayValue < starValue;

        return (
          <button
            key={starValue}
            type="button"
            disabled={!interactive}
            aria-label={`${starValue} 星`}
            className={cn(
              "relative inline-flex shrink-0 items-center justify-center transition-colors",
              interactive ? "cursor-pointer" : "cursor-default",
            )}
            onMouseMove={(event) => {
              if (!interactive) return;
              setHoverValue(resolveStarValue(index, event));
            }}
            onClick={(event) => commitValue(resolveStarValue(index, event))}
          >
            <Star
              className={cn(
                starSize,
                filled || halfFilled
                  ? "fill-warning-400 text-warning-400"
                  : "fill-transparent text-gray-300 dark:text-gray-600",
              )}
            />
            {halfFilled ? (
              <Star
                className={cn(
                  starSize,
                  "absolute left-0 top-0 fill-warning-400 text-warning-400",
                  "[clip-path:inset(0_50%_0_0)]",
                )}
              />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
