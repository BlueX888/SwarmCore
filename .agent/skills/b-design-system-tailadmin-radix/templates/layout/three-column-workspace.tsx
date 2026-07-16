import * as React from "react";
import { cn } from "@/lib/utils";

export type ThreeColumnWorkspaceProps = {
  /** Narrow icon rail (projects, portals). */
  rail?: React.ReactNode;
  /** Resource tree / file tree column. */
  tree: React.ReactNode;
  /** Main editor, viewer, or table. */
  main: React.ReactNode;
  /** Optional right aside (preview, properties). */
  aside?: React.ReactNode;
  treeHeader?: React.ReactNode;
  mainHeader?: React.ReactNode;
  className?: string;
  treeWidth?: string;
  asideWidth?: string;
};

/**
 * Three-column workspace — rail + tree + main (+ optional aside).
 * @see references/layout-patterns/three-column-workspace.md
 */
export function ThreeColumnWorkspace({
  rail,
  tree,
  main,
  aside,
  treeHeader,
  mainHeader,
  className,
  treeWidth = "w-64",
  asideWidth = "w-80",
}: ThreeColumnWorkspaceProps) {
  return (
    <div
      className={cn(
        "flex h-[calc(100vh-64px)] min-h-0 border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
    >
      {rail ? (
        <nav
          className="hidden shrink-0 flex-col border-r border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900 md:flex md:w-[72px]"
          aria-label="工作区导航栏"
        >
          {rail}
        </nav>
      ) : null}

      <aside
        className={cn(
          "hidden shrink-0 flex-col border-r border-gray-200 dark:border-gray-800 lg:flex",
          treeWidth,
        )}
        aria-label="资源树"
      >
        {treeHeader ? (
          <div className="shrink-0 border-b border-gray-200 px-3 py-3 dark:border-gray-800">
            {treeHeader}
          </div>
        ) : null}
        <div className="min-h-0 flex-1 overflow-y-auto custom-scrollbar">{tree}</div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col min-h-0">
        {mainHeader ? (
          <header className="shrink-0 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
            {mainHeader}
          </header>
        ) : null}
        <div className="min-h-0 flex-1 overflow-auto custom-scrollbar">{main}</div>
      </main>

      {aside ? (
        <aside
          className={cn(
            "hidden shrink-0 flex-col border-l border-gray-200 dark:border-gray-800 xl:flex",
            asideWidth,
          )}
          aria-label="侧边面板"
        >
          <div className="min-h-0 flex-1 overflow-y-auto custom-scrollbar">{aside}</div>
        </aside>
      ) : null}
    </div>
  );
}
