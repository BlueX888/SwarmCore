import * as React from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Chip } from "@/components/ui/chip";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Spinner } from "@/components/ui/spinner";
import type { HierarchicalNode, HierarchicalPath, LoadDataFn } from "./types";
import { useHierarchicalPicker } from "./use-hierarchical-picker";

type InputSkin = "outlined" | "filled" | "borderless" | "underlined";

export type CascaderProps = {
  options: HierarchicalNode[];
  value?: string[];
  onChange?: (path: string[]) => void;
  loadData?: LoadDataFn;
  multiple?: boolean;
  changeOnSelect?: boolean;
  showSearch?: boolean;
  placeholder?: string;
  disabled?: boolean;
  inputSkin?: InputSkin;
  className?: string;
};

const triggerSkinClasses: Record<InputSkin, string> = {
  outlined:
    "rounded-lg border border-gray-300 bg-transparent shadow-theme-xs dark:border-gray-700 dark:bg-gray-900",
  filled: "rounded-lg border border-transparent bg-gray-100 shadow-none dark:bg-white/5",
  borderless: "rounded-lg border border-transparent bg-transparent shadow-none",
  underlined: "rounded-none border-0 border-b bg-transparent px-0 shadow-none border-b-gray-300 dark:border-b-gray-700",
};

function getPathLabel(nodes: HierarchicalNode[], path: string[]): string {
  const labels: string[] = [];
  let current = nodes;
  for (const id of path) {
    const node = current.find((n) => n.id === id);
    if (!node) break;
    labels.push(typeof node.label === "string" ? node.label : String(node.label));
    current = node.children ?? [];
  }
  return labels.join(" / ");
}

function buildColumns(nodes: HierarchicalNode[], activePath: string[]): HierarchicalNode[][] {
  const columns: HierarchicalNode[][] = [nodes];
  let current = nodes;
  for (const id of activePath) {
    const node = current.find((n) => n.id === id);
    if (!node) break;
    const children = node.children ?? [];
    if (children.length > 0) {
      columns.push(children);
      current = children;
    } else {
      break;
    }
  }
  return columns;
}

function CascaderColumn({
  items,
  activeId,
  onSelect,
  loadingId,
}: {
  items: HierarchicalNode[];
  activeId?: string;
  onSelect: (node: HierarchicalNode) => void;
  loadingId?: string;
}) {
  return (
    <div className="w-[160px] shrink-0 border-r border-gray-200 last:border-r-0 dark:border-gray-800">
      <ScrollArea className="h-[220px]">
        <ul className="p-1">
          {items.map((item) => {
            const hasChildren = (item.children?.length ?? 0) > 0 || (!item.isLeaf && !item.children);
            const isActive = activeId === item.id;
            return (
              <li key={item.id}>
                <button
                  type="button"
                  disabled={item.disabled}
                  className={cn(
                    "flex w-full items-center justify-between gap-1 rounded-lg px-3 py-2 text-left text-sm transition-colors",
                    isActive && "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-400",
                    !isActive && "hover:bg-gray-50 dark:hover:bg-white/5",
                    item.disabled && "cursor-not-allowed opacity-50",
                  )}
                  onClick={() => onSelect(item)}
                >
                  <span className="truncate">{item.label}</span>
                  {loadingId === item.id ? (
                    <Spinner className="size-3.5 shrink-0" />
                  ) : hasChildren ? (
                    <ChevronRight className="size-3.5 shrink-0 text-gray-400" />
                  ) : null}
                </button>
              </li>
            );
          })}
        </ul>
      </ScrollArea>
    </div>
  );
}

export function Cascader({
  options,
  value = [],
  onChange,
  loadData,
  multiple = false,
  changeOnSelect = false,
  showSearch = false,
  placeholder = "请选择…",
  disabled = false,
  inputSkin = "outlined",
  className,
}: CascaderProps) {
  const [open, setOpen] = React.useState(false);
  const [activePath, setActivePath] = React.useState<string[]>(value);
  const [selectedPaths, setSelectedPaths] = React.useState<HierarchicalPath[]>(multiple ? [value].filter((p) => p.length > 0) : []);
  const [loadingId, setLoadingId] = React.useState<string | null>(null);
  const [loadedChildren, setLoadedChildren] = React.useState<Map<string, HierarchicalNode[]>>(new Map());

  const picker = useHierarchicalPicker({
    nodes: options,
    showSearch,
    loadData,
    disabled,
  });

  React.useEffect(() => {
    if (open) setActivePath(value);
  }, [open, value]);

  const mergeLoaded = React.useCallback(
    (nodes: HierarchicalNode[]): HierarchicalNode[] =>
      nodes.map((node) => {
        const loaded = loadedChildren.get(node.id);
        const children = loaded ?? node.children;
        return children ? { ...node, children: mergeLoaded(children) } : node;
      }),
    [loadedChildren],
  );

  const displayOptions = React.useMemo(() => mergeLoaded(options), [options, mergeLoaded]);
  const columns = React.useMemo(() => buildColumns(displayOptions, activePath), [displayOptions, activePath]);

  const commitPath = (path: string[]) => {
    if (multiple) {
      const exists = selectedPaths.some((p) => p.join("/") === path.join("/"));
      const next = exists ? selectedPaths : [...selectedPaths, path];
      setSelectedPaths(next);
      onChange?.(path);
      return;
    }
    onChange?.(path);
    setOpen(false);
  };

  const handleItemSelect = async (columnIndex: number, node: HierarchicalNode) => {
    if (disabled || node.disabled) return;
    const path = [...activePath.slice(0, columnIndex), node.id];
    setActivePath(path);

    const hasChildren = (node.children?.length ?? 0) > 0;
    const isLeaf = node.isLeaf || (!hasChildren && !loadData);

    if (!hasChildren && loadData && !node.isLeaf) {
      setLoadingId(node.id);
      try {
        const children = await loadData(node);
        setLoadedChildren((prev) => new Map(prev).set(node.id, children));
        if (children.length === 0) commitPath(path);
      } finally {
        setLoadingId(null);
      }
      return;
    }

    if (isLeaf || changeOnSelect) {
      commitPath(path);
    }
  };

  const displayLabel = React.useMemo(() => {
    if (multiple) {
      if (selectedPaths.length === 0) return placeholder;
      return null;
    }
    if (value.length === 0) return placeholder;
    return getPathLabel(displayOptions, value);
  }, [multiple, selectedPaths.length, placeholder, value, displayOptions]);

  const removePath = (index: number) => {
    const next = selectedPaths.filter((_, i) => i !== index);
    setSelectedPaths(next);
    onChange?.(next[next.length - 1] ?? []);
  };

  const handleOpenChange = (next: boolean) => {
    if (disabled) return;
    setOpen(next);
    if (next) setActivePath(value);
  };

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <button
          type="button"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            "flex h-11 w-full items-center justify-between gap-2 px-4 py-2.5 text-sm text-gray-800 transition-colors focus:outline-hidden focus:border-brand-300 focus:ring-3 focus:ring-brand-500/20 disabled:cursor-not-allowed disabled:opacity-40 dark:text-white/90 dark:focus:border-brand-800",
            triggerSkinClasses[inputSkin],
            className,
          )}
        >
          {multiple && selectedPaths.length > 0 ? (
            <span className="flex min-w-0 flex-1 flex-wrap items-center gap-1">
              {selectedPaths.map((path, index) => (
                <Chip
                  key={path.join("/")}
                  size="sm"
                  color="neutral"
                  variant="outlined"
                  onDelete={() => removePath(index)}
                >
                  {getPathLabel(displayOptions, path)}
                </Chip>
              ))}
            </span>
          ) : (
            <span className={cn("truncate", value.length === 0 && !multiple && "text-gray-400 dark:text-gray-500")}>
              {displayLabel}
            </span>
          )}
          <ChevronDown className="size-4 shrink-0 opacity-50" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        {showSearch ? (
          <div className="border-b border-gray-200 p-2 dark:border-gray-800">
            <Input
              inputSkin="borderless"
              placeholder="搜索…"
              value={picker.searchQuery}
              onChange={(e) => picker.setSearchQuery(e.target.value)}
              className="h-9"
            />
          </div>
        ) : null}
        <div className="flex">
          {(showSearch && picker.searchQuery.trim() ? [picker.nodes] : columns).map((column, columnIndex) => (
            <CascaderColumn
              key={columnIndex}
              items={column}
              activeId={activePath[columnIndex]}
              loadingId={loadingId ?? undefined}
              onSelect={(node) => handleItemSelect(columnIndex, node)}
            />
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
