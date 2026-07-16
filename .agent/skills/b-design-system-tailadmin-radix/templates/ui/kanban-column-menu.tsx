import * as React from "react";
import { MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  kanbanColumnMenuClass,
  kanbanColumnMenuItemClass,
} from "@/lib/kanban-theme";

export type KanbanColumnMenuAction = "edit" | "delete" | "clearAll";

export type KanbanColumnMenuItem = {
  id: KanbanColumnMenuAction;
  label: string;
  onSelect?: () => void;
};

export type KanbanColumnMenuProps = {
  items?: KanbanColumnMenuItem[];
  onEdit?: () => void;
  onDelete?: () => void;
  onClearAll?: () => void;
  onOpenChange?: (open: boolean) => void;
  triggerClassName?: string;
  contentClassName?: string;
  "aria-label"?: string;
};

const DEFAULT_ITEMS: KanbanColumnMenuItem[] = [
  { id: "edit", label: "Edit" },
  { id: "delete", label: "Delete" },
  { id: "clearAll", label: "Clear All" },
];

export function KanbanColumnMenu({
  items = DEFAULT_ITEMS,
  onEdit,
  onDelete,
  onClearAll,
  onOpenChange,
  triggerClassName,
  contentClassName,
  "aria-label": ariaLabel = "Column actions",
}: KanbanColumnMenuProps) {
  const [open, setOpen] = React.useState(false);

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    onOpenChange?.(nextOpen);
  };

  const actionHandlers: Record<KanbanColumnMenuAction, (() => void) | undefined> = {
    edit: onEdit,
    delete: onDelete,
    clearAll: onClearAll,
  };

  const handleSelect = (item: KanbanColumnMenuItem) => {
    item.onSelect?.();
    actionHandlers[item.id]?.();
    handleOpenChange(false);
  };

  return (
    <DropdownMenu open={open} onOpenChange={handleOpenChange}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className={cn(
            "inline-flex items-center justify-center rounded-lg text-gray-400 transition-colors hover:text-gray-700 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500/20 dark:hover:text-gray-300",
            triggerClassName,
          )}
          aria-label={ariaLabel}
        >
          <MoreHorizontal className="size-6" aria-hidden />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        sideOffset={4}
        className={cn(kanbanColumnMenuClass, "p-2", contentClassName)}
      >
        {items.map((item) => (
          <DropdownMenuItem
            key={item.id}
            onSelect={() => handleSelect(item)}
            className={cn(kanbanColumnMenuItemClass, "px-3 py-2")}
          >
            {item.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
