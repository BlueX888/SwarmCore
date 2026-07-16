import * as React from "react";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";

import { applyScreenChartTheme } from "../theme/chart-theme-screen-dark";
import { applyScreenChartThemeLight } from "../theme/chart-theme-screen-light";

export type ScreenRadarChartProps = {
  categories: string[];
  series: { name: string; data: number[] }[];
  height?: number;
  theme?: "dark" | "light";
};

/**
 * 雷达图 — 5 轴双系列（男/女或设备 A/B），浅色 L4 适用。
 * @see prd/data-screens/atoms.md#task-ds-a08
 */
export function ScreenRadarChart({
  categories,
  series,
  height = 220,
  theme = "light",
}: ScreenRadarChartProps) {
  const options: ApexOptions = {
    ...(theme === "light" ? applyScreenChartThemeLight() : applyScreenChartTheme()),
    chart: { type: "radar", background: "transparent", toolbar: { show: false } },
    xaxis: { categories },
    yaxis: { show: false, min: 0, max: 100 },
    stroke: { width: 2 },
    fill: { opacity: 0.15 },
    markers: { size: 3 },
    plotOptions: {
      radar: {
        polygons: {
          strokeColors: theme === "light" ? "#e2e8f0" : "rgba(255,255,255,0.12)",
          connectorColors: theme === "light" ? "#e2e8f0" : "rgba(255,255,255,0.12)",
        },
      },
    },
  };

  return (
    <div data-screen-radar-chart>
      <Chart type="radar" height={height} width="100%" options={options} series={series} />
    </div>
  );
}
