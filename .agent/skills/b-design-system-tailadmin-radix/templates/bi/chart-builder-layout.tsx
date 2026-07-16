import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { FieldListPanel, type BiFieldDef } from "./field-list-panel";
import { ChartConfigPanel, type EncodingValue } from "./chart-config-panel";
import { ChartPanel, type ChartPanelStatus } from "./chart-panel";

export type ChartType =
  | "bar"
  | "line"
  | "area"
  | "pie"
  | "radar"
  | "funnel"
  | "table";

export type ChartBuilderLayoutProps = {
  mode?: "edit" | "view";
  fields: BiFieldDef[];
  chartType: ChartType;
  onChartTypeChange?: (type: ChartType) => void;
  encodings: EncodingValue[];
  previewStatus?: ChartPanelStatus;
  preview?: React.ReactNode;
  className?: string;
};

const chartTypes: { id: ChartType; label: string }[] = [
  { id: "bar", label: "柱状图" },
  { id: "line", label: "折线图" },
  { id: "area", label: "面积图" },
  { id: "pie", label: "饼图" },
  { id: "radar", label: "雷达图" },
  { id: "funnel", label: "漏斗图" },
  { id: "table", label: "表格" },
];

/**
 * Three-column chart builder — fields | preview | encodings.
 * @see references/layout-patterns/bi-chart-builder.md
 */
export function ChartBuilderLayout({
  mode = "edit",
  fields,
  chartType,
  onChartTypeChange,
  encodings,
  previewStatus = "ready",
  preview,
  className,
}: ChartBuilderLayoutProps) {
  return (
    <div className={cn("flex min-h-[480px] flex-col overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-gray-200 px-4 py-3 dark:border-gray-800">
        <div className="flex flex-wrap gap-1" role="tablist" aria-label="图表类型">
          {chartTypes.map((t) => (
            <Button
              key={t.id}
              type="button"
              size="sm"
              variant={chartType === t.id ? "default" : "outline"}
              onClick={() => onChartTypeChange?.(t.id)}
              disabled={mode === "view"}
              role="tab"
              aria-selected={chartType === t.id}
            >
              {t.label}
            </Button>
          ))}
        </div>
        {mode === "edit" ? (
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              运行查询
            </Button>
            <Button size="sm">保存</Button>
          </div>
        ) : null}
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)_300px]">
        <FieldListPanel fields={fields} className="hidden min-h-0 lg:flex" />
        <ChartPanel status={previewStatus} title="预览" className="rounded-none border-0">
          {preview}
        </ChartPanel>
        <ChartConfigPanel encodings={encodings} className="hidden min-h-0 lg:flex" />
      </div>
    </div>
  );
}
