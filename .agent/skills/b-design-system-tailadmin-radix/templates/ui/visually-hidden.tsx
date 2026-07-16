import * as React from "react";
import { cn } from "@/lib/utils";

export type VisuallyHiddenProps = React.HTMLAttributes<HTMLSpanElement>;

/** 屏幕阅读器专用文案 — 视觉隐藏但可被 AT 读取。 */
export function VisuallyHidden({ className, ...props }: VisuallyHiddenProps) {
  return <span className={cn("sr-only", className)} {...props} />;
}
