# Kanban 主题 — 任务看板

独立 Kanban 主题 shard。源：`components/task/kanban/*`、`pages/Task/TaskKanban.tsx`。

可复制模板：`templates/lib/kanban-theme.ts`

## 检索别名

| 意图 | 读本节 |
|---|---|
| 看板三列布局 | `#board-layout` |
| 列头与计数 Badge | `#column-header` |
| 任务卡片 | `#task-card` |
| Category pill | `#category-colors` |
| DnD 拖拽态 | `#drag-states` |
| 列操作菜单 | `#column-menu` |
| 加载/空态 | `#data-states` |

## Board Layout

路由：`/task-kanban`（见 `route-index.md`）。

```tsx
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { kanbanBoardGridClass } from "@/lib/kanban-theme";

<DndProvider backend={HTML5Backend}>
  <div className={kanbanBoardGridClass}>
    <KanbanColumn title="To Do" status="todo" tasks={todoTasks} />
    <KanbanColumn title="In Progress" status="inProgress" tasks={inProgressTasks} />
    <KanbanColumn title="Completed" status="completed" tasks={completedTasks} />
  </div>
</DndProvider>
```

- 外包 `PageBreadcrumb pageTitle="Kanban"`
- 栅格：`grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 divide-x divide-gray-200`
- 列内：`flex flex-col gap-5 p-4 xl:p-6 swim-lane`

## Column Header

```tsx
import { getColumnCountBadgeClass } from "@/lib/kanban-theme";

<h3 className="flex items-center gap-3 text-base font-medium text-gray-800 dark:text-white/90">
  {title}
  <span className={getColumnCountBadgeClass(status)}>{tasks.length}</span>
</h3>
```

| status | Badge 语义 |
|---|---|
| `todo` | gray-100 / dark white/[0.03] |
| `inProgress` | warning-50 / dark warning-500/15 |
| `completed` | success-50 / dark success-500/15 |

列菜单：shadcn `DropdownMenu`（源项目为自定义 Dropdown）；`rounded-2xl shadow-theme-md w-[140px]`。

## Column Menu

可复制模板：`templates/ui/kanban-column-menu.tsx`

```tsx
import { KanbanColumnMenu } from "@/components/ui/kanban-column-menu";
import { getColumnCountBadgeClass } from "@/lib/kanban-theme";

<div className="flex items-center justify-between mb-1">
  <h3 className="flex items-center gap-3 text-base font-medium text-gray-800 dark:text-white/90">
    {title}
    <span className={getColumnCountBadgeClass(status)}>{tasks.length}</span>
  </h3>
  <KanbanColumnMenu
    onEdit={() => {}}
    onDelete={() => {}}
    onClearAll={() => {}}
  />
</div>
```

| 菜单项 | 源行为 | 说明 |
|---|---|---|
| Edit | `closeDropdown` | 列重命名/编辑入口 |
| Delete | `closeDropdown` | 删除列 |
| Clear All | `closeDropdown` | 清空列内任务 |

- 触发器：`MoreHorizontal` `size-6`，`text-gray-400 hover:text-gray-700`
- 内容：`kanbanColumnMenuClass` + `kanbanColumnMenuItemClass`（见 `kanban-theme.ts`）
- 浮层打开态截图：`preview-screenshots/kanban-column-menu-*.png`

## KanbanBoard 可复制模板

```tsx
import { KanbanBoard } from "@/components/ui/kanban-board";

<KanbanBoard
  columns={columns}
  onTaskMove={(taskId, from, to) => moveTask(taskId, from, to)}
  onColumnAction={(columnId, action) => handleColumnAction(columnId, action)}
  onAddTask={(columnId) => openAddTask(columnId)}
  loading={isLoading}
  error={errorMessage}
/>
```

- 受控 `columns: KanbanColumnData[]`，每列含 `status: todo | inProgress | completed`
- `onTaskMove` 可选；提供时启用 HTML5 drag-and-drop（无需 react-dnd）
- `loading` 每列 2 个 Skeleton；`error` 替换整板为 Alert
- 空列显示 `emptyColumnMessage` + 可选 `onAddTask` outline 按钮
- 列头集成 `KanbanColumnMenu`（Edit/Delete/Clear All）
- 审计状态见 `extension-audit.md#kanban`

## Task Card

```tsx
import { getCategoryClassName } from "@/lib/kanban-theme";

<div className="relative p-5 bg-white border border-gray-200 rounded-xl shadow-theme-sm dark:border-gray-800 dark:bg-white/5">
  <h4 className="mb-5 mr-10 text-base text-gray-800 dark:text-white/90">{task.title}</h4>
  {/* meta: dueDate, comments, links */}
  <span className={getCategoryClassName(task.category.color)}>{task.category.name}</span>
  <div className="absolute top-5 right-5 w-6 h-6 rounded-full border-[0.5px] border-gray-200 overflow-hidden">
    <img src={task.assignee} alt="" />
  </div>
</div>
```

- 可选 `projectDesc`（`text-sm text-gray-500`）与 `projectImg`（`rounded-xl border-[0.5px]`）
- meta 行：`flex gap-3 text-sm text-gray-500`（日历、评论、链接图标）

## Category Colors

| color key | 背景/文字 |
|---|---|
| `brand` | brand-50 / brand-700 |
| `success` | success-50 / success-700 |
| `orange` | orange-50 / orange-700 |
| `error` | error-50 / error-700 |
| `purple` | purple-50 / purple-700 |
| `default` | gray-100 / gray-700 |

## Drag States

| 状态 | 视觉 |
|---|---|
| dragging card | `opacity: 0.3` |
| column isOver + canDrop | `bg-blue-50/80 dark:bg-blue-500/5` + inset overlay |
| column canDrop + isDragging | `bg-gray-50/50 dark:bg-gray-500/5` |
| board isDragging | 非目标列 `opacity-80` |

使用 `react-dnd`：`accept: "task"`；`changeTaskStatus` 在 drop 到不同列时更新 status。

## Data States

| 状态 | 模式 |
|---|---|
| loading | 每列 2–3 个 `Skeleton` 卡 (`min-h-[120px]`) |
| empty column | 列内居中 `text-gray-500 text-sm` + outline Button「Add task」 |
| error | `Alert variant="error"` 替换整板，保留 breadcrumb |

## 工程约束

- 保留 `react-dnd` + `react-dnd-html5-backend`；不替换为 @dnd-kit 除非迁移任务明确要求
- 列宽响应式：mobile 单列堆叠，tablet 双列，desktop 三列
- 与 `layout-patterns/table-list.md` 的 TaskList 路由区分：Kanban 为 `/task-kanban`

## 与 third-party-template 关系

`third-party-template.md#kanban` 保留简要入口；本 shard 为 Kanban 深化参考。
