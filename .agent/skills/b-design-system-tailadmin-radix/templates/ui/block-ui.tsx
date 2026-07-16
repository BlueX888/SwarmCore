import * as React from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";

export type BlockUIProps = {
  blocked?: boolean;
  message?: React.ReactNode;
  /** 阻塞目标；默认全页 `document.body` */
  container?: HTMLElement | null;
  className?: string;
  spinnerSize?: "sm" | "md" | "lg";
};

export function BlockUI({
  blocked = false,
  message = "处理中…",
  container,
  className,
  spinnerSize = "md",
}: BlockUIProps) {
  const [mounted, setMounted] = React.useState(false);
  const target = container ?? (typeof document !== "undefined" ? document.body : null);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  React.useEffect(() => {
    if (!blocked || !target) return;
    target.setAttribute("aria-busy", "true");
    return () => {
      target.removeAttribute("aria-busy");
    };
  }, [blocked, target]);

  if (!blocked || !mounted || !target) {
    return null;
  }

  return createPortal(
    <div
      className={cn(
        "fixed inset-0 z-[100] flex flex-col items-center justify-center gap-3 bg-gray-900/40 backdrop-blur-[2px]",
        className,
      )}
      role="status"
      aria-live="polite"
      aria-label={typeof message === "string" ? message : "加载中"}
    >
      <Spinner size={spinnerSize} className="text-white" />
      {message ? (
        <p className="text-theme-sm font-medium text-white">{message}</p>
      ) : null}
    </div>,
    target,
  );
}
