import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Chip } from "@/components/ui/chip";
import { Spinner } from "@/components/ui/spinner";

export type AutocompleteOption = {
  value: string;
  label: React.ReactNode;
  disabled?: boolean;
};

export type AutocompleteVirtualConfig = {
  itemHeight: number;
  overscan?: number;
};

export type AutocompleteProps = {
  options: AutocompleteOption[];
  value?: string | string[];
  onValueChange?: (value: string | string[]) => void;
  multiple?: boolean;
  freeSolo?: boolean;
  loading?: boolean;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyText?: string;
  onSearch?: (query: string) => void;
  disabled?: boolean;
  className?: string;
  groupBy?: (option: AutocompleteOption) => string;
  virtual?: AutocompleteVirtualConfig;
  limitTags?: number;
  renderLimitTags?: (omittedCount: number) => React.ReactNode;
};

const AutocompleteVirtualList = React.lazy(() =>
  import("@/components/ui/autocomplete-virtual-list").then((module) => ({
    default: module.AutocompleteVirtualList,
  })),
);

function normalizeValue(value: string | string[] | undefined, multiple: boolean): string[] {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}

function groupOptions(
  options: AutocompleteOption[],
  groupBy: (option: AutocompleteOption) => string,
): [string, AutocompleteOption[]][] {
  const groups = new Map<string, AutocompleteOption[]>();
  for (const option of options) {
    const heading = groupBy(option);
    const bucket = groups.get(heading);
    if (bucket) {
      bucket.push(option);
    } else {
      groups.set(heading, [option]);
    }
  }
  return Array.from(groups.entries());
}

function renderOptionItem(
  option: AutocompleteOption,
  selected: string[],
  toggleOption: (value: string) => void,
) {
  const isSelected = selected.includes(option.value);
  return (
    <CommandItem
      key={option.value}
      value={option.value}
      disabled={option.disabled}
      onSelect={() => toggleOption(option.value)}
    >
      <Check className={cn("size-4", isSelected ? "opacity-100" : "opacity-0")} />
      {option.label}
    </CommandItem>
  );
}

export function Autocomplete({
  options,
  value,
  onValueChange,
  multiple = false,
  freeSolo = false,
  loading = false,
  placeholder = "请选择…",
  searchPlaceholder = "搜索…",
  emptyText = "无匹配结果",
  onSearch,
  disabled = false,
  className,
  groupBy,
  virtual,
  limitTags,
  renderLimitTags,
}: AutocompleteProps) {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const listRef = React.useRef<HTMLDivElement>(null);
  const selected = normalizeValue(value, multiple);

  const optionMap = React.useMemo(
    () => new Map(options.map((option) => [option.value, option])),
    [options],
  );

  const groupedOptions = React.useMemo(
    () => (groupBy ? groupOptions(options, groupBy) : null),
    [groupBy, options],
  );

  const displayLabel = React.useMemo(() => {
    if (selected.length === 0) return placeholder;
    if (!multiple) return optionMap.get(selected[0])?.label ?? selected[0];
    return null;
  }, [multiple, optionMap, placeholder, selected]);

  const renderMultipleTags = () => {
    if (selected.length === 0) {
      return <span className="truncate text-gray-400">{placeholder}</span>;
    }

    const visibleKeys =
      limitTags != null && limitTags >= 0 ? selected.slice(0, limitTags) : selected;
    const omittedCount =
      limitTags != null && limitTags >= 0 ? Math.max(selected.length - limitTags, 0) : 0;

    return (
      <span className="flex min-w-0 flex-1 flex-wrap items-center gap-1">
        {visibleKeys.map((key) => (
          <Chip key={key} size="sm" color="neutral" variant="filled">
            {optionMap.get(key)?.label ?? key}
          </Chip>
        ))}
        {omittedCount > 0
          ? (renderLimitTags?.(omittedCount) ?? (
              <Chip size="sm" color="neutral" variant="outlined">
                +{omittedCount}
              </Chip>
            ))
          : null}
      </span>
    );
  };

  const commitValue = (next: string[]) => {
    if (multiple) {
      onValueChange?.(next);
      return;
    }
    onValueChange?.(next[0] ?? "");
    setOpen(false);
  };

  const toggleOption = (optionValue: string) => {
    if (multiple) {
      const exists = selected.includes(optionValue);
      commitValue(exists ? selected.filter((item) => item !== optionValue) : [...selected, optionValue]);
      return;
    }
    commitValue([optionValue]);
  };

  const handleQueryChange = (next: string) => {
    setQuery(next);
    onSearch?.(next);
  };

  const handleOpenChange = (next: boolean) => {
    if (disabled) return;
    setOpen(next);
    if (!next && freeSolo && query.trim() && !multiple) {
      onValueChange?.(query.trim());
    }
  };

  const renderOptionsList = () => {
    if (virtual) {
      return (
        <React.Suspense
          fallback={
            <div className="flex items-center justify-center py-6 text-sm text-gray-500">加载列表…</div>
          }
        >
          <AutocompleteVirtualList
            options={options}
            selected={selected}
            itemHeight={virtual.itemHeight}
            overscan={virtual.overscan}
            onToggle={toggleOption}
            scrollElementRef={listRef}
          />
        </React.Suspense>
      );
    }

    if (groupedOptions) {
      return groupedOptions.map(([heading, items]) => (
        <CommandGroup key={heading} heading={heading}>
          {items.map((option) => renderOptionItem(option, selected, toggleOption))}
        </CommandGroup>
      ));
    }

    return (
      <CommandGroup>
        {options.map((option) => renderOptionItem(option, selected, toggleOption))}
      </CommandGroup>
    );
  };

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            "h-auto min-h-11 w-full justify-between gap-2 py-2 font-normal",
            multiple && selected.length > 0 && "items-start",
            className,
          )}
        >
          {multiple ? renderMultipleTags() : <span className="truncate">{displayLabel}</span>}
          <ChevronsUpDown className="ml-2 size-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
        <Command shouldFilter={!onSearch}>
          <CommandInput
            placeholder={searchPlaceholder}
            value={query}
            onValueChange={handleQueryChange}
          />
          <CommandList ref={listRef}>
            {loading ? (
              <div className="flex items-center justify-center gap-2 py-6 text-sm text-gray-500">
                <Spinner size="sm" aria-label="加载中" />
                加载中…
              </div>
            ) : (
              <CommandEmpty>{emptyText}</CommandEmpty>
            )}
            {renderOptionsList()}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
