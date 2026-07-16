import * as React from "react";
import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";
import { ContentState, ErrorState, type ErrorStateProps } from "@/components/ui/content-state";

export type QueryStatus =
  | "idle"
  | "pending"
  | "loading"
  | "success"
  | "empty"
  | "error"
  | "refetching"
  | "partial";

export type QueryShellProps = {
  /** Primary list/detail query status. */
  status: QueryStatus;
  /** Optional secondary query (filters, KPI row). Falls back to primary when omitted. */
  secondaryStatus?: QueryStatus;
  children?: React.ReactNode;
  className?: string;
  /** Shown when status is loading or pending (initial). */
  loadingFallback?: React.ReactNode;
  /** Shown when status is empty. */
  emptyTitle?: React.ReactNode;
  emptyDescription?: React.ReactNode;
  emptyAction?: React.ReactNode;
  /** Structured error for status === error. */
  error?: Omit<ErrorStateProps, "compact" | "className">;
  /** Shown when status is partial (stale data + background refresh). */
  partialBanner?: React.ReactNode;
  /** Minimum height to avoid layout collapse on empty/error. */
  minHeight?: string | number;
};

function isBlocking(status: QueryStatus): boolean {
  return status === "loading" || status === "pending";
}

function isEmpty(status: QueryStatus): boolean {
  return status === "empty";
}

function isError(status: QueryStatus): boolean {
  return status === "error";
}

function DefaultLoading() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <Spinner size="md" aria-label="正在加载数据" />
      <p className="text-theme-sm text-gray-500">加载中...</p>
    </div>
  );
}

/**
 * Query Shell — primary/secondary query state wrapper.
 * Use for list pages, detail panels, and KPI rows.
 */
export function QueryShell({
  status,
  secondaryStatus,
  children,
  className,
  loadingFallback,
  emptyTitle = "暂无数据",
  emptyDescription,
  emptyAction,
  error,
  partialBanner,
  minHeight = 240,
}: QueryShellProps) {
  const effectiveSecondary = secondaryStatus ?? status;
  const showRefetchOverlay =
    status === "refetching" || effectiveSecondary === "refetching";

  if (isBlocking(status)) {
    return (
      <div className={cn("relative w-full", className)} style={{ minHeight }}>
        {loadingFallback ?? <DefaultLoading />}
      </div>
    );
  }

  if (isError(status) && error) {
    return (
      <div className={cn("relative w-full", className)} style={{ minHeight }}>
        <ErrorState {...error} />
      </div>
    );
  }

  if (isEmpty(status)) {
    return (
      <div className={cn("relative w-full", className)} style={{ minHeight }}>
        <ContentState
          variant="empty"
          title={emptyTitle}
          description={emptyDescription}
          action={emptyAction}
        />
      </div>
    );
  }

  return (
    <div className={cn("relative w-full", className)} style={{ minHeight }}>
      {status === "partial" && partialBanner ? (
        <div className="mb-4 rounded-lg border border-warning-500/30 bg-warning-50 px-4 py-3 text-theme-sm text-warning-700 dark:bg-warning-500/10 dark:text-warning-400">
          {partialBanner}
        </div>
      ) : null}
      {children}
      {showRefetchOverlay ? (
        <div
          className="pointer-events-none absolute inset-0 flex items-start justify-center bg-white/60 pt-16 dark:bg-gray-900/60"
          aria-hidden
        >
          <Spinner size="sm" aria-label="正在刷新" />
        </div>
      ) : null}
    </div>
  );
}
