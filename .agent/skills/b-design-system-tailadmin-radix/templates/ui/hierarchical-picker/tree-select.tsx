import * as React from "react";
import { ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { HierarchicalTreeView } from "./hierarchical-tree-view";
import { useHierarchicalPicker } from "./use-hierarchical-picker";
import type { CheckStrategy, HierarchicalNode, LoadDataFn } from "./types";

type InputSkin = "outlined" | "filled" | "borderless" | "underlined";

export type TreeSelectProps = {
  treeData: HierarchicalNode[];
  value?: string | string[];
  onChange?: (value: string | string[]) => void;
  treeCheckable?: boolean;
  showCheckedStrategy?: CheckStrategy;
  loadData?: LoadDataFn;
  showSearch?: boolean;
  placeholder?: string;
  disabled?: boolean;
  inputSkin?: InputSkin;
  className?: string;
};

function normalizeValue(value: string | string[] | undefined, multiple: boolean): string[] {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}

function findNodeLabel(nodes: HierarchicalNode[], id: string): React.ReactNode {
  for (const node of nodes) {
    if (node.id === id) return node.label;
    if (node.children) {
      const label = findNodeLabel(node.children, id);
      if (label) return label;
    }
  }
  return id;
}

const triggerSkinClasses: Record<InputSkin, string> = {
  outlined: "",
  filled: "bg-gray-100 dark:bg-white/5",
  borderless: "border-transparent bg-transparent shadow-none",
  underlined: "rounded-none border-0 border-b px-0",
};

export function TreeSelect({
  treeData,
  value,
  onChange,
  treeCheckable = false,
  showCheckedStrategy = "child",
  loadData,
  showSearch = false,
  placeholder = "请选择…",
  disabled = false,
  inputSkin = "outlined",
  className,
}: TreeSelectProps) {
  const [open, setOpen] = React.useState(false);
  const multiple = treeCheckable;
  const selected = normalizeValue(value, multiple);

  const picker = useHierarchicalPicker({
    nodes: treeData,
    checkedKeys: treeCheckable ? selected : undefined,
    onCheckedKeysChange: treeCheckable
      ? (keys) => {
          onChange?.(keys);
        }
      : undefined,
    checkStrategy: showCheckedStrategy,
    loadData,
    showSearch,
    disabled,
  });

  const displayContent = React.useMemo(() => {
    if (selected.length === 0) return placeholder;
    if (treeCheckable) {
      return (
        <span className="flex min-w-0 flex-1 flex-wrap items-center gap-1">
          {selected.map((key) => (
            <Chip key={key} size="sm" color="neutral" variant="outlined">
              {findNodeLabel(treeData, key)}
            </Chip>
          ))}
        </span>
      );
    }
    return findNodeLabel(treeData, selected[0]);
  }, [selected, placeholder, treeCheckable, treeData]);

  const handleSelect = (id: string) => {
    if (treeCheckable) return;
    onChange?.(id);
    setOpen(false);
  };

  const handleOpenChange = (next: boolean) => {
    if (disabled) return;
    setOpen(next);
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
            "h-11 w-full justify-between font-normal",
            triggerSkinClasses[inputSkin],
            className,
          )}
        >
          <span className={cn("truncate", selected.length === 0 && "text-gray-400 dark:text-gray-500")}>
            {displayContent}
          </span>
          <ChevronsUpDown className="ml-2 size-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-2" align="start">
        {showSearch ? (
          <div className="mb-2">
            <Input
              inputSkin="borderless"
              placeholder="搜索…"
              value={picker.searchQuery}
              onChange={(e) => picker.setSearchQuery(e.target.value)}
              className="h-9"
            />
          </div>
        ) : null}
        <HierarchicalTreeView
          picker={picker}
          checkable={treeCheckable}
          selectedKeys={treeCheckable ? [] : selected}
          onSelect={handleSelect}
        />
      </PopoverContent>
    </Popover>
  );
}
