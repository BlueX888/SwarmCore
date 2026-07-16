import * as React from "react";
import { format, setHours, setMinutes, setSeconds, getHours, getMinutes, getSeconds, isWithinInterval } from "date-fns";
import { Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";

type InputSkin = "outlined" | "filled" | "borderless" | "underlined";

const triggerSkinClasses: Record<InputSkin, string> = {
  outlined:
    "rounded-lg border border-gray-300 bg-transparent shadow-theme-xs dark:border-gray-700 dark:bg-gray-900",
  filled: "rounded-lg border border-transparent bg-gray-100 shadow-none dark:bg-white/5",
  borderless: "rounded-lg border border-transparent bg-transparent shadow-none",
  underlined:
    "rounded-none border-0 border-b bg-transparent px-0 shadow-none border-b-gray-300 dark:border-b-gray-700",
};

function buildStepValues(max: number, step: number): number[] {
  const values: number[] = [];
  for (let i = 0; i <= max; i += step) {
    values.push(i);
  }
  return values;
}

function padUnit(value: number): string {
  return String(value).padStart(2, "0");
}

function isTimeInRange(time: Date, range?: [Date, Date]): boolean {
  if (!range) return true;
  const [start, end] = range;
  const base = new Date(2000, 0, 1);
  const candidate = setSeconds(
    setMinutes(setHours(base, getHours(time)), getMinutes(time)),
    getSeconds(time),
  );
  const rangeStart = setSeconds(
    setMinutes(setHours(base, getHours(start)), getMinutes(start)),
    getSeconds(start),
  );
  const rangeEnd = setSeconds(
    setMinutes(setHours(base, getHours(end)), getMinutes(end)),
    getSeconds(end),
  );
  return isWithinInterval(candidate, { start: rangeStart, end: rangeEnd });
}

export type TimeColumnsProps = {
  value?: Date;
  onChange?: (value: Date) => void;
  showSeconds?: boolean;
  minuteStep?: number;
  secondStep?: number;
  disabledHours?: (hour: number) => boolean;
  disabledMinutes?: (hour: number, minute: number) => boolean;
  range?: [Date, Date];
  className?: string;
};

function TimeColumn({
  label,
  values,
  selected,
  onSelect,
  formatValue = padUnit,
  isDisabled,
}: {
  label: string;
  values: number[];
  selected: number;
  onSelect: (value: number) => void;
  formatValue?: (value: number) => string;
  isDisabled?: (value: number) => boolean;
}) {
  const selectedRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    selectedRef.current?.scrollIntoView({ block: "center" });
  }, [selected]);

  return (
    <div className="flex w-[56px] shrink-0 flex-col border-r border-gray-200 last:border-r-0 dark:border-gray-800">
      <div className="border-b border-gray-200 px-2 py-1.5 text-center text-theme-xs font-medium text-gray-500 dark:border-gray-800 dark:text-gray-400">
        {label}
      </div>
      <ScrollArea className="h-[200px]">
        <ul className="p-1">
          {values.map((item) => {
            const disabled = isDisabled?.(item) ?? false;
            const isSelected = item === selected;
            return (
              <li key={item}>
                <button
                  ref={isSelected ? selectedRef : undefined}
                  type="button"
                  disabled={disabled}
                  onClick={() => onSelect(item)}
                  className={cn(
                    "flex w-full items-center justify-center rounded-md px-2 py-1.5 text-sm transition-colors",
                    isSelected
                      ? "bg-brand-50 font-medium text-brand-600 dark:bg-brand-500/15 dark:text-brand-400"
                      : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-white/5",
                    disabled && "cursor-not-allowed opacity-40",
                  )}
                >
                  {formatValue(item)}
                </button>
              </li>
            );
          })}
        </ul>
      </ScrollArea>
    </div>
  );
}

export function TimeColumns({
  value,
  onChange,
  showSeconds = false,
  minuteStep = 1,
  secondStep = 1,
  disabledHours,
  disabledMinutes,
  range,
  className,
}: TimeColumnsProps) {
  const base = value ?? new Date();
  const hour = getHours(base);
  const minute = getMinutes(base);
  const second = getSeconds(base);

  const hours = buildStepValues(23, 1);
  const minutes = buildStepValues(59, minuteStep);
  const seconds = buildStepValues(59, secondStep);

  const commit = (nextHour: number, nextMinute: number, nextSecond: number) => {
    const next = setSeconds(setMinutes(setHours(base, nextHour), nextMinute), nextSecond);
    onChange?.(next);
  };

  const isHourDisabled = (h: number) => {
    if (disabledHours?.(h)) return true;
    if (!range) return false;
    const probe = setSeconds(setMinutes(setHours(base, h), minute), second);
    return !isTimeInRange(probe, range);
  };

  const isMinuteDisabled = (m: number) => {
    if (disabledMinutes?.(hour, m)) return true;
    if (!range) return false;
    const probe = setSeconds(setMinutes(setHours(base, hour), m), second);
    return !isTimeInRange(probe, range);
  };

  const isSecondDisabled = (s: number) => {
    if (!range) return false;
    const probe = setSeconds(setMinutes(setHours(base, hour), minute), s);
    return !isTimeInRange(probe, range);
  };

  return (
    <div className={cn("flex border-t border-gray-200 dark:border-gray-800", className)} data-component="time-columns">
      <TimeColumn
        label="时"
        values={hours}
        selected={hour}
        onSelect={(h) => commit(h, minute, second)}
        isDisabled={isHourDisabled}
      />
      <TimeColumn
        label="分"
        values={minutes}
        selected={minute}
        onSelect={(m) => commit(hour, m, second)}
        isDisabled={isMinuteDisabled}
      />
      {showSeconds ? (
        <TimeColumn
          label="秒"
          values={seconds}
          selected={second}
          onSelect={(s) => commit(hour, minute, s)}
          isDisabled={isSecondDisabled}
        />
      ) : null}
    </div>
  );
}

export type TimePickerProps = {
  value?: Date;
  onChange?: (value: Date | undefined) => void;
  format?: string;
  showSeconds?: boolean;
  minuteStep?: number;
  secondStep?: number;
  disabledHours?: (hour: number) => boolean;
  disabledMinutes?: (hour: number, minute: number) => boolean;
  range?: [Date, Date];
  inputSkin?: InputSkin;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
};

export function TimePicker({
  value,
  onChange,
  format: formatString = "HH:mm",
  showSeconds = false,
  minuteStep = 1,
  secondStep = 1,
  disabledHours,
  disabledMinutes,
  range,
  inputSkin = "outlined",
  placeholder = "请选择时间",
  disabled = false,
  className,
}: TimePickerProps) {
  const [open, setOpen] = React.useState(false);
  const hasValue = Boolean(value);
  const displayValue = hasValue && value ? format(value, formatString) : placeholder;

  const handleChange = (next: Date) => {
    onChange?.(next);
  };

  return (
    <Popover open={open} onOpenChange={(next) => !disabled && setOpen(next)}>
      <PopoverTrigger asChild>
        <button
          type="button"
          disabled={disabled}
          className={cn(
            "flex h-11 w-full items-center px-4 py-2.5 text-left text-sm transition-colors",
            triggerSkinClasses[inputSkin],
            !hasValue && "text-gray-400 dark:text-white/30",
            hasValue && "text-gray-800 dark:text-white/90",
            disabled && "cursor-not-allowed opacity-40",
            className,
          )}
        >
          <Clock className="mr-2 size-5 shrink-0 text-gray-500 dark:text-gray-400" />
          <span className="truncate">{displayValue}</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <TimeColumns
          value={value}
          onChange={handleChange}
          showSeconds={showSeconds}
          minuteStep={minuteStep}
          secondStep={secondStep}
          disabledHours={disabledHours}
          disabledMinutes={disabledMinutes}
          range={range}
        />
      </PopoverContent>
    </Popover>
  );
}
