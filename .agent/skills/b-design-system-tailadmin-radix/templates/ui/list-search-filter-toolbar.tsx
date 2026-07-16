import { useState } from "react";
import { Filter } from "lucide-react";
import { ListFilterPanel } from "@/components/ui/list-filter-panel";
import type { ListFilterConfig, ListSearchConfig } from "@/components/ui/list-filter-types";
import { countActiveFilters } from "@/components/ui/list-filter-utils";
import { ListSearchInput } from "@/components/ui/list-search-input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Props = {
  search?: ListSearchConfig;
  filter?: ListFilterConfig;
  disabled?: boolean;
  className?: string;
};

export function ListSearchFilterToolbar({ search, filter, disabled, className }: Props) {
  const [open, setOpen] = useState(false);
  const activeCount = filter ? countActiveFilters(filter.fields, filter.values) : 0;
  const showFilter = Boolean(filter && filter.fields.length > 0);

  const filterTrigger = showFilter ? (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      disabled={disabled}
      className="relative size-8 shrink-0 p-0"
      aria-label={activeCount > 0 ? `筛选（${activeCount} 项已选）` : "筛选"}
      onClick={filter?.panel === "drawer" ? () => setOpen(true) : undefined}
    >
      <Filter
        className={cn(
          "size-4",
          activeCount > 0 ? "text-brand-500" : "text-gray-500 dark:text-gray-400",
        )}
        aria-hidden
      />
      {activeCount > 0 ? (
        <span
          className="absolute -bottom-0.5 -right-0.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full border border-white bg-brand-50 px-0.5 text-[9px] font-medium leading-none text-brand-600 dark:border-gray-900 dark:bg-brand-500/15 dark:text-brand-400"
          aria-hidden
        >
          {activeCount > 9 ? "9+" : activeCount}
        </span>
      ) : null}
    </Button>
  ) : null;

  const filterPanel =
    showFilter && filter ? (
      <ListFilterPanel
        open={open}
        onOpenChange={setOpen}
        fields={filter.fields}
        values={filter.values}
        onApply={filter.onApply}
        panel={filter.panel}
        disabled={disabled}
        trigger={filterTrigger}
      />
    ) : null;

  return (
    <div className={cn("flex min-w-0 flex-1 items-center", className)}>
      {search ? (
        <ListSearchInput
          value={search.value}
          onChange={search.onChange}
          onSearch={search.onSearch}
          placeholder={search.placeholder}
          disabled={disabled}
          suffix={filterPanel}
        />
      ) : (
        filterPanel
      )}
    </div>
  );
}
