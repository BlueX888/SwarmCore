import * as React from "react";
import { ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

const Pagination = ({ className, ...props }: React.ComponentProps<"nav">) => (
  <nav
    role="navigation"
    aria-label="分页"
    className={cn("mx-auto flex w-full justify-center", className)}
    {...props}
  />
);
Pagination.displayName = "Pagination";

const PaginationContent = React.forwardRef<
  HTMLUListElement,
  React.ComponentProps<"ul">
>(({ className, ...props }, ref) => (
  <ul
    ref={ref}
    className={cn("flex flex-row items-center gap-1", className)}
    {...props}
  />
));
PaginationContent.displayName = "PaginationContent";

const PaginationItem = React.forwardRef<
  HTMLLIElement,
  React.ComponentProps<"li">
>(({ className, ...props }, ref) => (
  <li ref={ref} className={cn("", className)} {...props} />
));
PaginationItem.displayName = "PaginationItem";

type PaginationLinkProps = {
  isActive?: boolean;
} & React.ComponentProps<"button">;

const PaginationLink = ({
  className,
  isActive,
  disabled,
  ...props
}: PaginationLinkProps) => (
  <button
    type="button"
    aria-current={isActive ? "page" : undefined}
    disabled={disabled}
    className={cn(
      "inline-flex size-10 items-center justify-center rounded-lg text-sm font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-3 focus-visible:ring-brand-500/20 disabled:pointer-events-none disabled:opacity-50",
      isActive
        ? "bg-brand-500 text-white hover:bg-brand-600"
        : "text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-white/5",
      className,
    )}
    {...props}
  />
);
PaginationLink.displayName = "PaginationLink";

const PaginationPrevious = ({
  className,
  ...props
}: React.ComponentProps<typeof PaginationLink>) => (
  <PaginationLink
    aria-label="上一页"
    className={cn("h-10 w-auto gap-1 px-2.5 whitespace-nowrap", className)}
    {...props}
  >
    <ChevronLeft className="size-4" />
    <span className="sr-only sm:not-sr-only sm:inline">上一页</span>
  </PaginationLink>
);
PaginationPrevious.displayName = "PaginationPrevious";

const PaginationNext = ({
  className,
  ...props
}: React.ComponentProps<typeof PaginationLink>) => (
  <PaginationLink
    aria-label="下一页"
    className={cn("h-10 w-auto gap-1 px-2.5 whitespace-nowrap", className)}
    {...props}
  >
    <span className="sr-only sm:not-sr-only sm:inline">下一页</span>
    <ChevronRight className="size-4" />
  </PaginationLink>
);
PaginationNext.displayName = "PaginationNext";

const PaginationEllipsis = ({
  className,
  ...props
}: React.ComponentProps<"span">) => (
  <span
    aria-hidden
    className={cn(
      "flex size-10 items-center justify-center text-gray-500",
      className,
    )}
    {...props}
  >
    <MoreHorizontal className="size-4" />
    <span className="sr-only">更多页</span>
  </span>
);
PaginationEllipsis.displayName = "PaginationEllipsis";

export type PaginationSizeChangerProps = {
  pageSize: number;
  pageSizeOptions?: number[];
  onPageSizeChange: (size: number) => void;
  className?: string;
};

export function PaginationSizeChanger({
  pageSize,
  pageSizeOptions = [10, 20, 50, 100],
  onPageSizeChange,
  className,
}: PaginationSizeChangerProps) {
  return (
    <label className={cn("flex items-center gap-2 text-theme-sm text-gray-500 dark:text-gray-400", className)}>
      每页
      <select
        className="rounded-lg border border-gray-200 bg-white px-2 py-1 text-sm text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-white/90"
        value={pageSize}
        onChange={(event) => onPageSizeChange(Number(event.target.value))}
        aria-label="每页条数"
      >
        {pageSizeOptions.map((size) => (
          <option key={size} value={size}>
            {size}
          </option>
        ))}
      </select>
      条
    </label>
  );
}

export {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext,
  PaginationEllipsis,
  PaginationSizeChanger,
};
