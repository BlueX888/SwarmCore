import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Spinner } from "@/components/ui/spinner";

export type ExportFormat = "png" | "pdf" | "excel" | "csv";

export type ExportContext = "chart" | "dashboard" | "data-screen" | "table";

const formatLabel: Record<ExportFormat, string> = {
  png: "PNG 图片",
  pdf: "PDF 文档",
  excel: "Excel 表格",
  csv: "CSV 明细",
};

const defaultFormatsByContext: Record<ExportContext, ExportFormat[]> = {
  chart: ["png", "pdf", "csv"],
  dashboard: ["png", "pdf", "excel"],
  "data-screen": ["png", "pdf"],
  table: ["csv", "excel"],
};

export type ExportMenuProps = {
  context?: ExportContext;
  formats?: ExportFormat[];
  /** 大屏画布尺寸，如 1920×1080 */
  dataScreenSize?: string;
  /** 导出使用的主题 */
  theme?: "light" | "dark" | "current";
  loading?: boolean;
  disabled?: boolean;
  label?: string;
  onExport?: (format: ExportFormat) => void;
  className?: string;
};

/**
 * BI 导出菜单 — PNG/PDF/Excel/CSV，大屏可记录画布尺寸与主题。
 * @see references/layout-patterns/bi-export-subscription.md
 */
export function ExportMenu({
  context = "dashboard",
  formats,
  dataScreenSize,
  theme = "current",
  loading = false,
  disabled = false,
  label = "导出",
  onExport,
  className,
}: ExportMenuProps) {
  const available = formats ?? defaultFormatsByContext[context];
  const themeLabel =
    theme === "current" ? "跟随当前主题" : theme === "dark" ? "深色主题" : "浅色主题";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          type="button"
          disabled={disabled || loading}
          className={cn(className)}
        >
          {loading ? (
            <>
              <Spinner className="mr-2 size-4" />
              导出中…
            </>
          ) : (
            <>
              {label}
              <span className="ml-1 opacity-50" aria-hidden>
                ▾
              </span>
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[200px]">
        <DropdownMenuLabel className="text-theme-xs font-normal text-gray-500">
          选择导出格式
        </DropdownMenuLabel>
        {context === "data-screen" && dataScreenSize ? (
          <>
            <DropdownMenuLabel className="text-theme-xs font-normal text-gray-500">
              画布 {dataScreenSize} · {themeLabel}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
          </>
        ) : null}
        {available.map((format) => (
          <DropdownMenuItem key={format} onSelect={() => onExport?.(format)}>
            {formatLabel[format]}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
