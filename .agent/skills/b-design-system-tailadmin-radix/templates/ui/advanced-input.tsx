import * as React from "react";
import { Copy, Search, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input, type InputProps } from "@/components/ui/input";

export type AdvancedInputProps = Omit<InputProps, "type"> & {
  type?: "text" | "search" | "password" | "url" | "email";
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  unit?: string;
  clearable?: boolean;
  copyable?: boolean;
  counter?: { value: number; max: number };
  onClear?: () => void;
  onCopy?: () => void;
};

export const AdvancedInput = React.forwardRef<HTMLInputElement, AdvancedInputProps>(
  (
    {
      className,
      type = "text",
      prefix,
      suffix,
      unit,
      clearable = false,
      copyable = false,
      counter,
      value,
      defaultValue,
      disabled,
      readOnly,
      onClear,
      onCopy,
      onChange,
      ...props
    },
    ref,
  ) => {
    const isControlled = value !== undefined;
    const [internalValue, setInternalValue] = React.useState(
      String(defaultValue ?? ""),
    );
    const currentValue = isControlled ? String(value ?? "") : internalValue;
    const showClear = clearable && currentValue.length > 0 && !disabled && !readOnly;

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      if (!isControlled) {
        setInternalValue(event.target.value);
      }
      onChange?.(event);
    };

    const handleClear = () => {
      if (!isControlled) {
        setInternalValue("");
      }
      onClear?.();
    };

  const resolvedPrefix =
    type === "search" && !prefix ? (
      <Search className="size-4 text-gray-400" aria-hidden="true" />
    ) : (
      prefix
    );

    return (
      <div className="space-y-1">
        <div
          className={cn(
            "flex h-11 w-full items-center gap-2 rounded-lg border border-gray-300 bg-transparent px-3 shadow-theme-xs transition-colors focus-within:border-brand-300 focus-within:ring-3 focus-within:ring-brand-500/20 dark:border-gray-700 dark:bg-gray-900 dark:focus-within:border-brand-800",
            disabled && "cursor-not-allowed opacity-40 bg-gray-100 dark:bg-gray-800",
            className,
          )}
        >
          {resolvedPrefix ? (
            <span className="shrink-0 text-gray-500 dark:text-gray-400">
              {resolvedPrefix}
            </span>
          ) : null}
          <Input
            ref={ref}
            type={type}
            value={value}
            defaultValue={defaultValue}
            disabled={disabled}
            readOnly={readOnly}
            onChange={handleChange}
            className="h-full min-w-0 flex-1 border-0 bg-transparent px-0 py-0 shadow-none focus-visible:ring-0"
            {...props}
          />
          {unit ? (
            <span className="shrink-0 text-sm text-gray-500 dark:text-gray-400">
              {unit}
            </span>
          ) : null}
          {suffix ? (
            <span className="shrink-0 text-gray-500 dark:text-gray-400">
              {suffix}
            </span>
          ) : null}
          {showClear ? (
            <button
              type="button"
              onClick={handleClear}
              className="inline-flex size-7 shrink-0 items-center justify-center rounded-md text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-white/5"
              aria-label="清空输入"
            >
              <X className="size-4" />
            </button>
          ) : null}
          {copyable ? (
            <button
              type="button"
              onClick={onCopy}
              className="inline-flex size-7 shrink-0 items-center justify-center rounded-md text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-white/5"
              aria-label="复制内容"
            >
              <Copy className="size-4" />
            </button>
          ) : null}
        </div>
        {counter ? (
          <p className="text-right text-xs text-gray-400">
            {counter.value}/{counter.max}
          </p>
        ) : null}
      </div>
    );
  },
);
AdvancedInput.displayName = "AdvancedInput";
