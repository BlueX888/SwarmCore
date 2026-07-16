/** TailAdmin Kanban theme — align token-index semantic colors */

export type KanbanStatus = "todo" | "inProgress" | "completed";

export type KanbanCategoryColor =
  | "brand"
  | "success"
  | "orange"
  | "error"
  | "purple"
  | "default";

export const kanbanBoardGridClass =
  "grid grid-cols-1 border-t border-gray-200 divide-x divide-gray-200 dark:divide-white/[0.05] mt-7 dark:border-white/[0.05] sm:mt-0 sm:grid-cols-2 xl:grid-cols-3";

export const kanbanColumnClass =
  "flex flex-col gap-5 p-4 swim-lane xl:p-6 transition-all duration-200 relative";

export const kanbanTaskCardClass =
  "relative p-5 bg-white border border-gray-200 task rounded-xl shadow-theme-sm dark:border-gray-800 dark:bg-white/5";

export const kanbanColumnTitleClass =
  "flex items-center gap-3 text-base font-medium text-gray-800 dark:text-white/90";

const columnCountBadgeMap: Record<KanbanStatus, string> = {
  todo: "bg-gray-100 text-gray-700 dark:bg-white/[0.03] dark:text-white/80",
  inProgress:
    "text-warning-700 bg-warning-50 dark:bg-warning-500/15 dark:text-orange-400",
  completed:
    "bg-success-50 text-success-700 dark:bg-success-500/15 dark:text-success-500",
};

const categoryColorMap: Record<KanbanCategoryColor, string> = {
  brand: "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-400",
  success:
    "bg-success-50 text-success-700 dark:bg-success-500/15 dark:text-success-400",
  orange:
    "bg-orange-50 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400",
  error:
    "bg-error-50 text-error-700 dark:bg-error-500/15 dark:text-error-400",
  purple:
    "bg-purple-50 text-purple-700 dark:bg-purple-500/15 dark:text-purple-400",
  default:
    "bg-gray-100 text-gray-700 dark:bg-gray-500/15 dark:text-gray-400",
};

export function getColumnCountBadgeClass(status: KanbanStatus): string {
  return `inline-flex rounded-full px-2 py-0.5 text-theme-xs font-medium ${columnCountBadgeMap[status]}`;
}

export function getCategoryClassName(color: KanbanCategoryColor | string): string {
  const key = (color in categoryColorMap ? color : "default") as KanbanCategoryColor;
  return `mt-3 inline-flex rounded-full px-2 py-0.5 text-theme-xs font-medium ${categoryColorMap[key]}`;
}

/** Drop zone highlight classes — apply to column wrapper */
export const kanbanDropZoneClasses = {
  isOver: "bg-blue-50/80 dark:bg-blue-500/5",
  canDrop: "bg-gray-50/50 dark:bg-gray-500/5",
  dragging: "opacity-80",
  overlay:
    "absolute inset-2 bg-blue-50/20 dark:bg-blue-500/10 z-10 pointer-events-none rounded-xl",
} as const;

export const kanbanDraggingCardOpacity = 0.3;

export const kanbanColumnMenuClass =
  "absolute right-0 top-full z-40 w-[140px] space-y-1 rounded-2xl border border-gray-200 bg-white p-2 shadow-theme-md dark:border-gray-800 dark:bg-gray-dark";

export const kanbanColumnMenuItemClass =
  "flex w-full font-normal text-left text-gray-500 rounded-lg hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-white/5 dark:hover:text-gray-300";
