import * as React from "react";
import { useSearchParams } from "react-router";
import { cn } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { QueryShell, type QueryShellProps } from "@/components/ui/query-shell";

export type HubTabDef = {
  id: string;
  label: React.ReactNode;
  /** Optional badge count (e.g. pending approvals). */
  count?: number;
  disabled?: boolean;
  disabledReason?: string;
};

export type HubTabsLayoutProps = {
  tabs: HubTabDef[];
  /** Controlled active tab id. When omitted, reads `?tab=` from URL. */
  activeTab?: string;
  defaultTab?: string;
  /** Sync tab to `?tab=` query param. Default true when using router. */
  syncUrl?: boolean;
  onTabChange?: (tabId: string) => void;
  /** Query state for the active panel. */
  status?: QueryShellProps["status"];
  queryShellProps?: Omit<QueryShellProps, "status" | "children">;
  children?: React.ReactNode | ((tabId: string) => React.ReactNode);
  className?: string;
  listClassName?: string;
  contentClassName?: string;
};

/**
 * Hub Tabs — settings/quota/usage style pages with URL-synced tabs.
 * @see references/layout-patterns/hub-tabs.md
 */
export function HubTabsLayout({
  tabs,
  activeTab: activeTabProp,
  defaultTab,
  syncUrl = true,
  onTabChange,
  status = "success",
  queryShellProps,
  children,
  className,
  listClassName,
  contentClassName,
}: HubTabsLayoutProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const fallback = defaultTab ?? tabs[0]?.id ?? "";
  const urlTab = searchParams.get("tab") ?? fallback;
  const isControlled = activeTabProp !== undefined;
  const activeTab = isControlled ? activeTabProp : urlTab;

  const validIds = React.useMemo(() => new Set(tabs.map((t) => t.id)), [tabs]);
  const resolvedTab = validIds.has(activeTab) ? activeTab : fallback;

  const handleChange = (next: string) => {
    if (syncUrl && !isControlled) {
      setSearchParams(
        (prev) => {
          const params = new URLSearchParams(prev);
          if (next === fallback) {
            params.delete("tab");
          } else {
            params.set("tab", next);
          }
          return params;
        },
        { replace: !validIds.has(urlTab) },
      );
    }
    onTabChange?.(next);
  };

  const renderPanel = (tabId: string) =>
    typeof children === "function" ? children(tabId) : children;

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      <Tabs value={resolvedTab} onValueChange={handleChange}>
        <TabsList
          className={cn(
            "h-auto w-full justify-start gap-0 overflow-x-auto rounded-none border-b border-gray-200 bg-transparent p-0 dark:border-gray-800",
            listClassName,
          )}
        >
          {tabs.map((tab) => (
            <TabsTrigger
              key={tab.id}
              value={tab.id}
              disabled={tab.disabled}
              title={tab.disabled ? tab.disabledReason : undefined}
              className={cn(
                "rounded-none border-b-2 border-transparent px-4 py-3 text-theme-sm font-medium text-gray-500 shadow-none",
                "data-[state=active]:border-brand-500 data-[state=active]:bg-transparent data-[state=active]:text-brand-500",
                "dark:text-gray-400 dark:data-[state=active]:text-brand-400",
              )}
            >
              <span className="inline-flex items-center gap-2">
                {tab.label}
                {tab.count != null && tab.count > 0 ? (
                  <span className="inline-flex min-w-[20px] items-center justify-center rounded-full bg-brand-50 px-1.5 py-0.5 text-xs font-medium text-brand-500 dark:bg-brand-500/15">
                    {tab.count}
                  </span>
                ) : null}
              </span>
            </TabsTrigger>
          ))}
        </TabsList>

        {tabs.map((tab) => (
          <TabsContent
            key={tab.id}
            value={tab.id}
            className={cn("mt-4 min-h-[320px] focus-visible:outline-none", contentClassName)}
          >
            <QueryShell status={status} minHeight={320} {...queryShellProps}>
              {renderPanel(tab.id)}
            </QueryShell>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
