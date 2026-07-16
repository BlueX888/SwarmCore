/**
 * Deprecated compatibility wrappers for backward-compatible migrations.
 * See references/migration-notes/ for filled migration note drills.
 */

export {
  ThemeToggle,
  ThemeToggleButton,
  type ThemeToggleButtonProps,
} from "@/components/layout/theme-toggle";

/** @deprecated 使用 layout/theme-toggle 的 ThemeToggle 或 ThemeToggleButton。兼容至 G50，见 MN-01 */
export { ThemeToggle as ThemeToggleAlias } from "@/components/layout/theme-toggle";

export {
  SearchCommandStatic,
  type SearchCommandStaticProps,
} from "./search-command-static";

export {
  KanbanLegacyShell,
  type KanbanLegacyShellProps,
} from "./kanban-legacy-shell";
