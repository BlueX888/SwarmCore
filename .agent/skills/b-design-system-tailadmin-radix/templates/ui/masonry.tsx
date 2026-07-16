import * as React from "react";
import { cn } from "@/lib/utils";

export type MasonryProps = {
  columns?: number;
  gap?: number;
  children: React.ReactNode;
  className?: string;
};

export function Masonry({
  columns = 3,
  gap = 16,
  children,
  className,
}: MasonryProps) {
  return (
    <div
      className={cn(className)}
      style={{
        columnCount: columns,
        columnGap: gap,
      }}
    >
      {React.Children.map(children, (child, index) => (
        <div
          key={index}
          className="mb-4 break-inside-avoid"
          style={{ marginBottom: gap }}
        >
          {child}
        </div>
      ))}
    </div>
  );
}
