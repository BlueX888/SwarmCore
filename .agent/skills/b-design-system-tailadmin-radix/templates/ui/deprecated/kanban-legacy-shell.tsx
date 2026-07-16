import {
  KanbanBoard,
  type KanbanBoardProps,
} from "@/components/ui/kanban-board";

export type KanbanLegacyShellProps = KanbanBoardProps;

/**
 * @deprecated 自建 kanban-theme DOM 迁移过渡 wrapper。请改用 KanbanBoard。
 * 兼容至 G50，见 references/migration-notes/MN-03-kanban-legacy-board.md
 */
export function KanbanLegacyShell(props: KanbanLegacyShellProps) {
  return <KanbanBoard {...props} />;
}
