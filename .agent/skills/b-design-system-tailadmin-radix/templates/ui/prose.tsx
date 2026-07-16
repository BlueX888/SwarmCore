import * as React from "react";
import { cn } from "@/lib/utils";

export type ProseProps = {
  children?: React.ReactNode;
  /** 仅渲染信任来源 HTML */
  html?: string;
  className?: string;
};

/**
 * 远程 HTML / 富文本排版容器 — 对标 Chakra Prose。
 * 使用 `html` 时须确保内容来源可信。
 */
export function Prose({ children, html, className }: ProseProps) {
  if (html) {
    return (
      <div
        className={cn("prose prose-sm max-w-none dark:prose-invert", className)}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }

  return (
    <div className={cn("prose prose-sm max-w-none dark:prose-invert", className)}>
      {children}
    </div>
  );
}
