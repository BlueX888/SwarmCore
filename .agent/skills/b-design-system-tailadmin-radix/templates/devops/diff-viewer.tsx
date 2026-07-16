import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronRight } from "lucide-react";

export type DiffLineType = "added" | "removed" | "context" | "changed";

export type DiffHunk = {
  id: string;
  header: string;
  collapsed?: boolean;
  lines: Array<{
    id: string;
    type: DiffLineType;
    oldNo?: number;
    newNo?: number;
    content: string;
  }>;
};

export type DiffViewerProps = {
  hunks: DiffHunk[];
  fileName?: string;
  largeFile?: boolean;
  onToggleHunk?: (hunkId: string) => void;
  className?: string;
};

const lineBg: Record<DiffLineType, string> = {
  added: "bg-success-50/80 dark:bg-success-500/10",
  removed: "bg-error-50/80 dark:bg-error-500/10",
  changed: "bg-warning-50/50 dark:bg-warning-500/10",
  context: "",
};

const linePrefix: Record<DiffLineType, string> = {
  added: "+",
  removed: "-",
  changed: "~",
  context: " ",
};

/**
 * MR/PR diff viewer — added/removed/changed hunks, collapse, large-file fallback.
 * @see references/layout-patterns/code-repository.md
 */
export function DiffViewer({
  hunks,
  fileName,
  largeFile = false,
  onToggleHunk,
  className,
}: DiffViewerProps) {
  if (largeFile) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-gray-300 bg-gray-50 py-16 text-center dark:border-gray-700 dark:bg-white/[0.02]",
          className,
        )}
      >
        <p className="text-theme-sm font-medium text-gray-800 dark:text-white/90">
          Diff too large to display
        </p>
        <p className="max-w-sm text-theme-sm text-gray-500">
          {fileName ? `${fileName} exceeds the inline diff limit.` : "Download the patch or view in an external tool."}
        </p>
        <Button type="button" variant="outline" size="sm">
          Download patch
        </Button>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-gray-200 font-mono text-[11px] leading-5 dark:border-gray-800",
        className,
      )}
    >
      {fileName ? (
        <div className="border-b border-gray-200 bg-gray-50 px-4 py-2 text-theme-sm font-medium text-gray-800 dark:border-gray-800 dark:bg-white/[0.03] dark:text-white/90">
          {fileName}
        </div>
      ) : null}
      <div className="max-h-[420px] overflow-auto">
        {hunks.map((hunk) => (
          <div key={hunk.id} className="border-b border-gray-100 last:border-0 dark:border-white/[0.05]">
            <button
              type="button"
              className="flex w-full items-center gap-2 bg-gray-100/80 px-3 py-1.5 text-left text-theme-xs text-gray-600 hover:bg-gray-100 dark:bg-white/[0.04] dark:text-gray-400 dark:hover:bg-white/[0.06]"
              onClick={() => onToggleHunk?.(hunk.id)}
            >
              {hunk.collapsed ? (
                <ChevronRight className="size-3.5 shrink-0" />
              ) : (
                <ChevronDown className="size-3.5 shrink-0" />
              )}
              <span className="truncate">{hunk.header}</span>
            </button>
            {!hunk.collapsed
              ? hunk.lines.map((line) => (
                  <div
                    key={line.id}
                    className={cn("grid grid-cols-[48px_48px_16px_1fr] gap-0", lineBg[line.type])}
                  >
                    <span className="select-none px-2 text-right tabular-nums text-gray-400">
                      {line.oldNo ?? ""}
                    </span>
                    <span className="select-none px-2 text-right tabular-nums text-gray-400">
                      {line.newNo ?? ""}
                    </span>
                    <span
                      className={cn(
                        "select-none text-center",
                        line.type === "added" && "text-success-600",
                        line.type === "removed" && "text-error-600",
                        line.type === "changed" && "text-warning-600",
                      )}
                    >
                      {linePrefix[line.type]}
                    </span>
                    <span className="min-w-0 whitespace-pre-wrap break-all px-2 py-0.5 text-gray-800 dark:text-gray-200">
                      {line.content}
                    </span>
                  </div>
                ))
              : null}
          </div>
        ))}
      </div>
    </div>
  );
}
