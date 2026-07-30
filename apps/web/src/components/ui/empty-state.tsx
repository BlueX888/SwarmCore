import type { LucideIcon } from "lucide-react";
import type * as React from "react";
import { cn } from "@/lib/utils";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 图标（lucide） */
  icon?: LucideIcon;
  /** 标题 */
  title: string;
  /** 描述 */
  description?: string;
  /** 操作按钮（一个或多个 Button / Link） */
  action?: React.ReactNode;
  /** 紧凑模式（卡片内嵌） */
  compact?: boolean;
}

const toneMap = {
  brand: "bg-brand-50 text-brand-500 dark:bg-brand-500/15 dark:text-brand-400",
  success: "bg-success-50 text-success-600 dark:bg-success-500/15 dark:text-success-500",
  neutral: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400",
} as const;

export interface EmptyStateWithToneProps extends EmptyStateProps {
  /** 图标背景色调 */
  tone?: keyof typeof toneMap;
}

export function EmptyState({ icon: Icon, title, description, action, compact, tone = "brand", className, ...props }: EmptyStateWithToneProps) {
  return (
    <div
      {...props}
      className={cn(
        "flex flex-col items-center justify-center text-center",
        compact ? "gap-2 py-8" : "min-h-60 gap-3 py-12",
        className,
      )}
    >
      {Icon ? (
        <span aria-hidden className={cn("grid size-12 place-items-center rounded-2xl", toneMap[tone])}>
          <Icon className="size-5" />
        </span>
      ) : null}
      <h2 className={cn("font-medium text-gray-900 dark:text-white", compact && "text-sm")}>{title}</h2>
      {description ? <p className="max-w-md text-sm text-gray-500">{description}</p> : null}
      {action ? <div className={cn("flex flex-wrap items-center justify-center gap-2", compact ? "mt-2" : "mt-3")}>{action}</div> : null}
    </div>
  );
}
