import type * as React from "react";
import { cn } from "@/lib/utils";

export interface PageHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 顶部小节标签（eyebrow），例如 "运行管理" */
  eyebrow?: string;
  /** 页面主标题 */
  title: string;
  /** 副标题描述 */
  description?: string;
  /** 右侧操作区 */
  actions?: React.ReactNode;
}

export function PageHeader({ eyebrow, title, description, actions, className, ...props }: PageHeaderProps) {
  return (
    <div {...props} className={cn("flex flex-wrap items-end justify-between gap-4", className)}>
      <div className="min-w-0">
        {eyebrow ? <p className="text-sm font-medium text-brand-500">{eyebrow}</p> : null}
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">{title}</h1>
        {description ? <p className="mt-1 max-w-2xl text-sm text-gray-500">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}
