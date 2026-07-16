import * as React from "react";
import { DndContext, closestCenter } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSortableItem, useSortableList } from "@/lib/use-sortable-list";

export type OrderListProps<T> = {
  items: T[];
  getId: (item: T) => string;
  renderItem: (item: T, index: number) => React.ReactNode;
  onReorder: (items: T[]) => void;
  className?: string;
};

function SortableOrderListItem({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  const { attributes, listeners, setNodeRef, style, isDragging } = useSortableItem(id);

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={cn(
        "flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 shadow-theme-xs dark:border-gray-800 dark:bg-white/[0.03]",
        isDragging && "z-10 opacity-80 ring-2 ring-brand-500/20",
      )}
    >
      <button
        type="button"
        className="inline-flex size-8 shrink-0 cursor-grab items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 active:cursor-grabbing dark:hover:bg-white/5 dark:hover:text-gray-300"
        aria-label="拖拽排序"
        {...attributes}
        {...listeners}
      >
        <GripVertical className="size-4" />
      </button>
      <div className="min-w-0 flex-1">{children}</div>
    </li>
  );
}

/**
 * 单栏垂直排序列表 — 功能开关优先级、菜单排序等场景。
 */
export function OrderList<T>({
  items,
  getId,
  renderItem,
  onReorder,
  className,
}: OrderListProps<T>) {
  const { sensors, ids, handleDragEnd } = useSortableList({ items, getId, onReorder });

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={ids} strategy={verticalListSortingStrategy}>
        <ul className={cn("flex flex-col gap-2", className)} role="list">
          {items.map((item, index) => {
            const id = getId(item);
            return (
              <SortableOrderListItem key={id} id={id}>
                {renderItem(item, index)}
              </SortableOrderListItem>
            );
          })}
        </ul>
      </SortableContext>
    </DndContext>
  );
}
