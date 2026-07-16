import * as React from "react";
import { Check, ChevronDown, X } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

export type MultiSelectOption = {
  value: string;
  label: string;
  keywords?: string[];
};

export type MultiSelectProps = {
  label?: string;
  options: MultiSelectOption[];
  value?: string[];
  defaultValue?: string[];
  onValueChange?: (value: string[]) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  disabled?: boolean;
  className?: string;
  /** @alias limitTags — antd/PrimeVue 命名 */
  maxVisibleTags?: number;
  limitTags?: number;
};

export function MultiSelect({
  label,
  options,
  value,
  defaultValue = [],
  onValueChange,
  placeholder = "请选择选项",
  searchPlaceholder = "搜索选项...",
  emptyMessage = "没有找到选项。",
  disabled = false,
  className,
  maxVisibleTags: maxVisibleTagsProp,
  limitTags,
}: MultiSelectProps) {
  const maxVisibleTags = limitTags ?? maxVisibleTagsProp ?? 3;
  const isControlled = value !== undefined;
  const [internalValue, setInternalValue] = React.useState<string[]>(defaultValue);
  const selectedValues = isControlled ? value : internalValue;
  const [open, setOpen] = React.useState(false);
  const labelId = React.useId();

  const updateValue = (next: string[]) => {
    if (!isControlled) {
      setInternalValue(next);
    }
    onValueChange?.(next);
  };

  const toggleOption = (optionValue: string) => {
    const next = selectedValues.includes(optionValue)
      ? selectedValues.filter((item) => item !== optionValue)
      : [...selectedValues, optionValue];
    updateValue(next);
  };

  const removeOption = (optionValue: string) => {
    updateValue(selectedValues.filter((item) => item !== optionValue));
  };

  const clearAll = (event: React.MouseEvent) => {
    event.stopPropagation();
    if (!disabled) {
      updateValue([]);
    }
  };

  const selectedOptions = options.filter((option) =>
    selectedValues.includes(option.value),
  );
  const visibleOptions = selectedOptions.slice(0, maxVisibleTags);
  const hiddenCount = Math.max(selectedOptions.length - maxVisibleTags, 0);

  return (
    <div className={cn("w-full", className)}>
      {label ? (
        <label
          htmlFor={labelId}
          className="mb-1.5 block text-sm font-medium text-gray-700 dark:text-gray-400"
        >
          {label}
        </label>
      ) : null}

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            id={labelId}
            type="button"
            role="combobox"
            aria-expanded={open}
            aria-haspopup="listbox"
            aria-labelledby={label ? labelId : undefined}
            disabled={disabled}
            className={cn(
              "flex min-h-11 w-full items-start justify-between gap-2 rounded-lg border border-gray-300 bg-transparent px-3 py-1.5 text-left text-sm shadow-theme-xs transition-colors focus-visible:border-brand-300 focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 disabled:cursor-not-allowed disabled:opacity-40 disabled:bg-gray-100 dark:border-gray-700 dark:bg-gray-900 dark:focus-visible:border-brand-800 dark:disabled:bg-gray-800",
              open && "border-brand-300 ring-3 ring-brand-500/20 dark:border-brand-800",
            )}
          >
            <span className="flex flex-1 flex-wrap gap-2 py-0.5">
              {selectedOptions.length > 0 ? (
                <>
                  {visibleOptions.map((option) => (
                    <span
                      key={option.value}
                      className="group inline-flex max-w-full items-center rounded-full border border-transparent bg-gray-100 py-1 pl-2.5 pr-2 text-sm text-gray-800 hover:border-gray-200 dark:bg-gray-800 dark:text-white/90 dark:hover:border-gray-800"
                    >
                      <span className="truncate">{option.label}</span>
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          if (!disabled) {
                            removeOption(option.value);
                          }
                        }}
                        disabled={disabled}
                        className="ml-1 text-gray-500 hover:text-gray-400 disabled:cursor-not-allowed dark:text-gray-400"
                        aria-label={`移除 ${option.label}`}
                      >
                        <X className="size-3.5" aria-hidden />
                      </button>
                    </span>
                  ))}
                  {hiddenCount > 0 ? (
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-1 text-theme-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                      +{hiddenCount} 项
                    </span>
                  ) : null}
                </>
              ) : (
                <span className="px-1 py-1 text-gray-400 dark:text-gray-500">
                  {placeholder}
                </span>
              )}
            </span>

            <span className="flex shrink-0 items-center gap-1 self-start py-1">
              {selectedOptions.length > 0 ? (
                <button
                  type="button"
                  onClick={clearAll}
                  disabled={disabled}
                  className="text-gray-500 hover:text-gray-700 disabled:cursor-not-allowed dark:text-gray-400 dark:hover:text-gray-200"
                  aria-label="清空选择"
                >
                  <X className="size-4" aria-hidden />
                </button>
              ) : null}
              <ChevronDown
                className={cn(
                  "size-5 text-gray-700 transition-transform dark:text-gray-400",
                  open && "rotate-180",
                )}
                aria-hidden
              />
            </span>
          </button>
        </PopoverTrigger>

        <PopoverContent
          className="w-[var(--radix-popover-trigger-width)] p-0"
          align="start"
        >
          <Command>
            <CommandInput placeholder={searchPlaceholder} />
            <CommandList className="max-h-60">
              <CommandEmpty>{emptyMessage}</CommandEmpty>
              <CommandGroup>
                {options.map((option) => {
                  const isSelected = selectedValues.includes(option.value);
                  return (
                    <CommandItem
                      key={option.value}
                      value={[option.label, ...(option.keywords ?? [])].join(" ")}
                      onSelect={() => toggleOption(option.value)}
                      className="gap-2"
                    >
                      <span
                        className={cn(
                          "flex size-4 items-center justify-center rounded-sm border border-gray-300 dark:border-gray-700",
                          isSelected &&
                            "border-brand-500 bg-brand-500 text-white dark:border-brand-500",
                        )}
                      >
                        {isSelected ? <Check className="size-3" aria-hidden /> : null}
                      </span>
                      <span
                        className={cn(
                          isSelected
                            ? "text-brand-500"
                            : "text-gray-700 dark:text-gray-300",
                        )}
                      >
                        {option.label}
                      </span>
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
