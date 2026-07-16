import * as React from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Checkbox } from "@/components/ui/checkbox";
import { Spinner } from "@/components/ui/spinner";
import type { HierarchicalNode } from "./types";
import type { useHierarchicalPicker } from "./use-hierarchical-picker";

type PickerState = ReturnType<typeof useHierarchicalPicker>;

export type HierarchicalTreeViewProps = {
  picker: PickerState;
  checkable?: boolean;
  selectedKeys?: string[];
  onSelect?: (id: string, node: HierarchicalNode) => void;
  className?: string;
};

function TreeRow({
  node,
  depth,
  picker,
  checkable,
  selectedKeys,
  onSelect,
}: {
  node: HierarchicalNode;
  depth: number;
  picker: PickerState;
  checkable?: boolean;
  selectedKeys: string[];
  onSelect?: (id: string, node: HierarchicalNode) => void;
}) {
  const hasChildren = (node.children?.length ?? 0) > 0 || (!node.isLeaf && !node.children);
  const isExpanded = picker.expandedKeys.includes(node.id);
  const isLoading = picker.loadingKeys.has(node.id);
  const isSelected = selectedKeys.includes(node.id);
  const isChecked = picker.checkedKeys.includes(node.id);

  return (
    <>
      <div
        className={cn(
          "flex w-full items-center gap-1.5 py-1.5 pr-2 text-left text-theme-sm",
          isSelected && "bg-brand-50/60 text-brand-700 dark:bg-brand-500/10 dark:text-brand-400",
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {checkable ? (
          <Checkbox
            checked={isChecked}
            disabled={node.disabled || picker.disabled}
            onCheckedChange={() => picker.toggleCheck(node)}
            aria-label={`选择 ${String(node.label)}`}
          />
        ) : null}
        {hasChildren ? (
          <button
            type="button"
            className="inline-flex size-5 shrink-0 items-center justify-center rounded text-gray-400 hover:text-brand-500"
            onClick={() => picker.toggleExpand(node)}
            aria-expanded={isExpanded}
            disabled={node.disabled || picker.disabled}
          >
            {isLoading ? (
              <Spinner className="size-3" />
            ) : (
              <ChevronRight className={cn("size-3.5 transition-transform", isExpanded && "rotate-90")} />
            )}
          </button>
        ) : (
          <span className="inline-block size-5 shrink-0" aria-hidden />
        )}
        <button
          type="button"
          className={cn(
            "flex min-w-0 flex-1 items-center gap-1.5 truncate text-left hover:text-brand-600 dark:hover:text-brand-400",
            node.disabled && "cursor-not-allowed opacity-50",
          )}
          onClick={() => {
            if (node.disabled || picker.disabled) return;
            const hasChildNodes = (node.children?.length ?? 0) > 0;
            if (hasChildNodes) void picker.toggleExpand(node);
            onSelect?.(node.id, node);
          }}
          disabled={node.disabled || picker.disabled}
        >
          <span className="truncate">{node.label}</span>
        </button>
      </div>
      {hasChildren && isExpanded
        ? node.children?.map((child) => (
            <TreeRow
              key={child.id}
              node={child}
              depth={depth + 1}
              picker={picker}
              checkable={checkable}
              selectedKeys={selectedKeys}
              onSelect={onSelect}
            />
          ))
        : null}
    </>
  );
}

export function HierarchicalTreeView({
  picker,
  checkable = false,
  selectedKeys = [],
  onSelect,
  className,
}: HierarchicalTreeViewProps) {
  return (
    <div className={cn("min-w-[200px]", className)} role="tree">
      {picker.nodes.map((node) => (
        <TreeRow
          key={node.id}
          node={node}
          depth={0}
          picker={picker}
          checkable={checkable}
          selectedKeys={selectedKeys}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
