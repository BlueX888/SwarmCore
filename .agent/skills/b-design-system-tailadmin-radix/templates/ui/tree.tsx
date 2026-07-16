import * as React from "react";
import { DndContext, closestCenter, type DragEndEvent } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { ChevronRight, GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";
import { Checkbox } from "@/components/ui/checkbox";
import { useSortableItem, useSortableList } from "@/lib/use-sortable-list";
import { HierarchicalTreeView } from "./hierarchical-picker/hierarchical-tree-view";
import { useHierarchicalPicker } from "./hierarchical-picker/use-hierarchical-picker";
import type { HierarchicalNode } from "./hierarchical-picker/types";

export type TreeNode = HierarchicalNode & { icon?: React.ReactNode };

export type TreeDropInfo = {
  dragKey: string;
  dropKey: string;
  dropPosition: -1 | 0 | 1;
};

export type TreeProps = {
  nodes: TreeNode[];
  selectedKeys?: string[];
  expandedKeys?: string[];
  onSelect?: (id: string, node: TreeNode) => void;
  onExpand?: (keys: string[]) => void;
  checkable?: boolean;
  checkedKeys?: string[];
  onCheck?: (keys: string[]) => void;
  draggable?: boolean;
  onDrop?: (info: TreeDropInfo) => void;
  className?: string;
};

function findTreeNode(nodes: TreeNode[], id: string): TreeNode | undefined {
  for (const node of nodes) {
    if (node.id === id) return node;
    if (node.children) {
      const found = findTreeNode(node.children as TreeNode[], id);
      if (found) return found;
    }
  }
  return undefined;
}

function mapNodesWithIcons(nodes: TreeNode[]): HierarchicalNode[] {
  return nodes.map((node) => ({
    id: node.id,
    label: node.icon ? (
      <span className="flex min-w-0 items-center gap-1.5">
        <span className="shrink-0">{node.icon}</span>
        <span className="truncate">{node.label}</span>
      </span>
    ) : (
      node.label
    ),
    disabled: node.disabled,
    isLeaf: node.isLeaf,
    children: node.children ? mapNodesWithIcons(node.children as TreeNode[]) : undefined,
  }));
}

type PickerState = ReturnType<typeof useHierarchicalPicker>;

function SortableTreeRow({
  node,
  depth,
  picker,
  checkable,
  selectedKeys,
  onSelect,
  onDrop,
}: {
  node: HierarchicalNode;
  depth: number;
  picker: PickerState;
  checkable?: boolean;
  selectedKeys: string[];
  onSelect?: (id: string, node: HierarchicalNode) => void;
  onDrop?: (info: TreeDropInfo) => void;
}) {
  const { attributes, listeners, setNodeRef, style, isDragging } = useSortableItem(node.id);
  const hasChildren = (node.children?.length ?? 0) > 0 || (!node.isLeaf && !node.children);
  const isExpanded = picker.expandedKeys.includes(node.id);
  const isSelected = selectedKeys.includes(node.id);
  const isChecked = picker.checkedKeys.includes(node.id);

  return (
    <>
      <div
        ref={setNodeRef}
        style={{ ...style, paddingLeft: `${depth * 12 + 8}px` }}
        className={cn(
          "flex w-full items-center gap-1.5 py-1.5 pr-2 text-left text-theme-sm",
          isSelected && "bg-brand-50/60 text-brand-700 dark:bg-brand-500/10 dark:text-brand-400",
          isDragging && "z-10 opacity-80 ring-2 ring-brand-500/20",
        )}
      >
        <button
          type="button"
          className="inline-flex size-5 shrink-0 cursor-grab items-center justify-center rounded text-gray-400 hover:text-brand-500 active:cursor-grabbing"
          aria-label={`拖拽 ${String(node.label)}`}
          {...attributes}
          {...listeners}
        >
          <GripVertical className="size-3.5" />
        </button>
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
            <ChevronRight className={cn("size-3.5 transition-transform", isExpanded && "rotate-90")} />
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
            onSelect?.(node.id, node);
          }}
          disabled={node.disabled || picker.disabled}
        >
          <span className="truncate">{node.label}</span>
        </button>
      </div>
      {hasChildren && isExpanded && node.children ? (
        <DraggableTreeLevel
          nodes={node.children}
          depth={depth + 1}
          picker={picker}
          checkable={checkable}
          selectedKeys={selectedKeys}
          onSelect={onSelect}
          onDrop={onDrop}
        />
      ) : null}
    </>
  );
}

function DraggableTreeLevel({
  nodes,
  depth,
  picker,
  checkable,
  selectedKeys,
  onSelect,
  onDrop,
}: {
  nodes: HierarchicalNode[];
  depth: number;
  picker: PickerState;
  checkable?: boolean;
  selectedKeys: string[];
  onSelect?: (id: string, node: HierarchicalNode) => void;
  onDrop?: (info: TreeDropInfo) => void;
}) {
  const getId = React.useCallback((node: HierarchicalNode) => node.id, []);
  const { sensors, ids, handleDragEnd: baseHandleDragEnd } = useSortableList({
    items: nodes,
    getId,
    onReorder: () => {},
  });

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = ids.indexOf(String(active.id));
    const newIndex = ids.indexOf(String(over.id));
    if (oldIndex === -1 || newIndex === -1) return;

    onDrop?.({
      dragKey: String(active.id),
      dropKey: String(over.id),
      dropPosition: newIndex > oldIndex ? 1 : -1,
    });

    baseHandleDragEnd(event);
  };

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={ids} strategy={verticalListSortingStrategy}>
        {nodes.map((node) => (
          <SortableTreeRow
            key={node.id}
            node={node}
            depth={depth}
            picker={picker}
            checkable={checkable}
            selectedKeys={selectedKeys}
            onSelect={onSelect}
            onDrop={onDrop}
          />
        ))}
      </SortableContext>
    </DndContext>
  );
}

function DraggableTreeView({
  picker,
  checkable,
  selectedKeys,
  onSelect,
  onDrop,
  className,
}: {
  picker: PickerState;
  checkable?: boolean;
  selectedKeys: string[];
  onSelect?: (id: string, node: HierarchicalNode) => void;
  onDrop?: (info: TreeDropInfo) => void;
  className?: string;
}) {
  return (
    <div className={cn("min-w-[200px]", className)} role="tree">
      <DraggableTreeLevel
        nodes={picker.nodes}
        depth={0}
        picker={picker}
        checkable={checkable}
        selectedKeys={selectedKeys}
        onSelect={onSelect}
        onDrop={onDrop}
      />
    </div>
  );
}

export function Tree({
  nodes,
  selectedKeys = [],
  expandedKeys: expandedKeysProp,
  onSelect,
  onExpand,
  checkable = false,
  checkedKeys = [],
  onCheck,
  draggable = false,
  onDrop,
  className,
}: TreeProps) {
  const hierarchicalNodes = React.useMemo(() => mapNodesWithIcons(nodes), [nodes]);

  const picker = useHierarchicalPicker({
    nodes: hierarchicalNodes,
    expandedKeys: expandedKeysProp,
    onExpandedKeysChange: onExpand,
    checkedKeys,
    onCheckedKeysChange: onCheck,
  });

  const handleSelect = (id: string) => {
    const node = findTreeNode(nodes, id);
    if (node) onSelect?.(id, node);
  };

  return (
    <div
      className={cn(
        "overflow-y-auto rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
    >
      {draggable ? (
        <DraggableTreeView
          picker={picker}
          checkable={checkable}
          selectedKeys={selectedKeys}
          onSelect={(id) => handleSelect(id)}
          onDrop={onDrop}
        />
      ) : (
        <HierarchicalTreeView
          picker={picker}
          checkable={checkable}
          selectedKeys={selectedKeys}
          onSelect={(id) => handleSelect(id)}
        />
      )}
    </div>
  );
}
