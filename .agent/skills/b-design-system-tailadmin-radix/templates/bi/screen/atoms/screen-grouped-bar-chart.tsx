import * as React from "react";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";

import { applyScreenChartTheme } from "../theme/chart-theme-screen-dark";
import { applyScreenChartThemeLight } from "../theme/chart-theme-screen-light";

export type ScreenGroupedBarChartProps = {
  categories: string[];
  series: { name: string; data: number[] }[];
  horizontal?: boolean;
  stacked?: boolean;
  height?: number;
  theme?: "dark" | "light";
};

/**
 * 分组柱图 — 双系列分组，横向/纵向，DS-06 消费金额与增长柱图适用。
 * @see prd/data-screens/atoms.md#task-ds-a10
 */
export function ScreenGroupedBarChart({
  categories,
  series,
  horizontal = false,
  stacked = false,
  height = 220,
  theme = "light",
}: ScreenGroupedBarChartProps) {
  const options: ApexOptions = {
    ...(theme === "light" ? applyScreenChartThemeLight() : applyScreenChartTheme()),
    chart: {
      type: "bar",
      background: "transparent",
      stacked,
      toolbar: { show: false },
    },
    plotOptions: {
      bar: {
        horizontal,
        columnWidth: horizontal ? "55%" : "62%",
        barHeight: horizontal ? "62%" : undefined,
        borderRadius: 4,
      },
    },
    xaxis: { categories },
    dataLabels: { enabled: false },
    legend: { position: "top", horizontalAlign: "right" },
  };

  return (
    <div data-screen-grouped-bar-chart>
      <Chart type="bar" height={height} width="100%" options={options} series={series} />
    </div>
  );
}
