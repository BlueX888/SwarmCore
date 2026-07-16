import * as React from "react";
import { cn } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export type ToggleTipProps = {
  content: React.ReactNode;
  children: React.ReactElement;
  side?: React.ComponentProps<typeof PopoverContent>["side"];
  align?: React.ComponentProps<typeof PopoverContent>["align"];
  className?: string;
  contentClassName?: string;
};

/**
 * 点击触发的帮助提示 — 移动端友好，非 hover Tooltip。
 */
export function ToggleTip({
  content,
  children,
  side = "top",
  align = "center",
  className,
  contentClassName,
}: ToggleTipProps) {
  return (
    <Popover modal={false}>
      <PopoverTrigger asChild className={className}>
        {children}
      </PopoverTrigger>
      <PopoverContent
        side={side}
        align={align}
        className={cn(
          "w-auto max-w-xs p-3 text-theme-sm leading-relaxed text-gray-600 dark:text-gray-300",
          contentClassName,
        )}
      >
        {content}
      </PopoverContent>
    </Popover>
  );
}
