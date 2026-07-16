import * as React from "react";
import { cn } from "@/lib/utils";

export type BlockquoteProps = React.BlockquoteHTMLAttributes<HTMLQuoteElement> & {
  cite?: string;
};

export function Blockquote({ cite, className, children, ...props }: BlockquoteProps) {
  return (
    <blockquote
      cite={cite}
      className={cn(
        "border-l-4 border-brand-500/40 pl-4 text-theme-sm italic text-gray-600 dark:text-gray-400",
        className,
      )}
      {...props}
    >
      {children}
      {cite ? (
        <footer className="mt-2 not-italic text-theme-xs text-gray-500 dark:text-gray-500">
          — {cite}
        </footer>
      ) : null}
    </blockquote>
  );
}
