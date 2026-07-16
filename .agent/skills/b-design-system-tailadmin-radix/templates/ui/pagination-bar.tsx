import * as React from "react";
import { cn } from "@/lib/utils";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationSizeChanger,
} from "@/components/ui/pagination";
import { Input } from "@/components/ui/input";

export type PaginationBarProps = {
  current: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  pageSizeOptions?: number[];
  onChange: (page: number, pageSize: number) => void;
  className?: string;
};

function buildPageNumbers(current: number, totalPages: number): (number | "ellipsis")[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }
  const pages: (number | "ellipsis")[] = [1];
  if (current > 3) pages.push("ellipsis");
  const start = Math.max(2, current - 1);
  const end = Math.min(totalPages - 1, current + 1);
  for (let p = start; p <= end; p++) pages.push(p);
  if (current < totalPages - 2) pages.push("ellipsis");
  pages.push(totalPages);
  return pages;
}

export function PaginationBar({
  current,
  pageSize,
  total,
  showSizeChanger = false,
  showQuickJumper = false,
  pageSizeOptions = [10, 20, 50, 100],
  onChange,
  className,
}: PaginationBarProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safeCurrent = Math.min(Math.max(1, current), totalPages);
  const [jumpValue, setJumpValue] = React.useState("");

  const emit = (page: number, size = pageSize) => {
    onChange(Math.min(Math.max(1, page), totalPages), size);
  };

  const handleJump = (event: React.FormEvent) => {
    event.preventDefault();
    const parsed = Number.parseInt(jumpValue, 10);
    if (!Number.isNaN(parsed)) {
      emit(parsed);
      setJumpValue("");
    }
  };

  const pageItems = buildPageNumbers(safeCurrent, totalPages);

  return (
    <div
      className={cn(
        "flex w-full flex-wrap items-center justify-between gap-4",
        className,
      )}
    >
      <div className="flex flex-wrap items-center gap-4">
        {showSizeChanger ? (
          <PaginationSizeChanger
            pageSize={pageSize}
            pageSizeOptions={pageSizeOptions}
            onPageSizeChange={(size) => onChange(1, size)}
          />
        ) : (
          <span className="text-theme-sm text-gray-500 dark:text-gray-400">
            共 {total} 条
          </span>
        )}
        {showQuickJumper ? (
          <form onSubmit={handleJump} className="flex items-center gap-2 text-theme-sm text-gray-500 dark:text-gray-400">
            跳至
            <Input
              className="h-9 w-16 px-2 text-center"
              value={jumpValue}
              onChange={(e) => setJumpValue(e.target.value)}
              inputMode="numeric"
              aria-label="跳转页码"
            />
            页
          </form>
        ) : null}
      </div>
      <Pagination className="mx-0 w-auto justify-end">
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              disabled={safeCurrent <= 1}
              onClick={() => emit(safeCurrent - 1)}
            />
          </PaginationItem>
          {pageItems.map((item, idx) =>
            item === "ellipsis" ? (
              <PaginationItem key={`e-${idx}`}>
                <PaginationEllipsis />
              </PaginationItem>
            ) : (
              <PaginationItem key={item}>
                <PaginationLink
                  isActive={item === safeCurrent}
                  onClick={() => emit(item)}
                  aria-label={`第 ${item} 页`}
                >
                  {item}
                </PaginationLink>
              </PaginationItem>
            ),
          )}
          <PaginationItem>
            <PaginationNext
              disabled={safeCurrent >= totalPages}
              onClick={() => emit(safeCurrent + 1)}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  );
}
