import * as React from "react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/context/sidebar-context";

export type BackdropProps = React.HTMLAttributes<HTMLDivElement> & {
  /**
   * 透明遮罩 — 视觉不可见且 `pointer-events-none` 可点穿下层。
   * 仅用于 Dialog 等特殊场景；移动端侧栏默认仍拦截点击。
   */
  invisible?: boolean;
};

export function Backdrop({ className, invisible = false, ...props }: BackdropProps) {
  const { isMobileOpen, toggleMobileSidebar } = useSidebar();

  if (!isMobileOpen) {
    return null;
  }

  return (
    <div
      className={cn(
        "fixed inset-0 z-40 xl:hidden",
        invisible
          ? "pointer-events-none bg-transparent"
          : "bg-gray-900/50",
        className,
      )}
      onClick={invisible ? undefined : toggleMobileSidebar}
      aria-hidden="true"
      data-invisible={invisible || undefined}
      {...props}
    />
  );
}
