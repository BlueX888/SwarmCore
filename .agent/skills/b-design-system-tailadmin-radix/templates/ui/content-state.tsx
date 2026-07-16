import * as React from "react";
import { AlertCircle, Inbox, Lock, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export type ContentStateVariant =
  | "loading"
  | "empty"
  | "error"
  | "forbidden"
  | "partial";

export type ContentStateProps = {
  variant: ContentStateVariant;
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  secondaryAction?: React.ReactNode;
  icon?: React.ReactNode;
  compact?: boolean;
  className?: string;
};

const defaultIcons: Record<ContentStateVariant, React.ReactNode> = {
  loading: <Spinner size="md" aria-label="加载中" />,
  empty: <Inbox className="size-8 text-gray-400" aria-hidden />,
  error: <AlertCircle className="size-8 text-error-500" aria-hidden />,
  forbidden: <Lock className="size-8 text-warning-500" aria-hidden />,
  partial: <RefreshCw className="size-8 text-brand-500" aria-hidden />,
};

export function ContentState({
  variant,
  title,
  description,
  action,
  secondaryAction,
  icon,
  compact = false,
  className,
}: ContentStateProps) {
  const isLoading = variant === "loading";

  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      aria-live={isLoading ? "polite" : undefined}
      aria-busy={isLoading || undefined}
      className={cn(
        "flex flex-col items-center justify-center text-center",
        compact ? "gap-3 py-8" : "gap-4 py-12",
        className,
      )}
    >
      <div className="flex items-center justify-center">{icon ?? defaultIcons[variant]}</div>
      <div className="max-w-md space-y-1">
        <p className="text-sm font-medium text-gray-800 dark:text-white/90">{title}</p>
        {description ? (
          <p className="text-theme-sm text-gray-500 dark:text-gray-400">{description}</p>
        ) : null}
      </div>
      {(action || secondaryAction) && (
        <div className="flex flex-wrap items-center justify-center gap-2">
          {action}
          {secondaryAction}
        </div>
      )}
    </div>
  );
}

export type ErrorStateAction = {
  label: string;
  onClick?: () => void;
  href?: string;
  variant?: "primary" | "outline";
};

export type ErrorStateProps = {
  reason: React.ReactNode;
  nextStep?: React.ReactNode;
  primaryAction?: ErrorStateAction;
  secondaryAction?: ErrorStateAction;
  deepLink?: { label: string; href: string };
  compact?: boolean;
  className?: string;
};

function renderAction(action: ErrorStateAction, key: string) {
  const variant = action.variant ?? (key === "primary" ? "primary" : "outline");
  if (action.href) {
    return (
      <Button key={key} variant={variant} asChild>
        <a href={action.href}>{action.label}</a>
      </Button>
    );
  }
  return (
    <Button key={key} variant={variant} onClick={action.onClick}>
      {action.label}
    </Button>
  );
}

/** Structured error: readable reason + next action + optional deep link. */
export function ErrorState({
  reason,
  nextStep,
  primaryAction,
  secondaryAction,
  deepLink,
  compact,
  className,
}: ErrorStateProps) {
  return (
    <ContentState
      variant="error"
      compact={compact}
      className={className}
      title={reason}
      description={nextStep}
      action={primaryAction ? renderAction(primaryAction, "primary") : undefined}
      secondaryAction={
        secondaryAction
          ? renderAction(secondaryAction, "secondary")
          : deepLink
            ? (
                <a
                  href={deepLink.href}
                  className="text-theme-sm font-medium text-brand-500 hover:text-brand-600"
                >
                  {deepLink.label}
                </a>
              )
            : undefined
      }
    />
  );
}

export type ResultStatus = "success" | "error" | "info" | "warning" | "404" | "403" | "500";

export type ResultStateProps = {
  status: ResultStatus;
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  secondaryAction?: React.ReactNode;
  compact?: boolean;
  className?: string;
};

const resultVariantMap: Record<ResultStatus, ContentStateVariant> = {
  success: "partial",
  error: "error",
  info: "empty",
  warning: "forbidden",
  "404": "empty",
  "403": "forbidden",
  "500": "error",
};

/** 整页/区块结果态 — 对齐 antd Result / MUI 状态页。 */
export function ResultState({
  status,
  title,
  description,
  action,
  secondaryAction,
  compact,
  className,
}: ResultStateProps) {
  return (
    <ContentState
      variant={resultVariantMap[status]}
      compact={compact}
      className={className}
      title={title}
      description={description}
      action={action}
      secondaryAction={secondaryAction}
    />
  );
}

export type EmptyStatePreset = "default" | "simple";

export type EmptyStateProps = {
  preset?: EmptyStatePreset;
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  compact?: boolean;
  className?: string;
};

/** 空数据预设 — 列表/表格/搜索无结果。 */
export function EmptyState({
  preset = "default",
  title = "暂无数据",
  description = preset === "default" ? "当前筛选条件下没有可展示的内容。" : undefined,
  action,
  compact,
  className,
}: EmptyStateProps) {
  return (
    <ContentState
      variant="empty"
      compact={compact ?? preset === "simple"}
      className={className}
      title={title}
      description={description}
      action={action}
    />
  );
}

export type ResultStatus = "success" | "error" | "info" | "warning" | "404" | "403" | "500";

export type ResultStateProps = {
  status: ResultStatus;
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  secondaryAction?: React.ReactNode;
  compact?: boolean;
  className?: string;
};

const resultVariantMap: Record<ResultStatus, ContentStateVariant> = {
  success: "partial",
  error: "error",
  info: "empty",
  warning: "forbidden",
  "404": "empty",
  "403": "forbidden",
  "500": "error",
};

/** 整页/区块结果态 — 对齐 antd Result / MUI 状态页。 */
export function ResultState({
  status,
  title,
  description,
  action,
  secondaryAction,
  compact,
  className,
}: ResultStateProps) {
  return (
    <ContentState
      variant={resultVariantMap[status]}
      compact={compact}
      className={className}
      title={title}
      description={description}
      action={action}
      secondaryAction={secondaryAction}
    />
  );
}

export type EmptyStatePreset = "default" | "simple";

export type EmptyStateProps = {
  preset?: EmptyStatePreset;
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  compact?: boolean;
  className?: string;
};

/** 空数据预设 — 列表/表格/搜索无结果。 */
export function EmptyState({
  preset = "default",
  title = "暂无数据",
  description = preset === "default" ? "当前筛选条件下没有可展示的内容。" : undefined,
  action,
  compact,
  className,
}: EmptyStateProps) {
  return (
    <ContentState
      variant="empty"
      compact={compact ?? preset === "simple"}
      className={className}
      title={title}
      description={description}
      action={action}
    />
  );
}
