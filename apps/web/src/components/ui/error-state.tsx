import { CircleAlert } from "lucide-react";
import type * as React from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 标题，例如 "无法加载运行记录" */
  title: string;
  /** 详细错误消息 */
  message?: string;
  /** 重试回调；传入则渲染重试按钮 */
  onRetry?: () => void;
  /** 紧凑模式（卡片内嵌 / 行内警告） */
  compact?: boolean;
}

export function ErrorState({ title, message, onRetry, compact, className, ...props }: ErrorStateProps) {
  if (compact) {
    return (
      <div
        role="alert"
        {...props}
        className={cn(
          "flex items-center gap-3 rounded-xl border border-error-200 bg-error-50 px-4 py-3 text-sm dark:border-error-500/30 dark:bg-error-500/10",
          className,
        )}
      >
        <CircleAlert aria-hidden className="size-4 shrink-0 text-error-600 dark:text-error-400" />
        <div className="min-w-0 flex-1">
          <p className="font-medium text-error-700 dark:text-error-300">{title}</p>
          {message ? <p className="mt-0.5 truncate text-xs text-error-600 dark:text-error-400">{message}</p> : null}
        </div>
        {onRetry ? (
          <Button variant="ghost" size="sm" onClick={onRetry} className="shrink-0 text-error-700 hover:bg-error-100 dark:text-error-300 dark:hover:bg-error-500/20">
            重试
          </Button>
        ) : null}
      </div>
    );
  }
  return (
    <div role="alert" {...props} className={cn("flex min-h-60 flex-col items-center justify-center gap-3 text-center", className)}>
      <span aria-hidden className="grid size-12 place-items-center rounded-2xl bg-error-50 text-error-600 dark:bg-error-500/15 dark:text-error-400">
        <CircleAlert className="size-5" />
      </span>
      <h2 className="font-medium text-error-600 dark:text-error-400">{title}</h2>
      {message ? <p className="max-w-md text-sm text-gray-500">{message}</p> : null}
      {onRetry ? (
        <Button variant="destructive" size="sm" onClick={onRetry} className="mt-1">
          重试
        </Button>
      ) : null}
    </div>
  );
}
