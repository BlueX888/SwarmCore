import * as React from "react";
import { format, getHours, getMinutes, getSeconds, setHours, setMinutes, setSeconds } from "date-fns";
import { Calendar as CalendarIcon } from "lucide-react";
import type { DateRange } from "react-day-picker";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { TimeColumns } from "@/components/ui/time-picker";

export type DatePickerMode = "single" | "range";
export type DatePickerSelectionMode = "single" | "range" | "multiple";
export type DatePickerValue = Date | DateRange | Date[];

export type DatePickerShowTimeConfig = {
  format?: string;
  minuteStep?: number;
};

export type DatePickerProps = {
  label?: string;
  mode?: DatePickerMode;
  selectionMode?: DatePickerSelectionMode;
  value?: DatePickerValue;
  defaultValue?: DatePickerValue;
  onValueChange?: (value: DatePickerValue | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  min?: Date;
  max?: Date;
  unavailable?: Date[];
  numberOfMonths?: number;
  size?: "sm" | "md" | "lg";
  formatString?: string;
  showTime?: boolean | DatePickerShowTimeConfig;
  error?: string;
  className?: string;
  id?: string;
};

function isDateRange(value: DatePickerValue | undefined): value is DateRange {
  return Boolean(value && typeof value === "object" && "from" in value);
}

function isDateArray(value: DatePickerValue | undefined): value is Date[] {
  return Array.isArray(value);
}

function formatRangeValue(range: DateRange | undefined): string {
  if (!range?.from) {
    return "";
  }
  if (range.to) {
    return `${format(range.from, "yyyy-MM-dd")} - ${format(range.to, "yyyy-MM-dd")}`;
  }
  return format(range.from, "yyyy-MM-dd");
}

function formatMultipleValue(value: Date[] | undefined, formatString: string): string {
  if (!value?.length) {
    return "";
  }
  if (value.length === 1) {
    return format(value[0], formatString);
  }
  return `${value.length} dates selected`;
}

function buildDisabledDates({
  min,
  max,
  unavailable,
}: Pick<DatePickerProps, "min" | "max" | "unavailable">) {
  return [
    min ? { before: min } : undefined,
    max ? { after: max } : undefined,
    ...(unavailable ?? []),
  ].filter(Boolean);
}

export function DatePicker({
  label,
  mode = "single",
  selectionMode,
  value,
  defaultValue,
  onValueChange,
  placeholder = "请选择日期",
  disabled = false,
  min,
  max,
  unavailable,
  numberOfMonths,
  size = "md",
  formatString = "yyyy-MM-dd",
  showTime,
  error,
  className,
  id,
}: DatePickerProps) {
  const resolvedMode = selectionMode ?? mode;
  const showTimeEnabled = resolvedMode === "single" && Boolean(showTime);
  const showTimeConfig = React.useMemo<DatePickerShowTimeConfig | null>(() => {
    if (!showTimeEnabled) return null;
    if (showTime === true) {
      return { format: "yyyy-MM-dd HH:mm", minuteStep: 1 };
    }
    return {
      format: showTime.format ?? `${formatString} HH:mm`,
      minuteStep: showTime.minuteStep ?? 1,
    };
  }, [showTime, showTimeEnabled, formatString]);
  const resolvedFormatString = showTimeConfig?.format ?? formatString;
  const isControlled = value !== undefined;
  const [internalSingle, setInternalSingle] = React.useState<Date | undefined>(
    resolvedMode === "single" && defaultValue && !isDateRange(defaultValue) && !isDateArray(defaultValue)
      ? defaultValue
      : undefined,
  );
  const [internalRange, setInternalRange] = React.useState<DateRange | undefined>(
    resolvedMode === "range" && defaultValue && isDateRange(defaultValue)
      ? defaultValue
      : undefined,
  );
  const [internalMultiple, setInternalMultiple] = React.useState<Date[] | undefined>(
    resolvedMode === "multiple" && isDateArray(defaultValue)
      ? defaultValue
      : undefined,
  );
  const [open, setOpen] = React.useState(false);
  const inputId = id ?? React.useId();
  const errorId = error ? `${inputId}-error` : undefined;
  const disabledDates = buildDisabledDates({ min, max, unavailable });
  const triggerSizeClass = {
    sm: "h-10 px-3 py-2 text-sm",
    md: "h-11 px-4 py-2.5",
    lg: "h-12 px-4 py-3 text-base",
  }[size];

  const selectedSingle =
    resolvedMode === "single"
      ? isControlled
        ? isDateRange(value)
          ? value.from
          : isDateArray(value)
            ? value[0]
          : (value as Date | undefined)
        : internalSingle
      : undefined;

  const selectedRange =
    resolvedMode === "range"
      ? isControlled
        ? isDateRange(value)
          ? value
          : undefined
        : internalRange
      : undefined;

  const selectedMultiple =
    resolvedMode === "multiple"
      ? isControlled
        ? isDateArray(value)
          ? value
          : undefined
        : internalMultiple
      : undefined;

  const displayValue =
    resolvedMode === "range"
      ? formatRangeValue(selectedRange) || placeholder
      : resolvedMode === "multiple"
        ? formatMultipleValue(selectedMultiple, formatString) || placeholder
      : selectedSingle
        ? format(selectedSingle, resolvedFormatString)
        : placeholder;

  const hasValue =
    resolvedMode === "range"
      ? Boolean(selectedRange?.from)
      : resolvedMode === "multiple"
        ? Boolean(selectedMultiple?.length)
      : Boolean(selectedSingle);

  const mergeDateWithTime = (datePart: Date, timeSource?: Date) => {
    const source = timeSource ?? new Date();
    return setSeconds(
      setMinutes(
        setHours(datePart, getHours(source)),
        getMinutes(source),
      ),
      getSeconds(source),
    );
  };

  const updateSingle = (next: Date | undefined) => {
    const merged =
      next && showTimeConfig
        ? mergeDateWithTime(next, selectedSingle)
        : next;

    if (!isControlled) {
      setInternalSingle(merged);
    }
    onValueChange?.(merged);
    if (merged && !showTimeConfig) {
      setOpen(false);
    }
  };

  const updateSingleTime = (timeValue: Date) => {
    const base = selectedSingle ?? new Date();
    const merged = mergeDateWithTime(base, timeValue);

    if (!isControlled) {
      setInternalSingle(merged);
    }
    onValueChange?.(merged);
  };

  const updateRange = (next: DateRange | undefined) => {
    if (!isControlled) {
      setInternalRange(next);
    }
    onValueChange?.(next);
    if (next?.from && next?.to) {
      setOpen(false);
    }
  };

  const updateMultiple = (next: Date[] | undefined) => {
    if (!isControlled) {
      setInternalMultiple(next);
    }
    onValueChange?.(next);
  };

  return (
    <div className={cn("w-full", className)}>
      {label ? (
        <label
          htmlFor={inputId}
          className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400"
        >
          {label}
        </label>
      ) : null}

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            id={inputId}
            type="button"
            variant="outline"
            disabled={disabled}
            aria-invalid={Boolean(error)}
            aria-describedby={errorId}
            className={cn(
              "w-full justify-start text-left font-normal shadow-theme-xs",
              triggerSizeClass,
              !hasValue && "text-gray-400 dark:text-white/30",
              error &&
                "border-error-500 focus-visible:ring-error-500/20 dark:border-error-500",
            )}
          >
            <CalendarIcon className="mr-2 size-5 text-gray-500 dark:text-gray-400" />
            {displayValue}
          </Button>
        </PopoverTrigger>

        <PopoverContent className="w-auto p-0" align="start">
          {resolvedMode === "range" ? (
            <Calendar
              mode="range"
              selected={selectedRange}
              onSelect={updateRange}
              numberOfMonths={numberOfMonths ?? 2}
              defaultMonth={selectedRange?.from}
              disabled={disabledDates}
              size={size}
            />
          ) : resolvedMode === "multiple" ? (
            <Calendar
              mode="multiple"
              selected={selectedMultiple}
              onSelect={updateMultiple}
              numberOfMonths={numberOfMonths}
              defaultMonth={selectedMultiple?.[0]}
              disabled={disabledDates}
              size={size}
            />
          ) : showTimeConfig ? (
            <>
              <Calendar
                mode="single"
                selected={selectedSingle}
                onSelect={updateSingle}
                defaultMonth={selectedSingle}
                disabled={disabledDates}
                size={size}
              />
              <TimeColumns
                value={selectedSingle}
                onChange={updateSingleTime}
                minuteStep={showTimeConfig.minuteStep}
              />
            </>
          ) : (
            <Calendar
              mode="single"
              selected={selectedSingle}
              onSelect={updateSingle}
              defaultMonth={selectedSingle}
              disabled={disabledDates}
              size={size}
            />
          )}
        </PopoverContent>
      </Popover>

      {error ? (
        <p id={errorId} className="mt-1.5 text-theme-xs text-error-500">
          {error}
        </p>
      ) : null}
    </div>
  );
}
