import * as React from "react";
import { cn } from "@/lib/utils";

export type InputGroupProps = {
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  addonBefore?: React.ReactNode;
  addonAfter?: React.ReactNode;
  className?: string;
  children: React.ReactElement<{ className?: string }>;
};

function Addon({
  children,
  position,
}: {
  children: React.ReactNode;
  position: "before" | "after";
}) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center border border-gray-300 bg-gray-50 px-3 text-theme-sm text-gray-600 dark:border-gray-700 dark:bg-white/5 dark:text-gray-400",
        position === "before" ? "rounded-l-lg border-r-0" : "rounded-r-lg border-l-0",
      )}
    >
      {children}
    </span>
  );
}

function Affix({
  children,
  position,
}: {
  children: React.ReactNode;
  position: "prefix" | "suffix";
}) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center text-gray-500 dark:text-gray-400",
        position === "prefix" ? "pl-3" : "pr-3",
      )}
    >
      {children}
    </span>
  );
}

/**
 * 输入框前缀/后缀与 addon 组合 — 搜索栏、金额输入、图标字段。
 */
export function InputGroup({
  prefix,
  suffix,
  addonBefore,
  addonAfter,
  className,
  children,
}: InputGroupProps) {
  const hasAddonBefore = addonBefore != null;
  const hasAddonAfter = addonAfter != null;
  const hasPrefix = prefix != null;
  const hasSuffix = suffix != null;

  const childClassName = cn(
    children.props.className,
    "min-w-0 flex-1",
    hasAddonBefore && "rounded-l-none",
    hasAddonAfter && "rounded-r-none",
    !hasAddonBefore && !hasPrefix && "rounded-l-lg",
    !hasAddonAfter && !hasSuffix && "rounded-r-lg",
    (hasPrefix || hasSuffix) && !hasAddonBefore && !hasAddonAfter && "border-0 shadow-none focus-visible:ring-0",
  );

  const inputShell = (
    <div
      className={cn(
        "flex min-w-0 flex-1 items-center overflow-hidden border border-gray-300 bg-transparent shadow-theme-xs dark:border-gray-700",
        !hasAddonBefore && "rounded-l-lg",
        !hasAddonAfter && "rounded-r-lg",
        (hasPrefix || hasSuffix) && "focus-within:border-brand-300 focus-within:ring-3 focus-within:ring-brand-500/20 dark:focus-within:border-brand-800",
      )}
    >
      {hasPrefix ? <Affix position="prefix">{prefix}</Affix> : null}
      {React.cloneElement(children, { className: childClassName })}
      {hasSuffix ? <Affix position="suffix">{suffix}</Affix> : null}
    </div>
  );

  return (
    <div className={cn("flex w-full items-stretch", className)}>
      {hasAddonBefore ? <Addon position="before">{addonBefore}</Addon> : null}
      {inputShell}
      {hasAddonAfter ? <Addon position="after">{addonAfter}</Addon> : null}
    </div>
  );
}
