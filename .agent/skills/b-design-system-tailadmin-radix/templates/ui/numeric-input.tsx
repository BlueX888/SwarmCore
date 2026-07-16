import * as React from "react";
import { Minus, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input, type InputProps } from "@/components/ui/input";

export type NumericFormat = "integer" | "decimal" | "currency" | "percent";

export type NumericInputProps = Omit<InputProps, "type" | "value" | "defaultValue" | "onChange"> & {
  format?: NumericFormat;
  value?: number | null;
  defaultValue?: number | null;
  min?: number;
  max?: number;
  precision?: number;
  step?: number;
  currency?: string;
  showStepper?: boolean;
  onValueChange?: (value: number | null) => void;
};

function formatDisplay(
  value: number | null,
  format: NumericFormat,
  precision: number,
  currency: string,
): string {
  if (value === null || Number.isNaN(value)) return "";
  if (format === "currency") {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      minimumFractionDigits: precision,
      maximumFractionDigits: precision,
    }).format(value);
  }
  if (format === "percent") {
    return `${value.toFixed(precision)}%`;
  }
  if (format === "integer") {
    return String(Math.trunc(value));
  }
  return value.toFixed(precision);
}

function parseNumeric(raw: string, format: NumericFormat): number | null {
  const cleaned = raw.replace(/[^0-9.-]/g, "");
  if (!cleaned || cleaned === "-" || cleaned === ".") return null;
  const parsed = format === "integer" ? parseInt(cleaned, 10) : parseFloat(cleaned);
  return Number.isNaN(parsed) ? null : parsed;
}

function clamp(value: number | null, min?: number, max?: number): number | null {
  if (value === null) return null;
  let next = value;
  if (min !== undefined) next = Math.max(min, next);
  if (max !== undefined) next = Math.min(max, next);
  return next;
}

export const NumericInput = React.forwardRef<HTMLInputElement, NumericInputProps>(
  (
    {
      className,
      format = "decimal",
      value,
      defaultValue = null,
      min,
      max,
      precision = format === "integer" ? 0 : 2,
      step = format === "integer" ? 1 : 0.01,
      currency = "USD",
      showStepper = false,
      disabled,
      readOnly,
      onValueChange,
      variant,
      ...props
    },
    ref,
  ) => {
    const isControlled = value !== undefined;
    const [internalValue, setInternalValue] = React.useState<number | null>(defaultValue);
    const [draft, setDraft] = React.useState("");
    const currentValue = isControlled ? value ?? null : internalValue;

    React.useEffect(() => {
      setDraft(formatDisplay(currentValue, format, precision, currency));
    }, [currentValue, format, precision, currency]);

    const commit = (next: number | null) => {
      const clamped = clamp(next, min, max);
      if (!isControlled) {
        setInternalValue(clamped);
      }
      onValueChange?.(clamped);
    };

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      setDraft(event.target.value);
      commit(parseNumeric(event.target.value, format));
    };

    const handleBlur = () => {
      setDraft(formatDisplay(currentValue, format, precision, currency));
    };

    const adjust = (delta: number) => {
      const base = currentValue ?? 0;
      commit(base + delta);
    };

    return (
      <div className={cn("flex items-center gap-2", className)}>
        {showStepper ? (
          <button
            type="button"
            disabled={disabled || readOnly}
            onClick={() => adjust(-step)}
            className="inline-flex size-11 shrink-0 items-center justify-center rounded-lg border border-gray-300 bg-transparent text-gray-600 hover:bg-gray-100 disabled:opacity-40 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-white/5"
            aria-label="减少数值"
          >
            <Minus className="size-4" />
          </button>
        ) : null}
        <Input
          ref={ref}
          inputMode={format === "integer" ? "numeric" : "decimal"}
          value={draft}
          disabled={disabled}
          readOnly={readOnly}
          variant={variant}
          onChange={handleChange}
          onBlur={handleBlur}
          className="min-w-0 flex-1"
          {...props}
        />
        {showStepper ? (
          <button
            type="button"
            disabled={disabled || readOnly}
            onClick={() => adjust(step)}
            className="inline-flex size-11 shrink-0 items-center justify-center rounded-lg border border-gray-300 bg-transparent text-gray-600 hover:bg-gray-100 disabled:opacity-40 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-white/5"
            aria-label="增加数值"
          >
            <Plus className="size-4" />
          </button>
        ) : null}
      </div>
    );
  },
);
NumericInput.displayName = "NumericInput";
