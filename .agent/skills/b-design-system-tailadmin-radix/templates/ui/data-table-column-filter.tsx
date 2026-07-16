import * as React from "react";
import { Filter } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type ColumnFilterConfig =
  | { type: "select"; options: { label: string; value: string }[] }
  | { type: "text"; placeholder?: string };

export type DataTableColumnFilterProps = {
  config: ColumnFilterConfig;
  value?: unknown;
  onApply: (value: unknown) => void;
  /** 用于 filter 按钮 aria-label */
  columnTitle?: React.ReactNode;
};

function isFilterActive(value: unknown): boolean {
  return value !== undefined && value !== null && value !== "";
}

export function DataTableColumnFilter({
  config,
  value,
  onApply,
  columnTitle,
}: DataTableColumnFilterProps) {
  const [open, setOpen] = React.useState(false);
  const [draft, setDraft] = React.useState(() =>
    value == null ? "" : String(value),
  );

  React.useEffect(() => {
    if (open) {
      setDraft(value == null ? "" : String(value));
    }
  }, [open, value]);

  const active = isFilterActive(value);

  const handleApply = () => {
    onApply(draft === "" ? undefined : draft);
    setOpen(false);
  };

  const handleReset = () => {
    onApply(undefined);
    setDraft("");
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="inline-flex size-6 shrink-0 items-center justify-center rounded-md text-gray-400 transition-colors hover:bg-gray-100 hover:text-brand-500 dark:hover:bg-white/5 dark:hover:text-brand-400"
          aria-label={`筛选${columnTitle != null ? String(columnTitle) : "列"}${
            active ? "，已启用" : ""
          }`}
        >
          <Filter
            className={cn("size-3.5", active && "text-brand-500 dark:text-brand-400")}
            aria-hidden
          />
        </button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-64 p-3">
        <div className="grid gap-3">
          {config.type === "select" ? (
            <Select value={draft || undefined} onValueChange={setDraft}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="选择筛选值" />
              </SelectTrigger>
              <SelectContent>
                {config.options.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <Input
              size="sm"
              value={draft}
              placeholder={config.placeholder ?? "输入筛选值"}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  handleApply();
                }
              }}
            />
          )}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={handleReset}>
              重置
            </Button>
            <Button type="button" size="sm" onClick={handleApply}>
              确定
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
