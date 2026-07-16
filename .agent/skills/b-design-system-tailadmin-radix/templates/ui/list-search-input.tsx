import { useEffect, useRef, type ReactNode } from "react";
import { Input } from "@/components/ui/input";
import { useDebouncedValue } from "@/lib/use-debounced-value";
import { cn } from "@/lib/utils";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSearch: (value: string) => void;
  placeholder: string;
  disabled?: boolean;
  className?: string;
  suffix?: ReactNode;
  "aria-label"?: string;
};

export function ListSearchInput({
  value,
  onChange,
  onSearch,
  placeholder,
  disabled,
  className,
  suffix,
  "aria-label": ariaLabel = "搜索",
}: Props) {
  const debounced = useDebouncedValue(value, 300);
  const prevDebounced = useRef(debounced);

  useEffect(() => {
    if (prevDebounced.current === debounced) return;
    prevDebounced.current = debounced;
    onSearch(debounced.trim());
  }, [debounced, onSearch]);

  const input = (
    <Input
      type="search"
      value={value}
      disabled={disabled}
      placeholder={placeholder}
      aria-label={ariaLabel}
      className={cn(
        "h-11 max-w-sm min-w-0 flex-1",
        suffix && "max-w-none w-full pr-11",
        className,
      )}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          onSearch(value.trim());
        }
      }}
    />
  );

  if (!suffix) return input;

  return (
    <div className="relative max-w-sm min-w-0 flex-1">
      {input}
      <div className="absolute inset-y-0 right-1 flex items-center border-l border-gray-200 pl-1 dark:border-gray-800">
        {suffix}
      </div>
    </div>
  );
}
