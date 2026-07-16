import * as React from "react";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";

import { cn } from "../lib/cn";
import { applyScreenChartTheme } from "../theme/chart-theme-screen-dark";
import { applyScreenChartThemeLight } from "../theme/chart-theme-screen-light";
import { screenTokens } from "../theme/screen-tokens";

export type GaugeItem = {
  label: string;
  value: number;
  unit?: string;
  max?: number;
};

export type ScreenGaugeRingProps = {
  items: GaugeItem[];
  height?: number;
  theme?: "dark" | "light";
  className?: string;
};

/**
 * 单环/多环仪表 — 0–100 百分比，停车场 KPI、绿化进度适用。
 * @see prd/data-screens/atoms.md#task-ds-a13
 */
export function ScreenGaugeRing({
  items,
  height = 120,
  theme = "dark",
  className,
}: ScreenGaugeRingProps) {
  if (items.length === 1) {
    const item = items[0]!;
    const max = item.max ?? 100;
    const pct = Math.min(100, Math.round((item.value / max) * 100));

    const options: ApexOptions = {
      ...(theme === "light" ? applyScreenChartThemeLight() : applyScreenChartTheme()),
      chart: { type: "radialBar", background: "transparent", sparkline: { enabled: true } },
      plotOptions: {
        radialBar: {
          hollow: { size: "62%" },
          track: { background: theme === "light" ? "#e2e8f0" : "rgba(255,255,255,0.08)" },
          dataLabels: {
            name: { show: true, color: theme === "light" ? "#64748b" : "#94a3b8", fontSize: "11px" },
            value: {
              show: true,
              fontSize: "18px",
              fontWeight: 700,
              color: theme === "light" ? "#0f172a" : "#f8fafc",
              formatter: () => `${item.value}${item.unit ?? ""}`,
            },
          },
        },
      },
      labels: [item.label],
      colors: [theme === "light" ? "#0ea5e9" : "#22d3ee"],
    };

    return (
      <div data-screen-gauge-ring className={className}>
        <Chart type="radialBar" height={height} width="100%" options={options} series={[pct]} />
      </div>
    );
  }

  return (
    <div
      data-screen-gauge-ring
      className={cn("grid grid-cols-2 gap-2", className)}
      style={{ minHeight: height }}
    >
      {items.map((item) => {
        const max = item.max ?? 100;
        const pct = Math.min(100, Math.round((item.value / max) * 100));
        return (
          <div
            key={item.label}
            className="flex flex-col items-center justify-center rounded-md border border-white/10 bg-white/5 px-2 py-2 text-center"
          >
            <div
              className="relative flex h-14 w-14 items-center justify-center rounded-full"
              style={{
                background: `conic-gradient(${theme === "light" ? "#0ea5e9" : "#22d3ee"} ${pct * 3.6}deg, rgba(255,255,255,0.08) 0deg)`,
              }}
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900/90 text-xs font-bold tabular-nums text-white">
                {pct}%
              </span>
            </div>
            <p className={cn("mt-1", screenTokens.kpiLabel)}>{item.label}</p>
            <p className="text-xs font-semibold tabular-nums text-white">
              {item.value}
              {item.unit ?? ""}
            </p>
          </div>
        );
      })}
    </div>
  );
}
