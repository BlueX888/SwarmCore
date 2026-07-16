import * as React from "react";
import { cn } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { QueryShell, type QueryShellProps } from "@/components/ui/query-shell";

export type MasterDetailTab = {
  id: string;
  label: React.ReactNode;
};

export type MasterDetailOpsProps = {
  /** Left master list — typically DataTableCard or compact list. */
  master: React.ReactNode;
  /** Detail header (title, status badge, actions). */
  detailHeader?: React.ReactNode;
  detailTabs?: MasterDetailTab[];
  activeDetailTab?: string;
  defaultDetailTab?: string;
  onDetailTabChange?: (tabId: string) => void;
  /** Detail body when not using tabbed panels. */
  detail?: React.ReactNode;
  /** Per-tab detail render when using detailTabs. */
  renderDetailTab?: (tabId: string) => React.ReactNode;
  detailStatus?: QueryShellProps["status"];
  detailQueryShellProps?: Omit<QueryShellProps, "status" | "children">;
  /** Selected master row id for a11y. */
  selectedId?: string | null;
  /** Placeholder when nothing selected. */
  emptyDetail?: React.ReactNode;
  masterWidth?: string;
  className?: string;
};

const defaultEmpty = (
  <div className="flex flex-1 flex-col items-center justify-center gap-2 py-16 text-center">
    <p className="text-theme-sm font-medium text-gray-800 dark:text-white/90">请选择一项</p>
    <p className="text-theme-sm text-gray-500">Choose a row from the list to view details.</p>
  </div>
);

/**
 * Master-Detail Ops — list + multi-tab detail with height chain.
 * @see references/layout-patterns/master-detail-ops.md
 */
export function MasterDetailOps({
  master,
  detailHeader,
  detailTabs,
  activeDetailTab,
  defaultDetailTab,
  onDetailTabChange,
  detail,
  renderDetailTab,
  detailStatus = "success",
  detailQueryShellProps,
  selectedId,
  emptyDetail = defaultEmpty,
  masterWidth = "xl:w-[360px] xl:max-w-[40%]",
  className,
}: MasterDetailOpsProps) {
  const hasSelection = selectedId != null && selectedId !== "";
  const tabs = detailTabs ?? [];
  const fallbackTab = defaultDetailTab ?? tabs[0]?.id ?? "overview";
  const resolvedDetailTab = activeDetailTab ?? fallbackTab;

  const detailBody = hasSelection ? (
    <>
      {detailHeader ? (
        <div className="shrink-0 border-b border-gray-200 px-4 py-4 dark:border-gray-800 md:px-6">
          {detailHeader}
        </div>
      ) : null}

      {tabs.length > 0 ? (
        <Tabs
          value={resolvedDetailTab}
          onValueChange={onDetailTabChange}
          className="flex min-h-0 flex-1 flex-col"
        >
          <TabsList className="h-auto w-full shrink-0 justify-start gap-0 overflow-x-auto rounded-none border-b border-gray-200 bg-transparent px-4 dark:border-gray-800 md:px-6">
            {tabs.map((tab) => (
              <TabsTrigger
                key={tab.id}
                value={tab.id}
                className="rounded-none border-b-2 border-transparent px-3 py-2.5 text-theme-sm data-[state=active]:border-brand-500 data-[state=active]:bg-transparent data-[state=active]:text-brand-500"
              >
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
          {tabs.map((tab) => (
            <TabsContent
              key={tab.id}
              value={tab.id}
              className="mt-0 flex min-h-0 flex-1 flex-col focus-visible:outline-none"
            >
              <div className="flex-1 overflow-auto custom-scrollbar p-4 md:p-6">
                <QueryShell status={detailStatus} minHeight={200} {...detailQueryShellProps}>
                  {renderDetailTab?.(tab.id)}
                </QueryShell>
              </div>
            </TabsContent>
          ))}
        </Tabs>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col overflow-auto custom-scrollbar p-4 md:p-6">
          <QueryShell status={detailStatus} minHeight={200} {...detailQueryShellProps}>
            {detail}
          </QueryShell>
        </div>
      )}
    </>
  ) : (
    emptyDetail
  );

  return (
    <div
      className={cn(
        "flex min-h-0 flex-1 flex-col gap-4 xl:flex-row",
        className,
      )}
    >
      <aside
        className={cn(
          "flex w-full shrink-0 flex-col min-h-0",
          masterWidth,
        )}
        aria-label="条目列表"
      >
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
          <div className="min-h-0 flex-1 overflow-y-auto custom-scrollbar">{master}</div>
        </div>
      </aside>

      <section
        className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]"
        aria-label={hasSelection ? `Details for ${selectedId}` : "Detail panel"}
      >
        <div className="flex min-h-0 flex-1 flex-col">{detailBody}</div>
      </section>
    </div>
  );
}
