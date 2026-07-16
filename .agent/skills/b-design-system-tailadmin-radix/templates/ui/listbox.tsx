import * as React from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export type ListboxOption = {
  value: string;
  label: React.ReactNode;
  disabled?: boolean;
};

export type ListboxProps = {
  options: ListboxOption[];
  value: string | string[];
  onChange: (value: string | string[]) => void;
  multiple?: boolean;
  className?: string;
  "aria-label"?: string;
};

function normalizeValue(value: string | string[]): string[] {
  return Array.isArray(value) ? value : value ? [value] : [];
}

/**
 * 无 Trigger 的列表选择 — 筛选面板、侧栏多选。
 */
export function Listbox({
  options,
  value,
  onChange,
  multiple = false,
  className,
  "aria-label": ariaLabel,
}: ListboxProps) {
  const selected = normalizeValue(value);
  const [activeIndex, setActiveIndex] = React.useState(0);
  const listRef = React.useRef<HTMLUListElement>(null);

  const enabledIndexes = React.useMemo(
    () => options.map((option, index) => (option.disabled ? -1 : index)).filter((index) => index >= 0),
    [options],
  );

  const selectAt = (index: number) => {
    const option = options[index];
    if (!option || option.disabled) return;

    if (multiple) {
      const next = selected.includes(option.value)
        ? selected.filter((item) => item !== option.value)
        : [...selected, option.value];
      onChange(next);
      return;
    }

    onChange(option.value);
  };

  const moveActive = (direction: 1 | -1) => {
    if (enabledIndexes.length === 0) return;
    const currentPos = enabledIndexes.indexOf(activeIndex);
    const base = currentPos >= 0 ? currentPos : 0;
    const nextPos = (base + direction + enabledIndexes.length) % enabledIndexes.length;
    const nextIndex = enabledIndexes[nextPos] ?? 0;
    setActiveIndex(nextIndex);
    listRef.current
      ?.querySelector<HTMLElement>(`[data-listbox-index="${nextIndex}"]`)
      ?.scrollIntoView({ block: "nearest" });
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLUListElement>) => {
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        moveActive(1);
        break;
      case "ArrowUp":
        event.preventDefault();
        moveActive(-1);
        break;
      case "Home":
        event.preventDefault();
        if (enabledIndexes[0] != null) setActiveIndex(enabledIndexes[0]);
        break;
      case "End":
        event.preventDefault();
        if (enabledIndexes.at(-1) != null) setActiveIndex(enabledIndexes.at(-1)!);
        break;
      case "Enter":
      case " ":
        event.preventDefault();
        selectAt(activeIndex);
        break;
      default:
        break;
    }
  };

  return (
    <ul
      ref={listRef}
      role="listbox"
      aria-label={ariaLabel}
      aria-multiselectable={multiple || undefined}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className={cn(
        "max-h-64 overflow-y-auto rounded-xl border border-gray-200 bg-white p-1 outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
    >
      {options.map((option, index) => {
        const isSelected = selected.includes(option.value);
        const isActive = index === activeIndex;

        return (
          <li
            key={option.value}
            role="option"
            data-listbox-index={index}
            aria-selected={isSelected}
            aria-disabled={option.disabled || undefined}
            tabIndex={-1}
            onMouseEnter={() => !option.disabled && setActiveIndex(index)}
            onClick={() => selectAt(index)}
            className={cn(
              "flex cursor-default select-none items-center gap-2 rounded-lg px-3 py-2 text-theme-sm text-gray-700 dark:text-gray-300",
              isActive && "bg-gray-100 dark:bg-white/5",
              isSelected && "text-brand-700 dark:text-brand-400",
              option.disabled && "cursor-not-allowed opacity-50",
            )}
          >
            {multiple ? (
              <span
                className={cn(
                  "inline-flex size-4 shrink-0 items-center justify-center rounded border border-gray-300 dark:border-gray-600",
                  isSelected && "border-brand-500 bg-brand-500 text-white",
                )}
                aria-hidden
              >
                {isSelected ? <Check className="size-3" /> : null}
              </span>
            ) : null}
            <span className="min-w-0 flex-1 truncate">{option.label}</span>
          </li>
        );
      })}
    </ul>
  );
}
