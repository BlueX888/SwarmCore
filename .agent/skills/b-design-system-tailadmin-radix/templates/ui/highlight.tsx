import * as React from "react";
import { cn } from "@/lib/utils";

export type HighlightProps = {
  query: string;
  children: string;
  caseSensitive?: boolean;
  className?: string;
  markClassName?: string;
};

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function Highlight({
  query,
  children,
  caseSensitive = false,
  className,
  markClassName,
}: HighlightProps) {
  if (!query.trim()) {
    return <span className={className}>{children}</span>;
  }

  const flags = caseSensitive ? "g" : "gi";
  const parts = children.split(new RegExp(`(${escapeRegExp(query)})`, flags));

  return (
    <span className={className}>
      {parts.map((part, index) =>
        (caseSensitive ? part === query : part.toLowerCase() === query.toLowerCase()) ? (
          <mark
            key={index}
            className={cn(
              "rounded bg-warning-100 px-0.5 text-inherit dark:bg-warning-500/20",
              markClassName,
            )}
          >
            {part}
          </mark>
        ) : (
          <React.Fragment key={index}>{part}</React.Fragment>
        ),
      )}
    </span>
  );
}
