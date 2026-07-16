import * as React from "react";
import { cn } from "@/lib/utils";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  KanbanColumnMenu,
  type KanbanColumnMenuAction,
} from "@/components/ui/kanban-column-menu";
import {
  getCategoryClassName,
  getColumnCountBadgeClass,
  kanbanBoardGridClass,
  kanbanColumnClass,
  kanbanColumnTitleClass,
  kanbanTaskCardClass,
  type KanbanCategoryColor,
  type KanbanStatus,
} from "@/lib/kanban-theme";

export type KanbanTask = {
  id: string;
  title: string;
  category?: { name: string; color: KanbanCategoryColor | string };
  dueDate?: string;
  commentCount?: number;
  assigneeAvatar?: string;
  assigneeName?: string;
};

export type KanbanColumnData = {
  id: string;
  status: KanbanStatus;
  title: string;
  tasks: KanbanTask[];
};

export type KanbanBoardProps = {
  columns: KanbanColumnData[];
  loading?: boolean;
  error?: string;
  onTaskMove?: (taskId: string, fromColumnId: string, toColumnId: string) => void;
  onColumnAction?: (
    columnId: string,
    action: KanbanColumnMenuAction,
  ) => void;
  onAddTask?: (columnId: string) => void;
  className?: string;
  emptyColumnMessage?: string;
  addTaskLabel?: string;
};

function KanbanTaskCard({ task }: { task: KanbanTask }) {
  return (
    <div className={kanbanTaskCardClass}>
      <h4 className="mb-5 mr-10 text-base text-gray-800 dark:text-white/90">
        {task.title}
      </h4>
      {(task.dueDate || task.commentCount !== undefined) && (
        <div className="mb-3 flex flex-wrap gap-3 text-sm text-gray-500 dark:text-gray-400">
          {task.dueDate ? <span>{task.dueDate}</span> : null}
          {task.commentCount !== undefined ? (
            <span>{task.commentCount} 条评论</span>
          ) : null}
        </div>
      )}
      {task.category ? (
        <span className={getCategoryClassName(task.category.color)}>
          {task.category.name}
        </span>
      ) : null}
      {task.assigneeAvatar || task.assigneeName ? (
        <div className="absolute right-5 top-5 size-6 overflow-hidden rounded-full border-[0.5px] border-gray-200 dark:border-gray-700">
          {task.assigneeAvatar ? (
            <img src={task.assigneeAvatar} alt={task.assigneeName ?? ""} />
          ) : (
            <span className="flex size-full items-center justify-center bg-gray-100 text-[10px] text-gray-600 dark:bg-white/10 dark:text-gray-300">
              {task.assigneeName?.slice(0, 1) ?? "?"}
            </span>
          )}
        </div>
      ) : null}
    </div>
  );
}

function KanbanColumnSkeleton() {
  return (
    <div className={cn(kanbanColumnClass, "gap-4")}>
      <Skeleton className="h-6 w-32 rounded-md" />
      <Skeleton className="min-h-[120px] rounded-xl" />
      <Skeleton className="min-h-[120px] rounded-xl" />
    </div>
  );
}

export function KanbanBoard({
  columns,
  loading = false,
  error,
  onTaskMove,
  onColumnAction,
  onAddTask,
  className,
  emptyColumnMessage = "暂无任务",
  addTaskLabel = "添加任务",
}: KanbanBoardProps) {
  const [draggingTaskId, setDraggingTaskId] = React.useState<string | null>(null);
  const [dragSourceColumnId, setDragSourceColumnId] = React.useState<string | null>(
    null,
  );

  if (error) {
    return (
      <Alert variant="error" className={className}>
        {error}
      </Alert>
    );
  }

  if (loading) {
    return (
      <div className={cn(kanbanBoardGridClass, className)}>
        <KanbanColumnSkeleton />
        <KanbanColumnSkeleton />
        <KanbanColumnSkeleton />
      </div>
    );
  }

  const handleDragStart = (
    event: React.DragEvent<HTMLDivElement>,
    taskId: string,
    columnId: string,
  ) => {
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", taskId);
    setDraggingTaskId(taskId);
    setDragSourceColumnId(columnId);
  };

  const handleDragEnd = () => {
    setDraggingTaskId(null);
    setDragSourceColumnId(null);
  };

  const handleDrop = (
    event: React.DragEvent<HTMLDivElement>,
    targetColumnId: string,
  ) => {
    event.preventDefault();
    const taskId = event.dataTransfer.getData("text/plain") || draggingTaskId;
    if (taskId && dragSourceColumnId && dragSourceColumnId !== targetColumnId) {
      onTaskMove?.(taskId, dragSourceColumnId, targetColumnId);
    }
    handleDragEnd();
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  return (
    <div className={cn(kanbanBoardGridClass, className)}>
      {columns.map((column) => (
        <div
          key={column.id}
          className={cn(
            kanbanColumnClass,
            draggingTaskId && dragSourceColumnId !== column.id
              ? "bg-blue-50/50 dark:bg-blue-500/5"
              : undefined,
          )}
          onDragOver={handleDragOver}
          onDrop={(event) => handleDrop(event, column.id)}
        >
          <div className="mb-1 flex items-center justify-between gap-2">
            <h3 className={kanbanColumnTitleClass}>
              {column.title}
              <span className={getColumnCountBadgeClass(column.status)}>
                {column.tasks.length}
              </span>
            </h3>
            <KanbanColumnMenu
              onEdit={() => onColumnAction?.(column.id, "edit")}
              onDelete={() => onColumnAction?.(column.id, "delete")}
              onClearAll={() => onColumnAction?.(column.id, "clearAll")}
            />
          </div>

          <div className="flex flex-col gap-5">
            {column.tasks.length === 0 ? (
              <p className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                {emptyColumnMessage}
              </p>
            ) : (
              column.tasks.map((task) => (
                <div
                  key={task.id}
                  draggable={Boolean(onTaskMove)}
                  onDragStart={(event) =>
                    handleDragStart(event, task.id, column.id)
                  }
                  onDragEnd={handleDragEnd}
                  className={cn(
                    draggingTaskId === task.id && "opacity-30",
                  )}
                >
                  <KanbanTaskCard task={task} />
                </div>
              ))
            )}
          </div>

          {onAddTask ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="mt-2 w-full"
              onClick={() => onAddTask(column.id)}
            >
              {addTaskLabel}
            </Button>
          ) : null}
        </div>
      ))}
    </div>
  );
}
