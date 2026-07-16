import * as React from "react";
import { cn } from "@/lib/utils";

export type ButtonGroupProps = {
  /** 无缝拼接 — 负 margin + 圆角仅首尾 */
  attached?: boolean;
  className?: string;
  children: React.ReactElement | React.ReactElement[];
};

export function ButtonGroup({ attached = false, className, children }: ButtonGroupProps) {
  const items = React.Children.toArray(children).filter(React.isValidElement) as React.ReactElement[];

  if (!attached) {
    return (
      <div className={cn("inline-flex items-stretch gap-2", className)} role="group">
        {items}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "inline-flex items-stretch -space-x-px",
        "[&>*:first-child]:rounded-r-none [&>*:last-child]:rounded-l-none",
        "[&>*:not(:first-child):not(:last-child)]:rounded-none",
        className,
      )}
      role="group"
      data-attached="true"
    >
      {items.map((child, index) => {
        const childClassName =
          typeof child.props === "object" && child.props && "className" in child.props
            ? String(child.props.className ?? "")
            : "";

        return React.cloneElement(child, {
          key: child.key ?? index,
          className: cn(childClassName, "relative z-[1] focus-visible:z-[2]"),
        });
      })}
    </div>
  );
}
