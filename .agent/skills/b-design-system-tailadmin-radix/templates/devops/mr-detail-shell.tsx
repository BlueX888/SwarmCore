import * as React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DiffViewer, type DiffHunk } from "./diff-viewer";
import { ApprovalTimeline, type ApprovalEvent } from "./approval-timeline";

export type MrDetailTab = "overview" | "commits" | "changes" | "checks" | "reviewers";

export type MrDetailShellProps = {
  title: string;
  status: "open" | "merged" | "closed" | "draft";
  sourceBranch: string;
  targetBranch: string;
  author: string;
  createdAt: string;
  reviewers?: string[];
  labels?: string[];
  activeTab?: MrDetailTab;
  defaultTab?: MrDetailTab;
  onTabChange?: (tab: MrDetailTab) => void;
  overview?: React.ReactNode;
  commits?: React.ReactNode;
  diffHunks?: DiffHunk[];
  checks?: React.ReactNode;
  approvalEvents?: ApprovalEvent[];
  sidebar?: React.ReactNode;
  onApprove?: () => void;
  onRequestChanges?: () => void;
  onMerge?: () => void;
  className?: string;
};

const statusColor: Record<MrDetailShellProps["status"], "primary" | "success" | "error" | "warning"> = {
  open: "primary",
  merged: "success",
  closed: "error",
  draft: "warning",
};

/**
 * Merge Request / Pull Request detail shell — Overview/Commits/Changes/Checks tabs.
 * @see references/layout-patterns/code-repository.md
 */
export function MrDetailShell({
  title,
  status,
  sourceBranch,
  targetBranch,
  author,
  createdAt,
  reviewers = [],
  labels = [],
  activeTab,
  defaultTab = "overview",
  onTabChange,
  overview,
  commits,
  diffHunks = [],
  checks,
  approvalEvents = [],
  sidebar,
  onApprove,
  onRequestChanges,
  onMerge,
  className,
}: MrDetailShellProps) {
  const resolvedTab = activeTab ?? defaultTab;

  return (
    <div className={cn("flex min-h-0 flex-col rounded-xl border border-gray-200 dark:border-gray-800", className)}>
      <header className="border-b border-gray-200 px-4 py-4 md:px-6 dark:border-gray-800">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white/90">{title}</h1>
              <Badge variant="light" color={statusColor[status]} size="sm">
                {status}
              </Badge>
            </div>
            <p className="mt-1 text-theme-sm text-gray-500">
              <span className="font-mono text-brand-600">{sourceBranch}</span>
              <span className="mx-2">→</span>
              <span className="font-mono">{targetBranch}</span>
              <span className="mx-2">·</span>
              {author}
              <span className="mx-2">·</span>
              {createdAt}
            </p>
            {labels.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-1">
                {labels.map((label) => (
                  <Badge key={label} variant="light" color="light" size="sm">
                    {label}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" size="sm" onClick={onRequestChanges}>
              Request changes
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={onApprove}>
              Approve
            </Button>
            <Button type="button" size="sm" onClick={onMerge} disabled={status !== "open"}>
              Merge
            </Button>
          </div>
        </div>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 xl:grid-cols-[minmax(0,1fr)_280px]">
        <Tabs
          value={resolvedTab}
          onValueChange={(v) => onTabChange?.(v as MrDetailTab)}
          className="flex min-h-0 flex-col"
        >
          <TabsList className="h-auto w-full shrink-0 justify-start gap-0 overflow-x-auto rounded-none border-b border-gray-200 bg-transparent px-4 dark:border-gray-800 md:px-6">
            {(["overview", "commits", "changes", "checks"] as const).map((tab) => (
              <TabsTrigger
                key={tab}
                value={tab}
                className="rounded-none border-b-2 border-transparent px-4 py-3 capitalize data-[state=active]:border-brand-500 data-[state=active]:text-brand-600"
              >
                {tab}
              </TabsTrigger>
            ))}
          </TabsList>

          <div className="min-h-0 flex-1 overflow-y-auto p-4 md:p-6">
            <TabsContent value="overview" className="mt-0">
              {overview ?? (
                approvalEvents.length > 0 ? (
                  <ApprovalTimeline events={approvalEvents} />
                ) : (
                  <p className="text-theme-sm text-gray-500">No overview content.</p>
                )
              )}
            </TabsContent>
            <TabsContent value="commits" className="mt-0">
              {commits ?? <p className="text-theme-sm text-gray-500">No commits listed.</p>}
            </TabsContent>
            <TabsContent value="changes" className="mt-0 space-y-4">
              {diffHunks.length > 0 ? (
                <DiffViewer hunks={diffHunks} fileName="src/api/handler.ts" />
              ) : (
                <p className="text-theme-sm text-gray-500">暂无文件变更。</p>
              )}
            </TabsContent>
            <TabsContent value="checks" className="mt-0">
              {checks ?? <p className="text-theme-sm text-gray-500">所有检查已通过。</p>}
            </TabsContent>
          </div>
        </Tabs>

        <aside className="border-t border-gray-200 p-4 xl:border-l xl:border-t-0 dark:border-gray-800">
          {sidebar ?? (
            <div className="space-y-4">
              <div>
                <h3 className="text-theme-xs font-semibold uppercase tracking-wide text-gray-500">
                  评审人
                </h3>
                <ul className="mt-2 space-y-1">
                  {reviewers.length === 0 ? (
                    <li className="text-theme-sm text-gray-500">暂无评审人</li>
                  ) : (
                    reviewers.map((r) => (
                      <li key={r} className="text-theme-sm text-gray-800 dark:text-white/90">
                        {r}
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
