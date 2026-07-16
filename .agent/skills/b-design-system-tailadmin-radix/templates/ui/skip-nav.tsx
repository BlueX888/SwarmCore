import * as React from "react";
import { cn } from "@/lib/utils";

export type SkipNavProps = {
  targetId?: string;
  label?: string;
  className?: string;
};

/**
 * 跳过导航链接 — 挂载于 AppLayout 顶部，Tab 聚焦时可见。
 */
export function SkipNav({
  targetId = "main-content",
  label = "跳到主内容",
  className,
}: SkipNavProps) {
  return (
    <a
      href={`#${targetId}`}
      className={cn(
        "sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:p-4 focus:text-sm focus:font-medium focus:text-brand-600 focus:shadow-theme-lg dark:focus:bg-gray-dark dark:focus:text-brand-400",
        className,
      )}
    >
      {label}
    </a>
  );
}
