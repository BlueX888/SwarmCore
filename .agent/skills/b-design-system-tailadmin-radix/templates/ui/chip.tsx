import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

const chipVariants = cva(
  "inline-flex max-w-full items-center gap-1 rounded-full font-medium transition-colors",
  {
    variants: {
      variant: {
        filled: "",
        outlined: "border bg-transparent",
      },
      color: {
        brand: "",
        success: "",
        error: "",
        warning: "",
        info: "",
        neutral: "",
      },
      size: {
        sm: "px-2 py-0.5 text-theme-xs",
        md: "px-2.5 py-0.5 text-sm",
      },
    },
    compoundVariants: [
      { variant: "filled", color: "brand", className: "bg-brand-500 text-white" },
      { variant: "filled", color: "success", className: "bg-success-500 text-white" },
      { variant: "filled", color: "error", className: "bg-error-500 text-white" },
      { variant: "filled", color: "warning", className: "bg-warning-500 text-white" },
      { variant: "filled", color: "info", className: "bg-blue-light-500 text-white" },
      { variant: "filled", color: "neutral", className: "bg-gray-200 text-gray-700 dark:bg-white/10 dark:text-white/80" },
      { variant: "outlined", color: "brand", className: "border-brand-500 text-brand-600 dark:text-brand-400" },
      { variant: "outlined", color: "success", className: "border-success-500 text-success-600 dark:text-success-400" },
      { variant: "outlined", color: "error", className: "border-error-500 text-error-600 dark:text-error-400" },
      { variant: "outlined", color: "warning", className: "border-warning-500 text-warning-600 dark:text-warning-400" },
      { variant: "outlined", color: "info", className: "border-blue-light-500 text-blue-light-600 dark:text-blue-light-400" },
      { variant: "outlined", color: "neutral", className: "border-gray-300 text-gray-600 dark:border-gray-700 dark:text-gray-300" },
    ],
    defaultVariants: {
      variant: "filled",
      color: "brand",
      size: "md",
    },
  },
);

export interface ChipProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof chipVariants> {
  icon?: React.ReactNode;
  onDelete?: () => void;
  deleteLabel?: string;
  checkable?: boolean;
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

function Chip({
  className,
  variant,
  color,
  size,
  icon,
  onDelete,
  deleteLabel = "移除标签",
  checkable,
  checked = false,
  onCheckedChange,
  children,
  onClick,
  onKeyDown,
  ...props
}: ChipProps) {
  const handleClick = (event: React.MouseEvent<HTMLSpanElement>) => {
    if (checkable) {
      onCheckedChange?.(!checked);
    }
    onClick?.(event);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLSpanElement>) => {
    if (checkable && (event.key === " " || event.key === "Enter")) {
      event.preventDefault();
      onCheckedChange?.(!checked);
    }
    onKeyDown?.(event);
  };

  return (
    <span
      className={cn(
        chipVariants({ variant, color, size }),
        checkable && "cursor-pointer select-none",
        checkable && checked && "ring-2 ring-brand-500",
        className,
      )}
      role={checkable ? "checkbox" : undefined}
      aria-checked={checkable ? checked : undefined}
      tabIndex={checkable ? 0 : undefined}
      onClick={checkable ? handleClick : onClick}
      onKeyDown={checkable ? handleKeyDown : onKeyDown}
      {...props}
    >
      {icon}
      <span className="truncate">{children}</span>
      {onDelete ? (
        <button
          type="button"
          aria-label={deleteLabel}
          onClick={(event) => {
            event.stopPropagation();
            onDelete();
          }}
          className="inline-flex size-4 items-center justify-center rounded-full hover:bg-black/10 dark:hover:bg-white/10"
        >
          <X className="size-3" />
        </button>
      ) : null}
    </span>
  );
}

export { Chip, chipVariants };
