import * as React from "react";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";

import { applyScreenChartTheme } from "../theme/chart-theme-screen-dark";
import { applyScreenChartThemeLight } from "../theme/chart-theme-screen-light";

export type ScreenLineAreaChartProps = {
  categories: string[];
  series: { name: string; data: number[] }[];
  smooth?: boolean;
  area?: boolean;
  height?: number;
  theme?: "dark" | "light";
};

export function ScreenLineAreaChart({
  categories,
  series,
  smooth = true,
  area = true,
  height = 240,
  theme = "dark",
}: ScreenLineAreaChartProps) {
  const options: ApexOptions = {
    ...(theme === "light" ? applyScreenChartThemeLight() : applyScreenChartTheme()),
    chart: { type: area ? "area" : "line", background: "transparent" },
    xaxis: { categories },
    stroke: {
      curve: smooth ? "smooth" : "straight",
      width: 2,
    },
    fill: area
      ? {
          type: "gradient",
          gradient: {
            shadeIntensity: 0.35,
            opacityFrom: 0.45,
            opacityTo: 0.05,
            stops: [0, 90, 100],
          },
        }
      : { opacity: 1 },
  };

  return (
    <div data-screen-line-area-chart>
      <Chart
        type={area ? "area" : "line"}
        height={height}
        width="100%"
        options={options}
        series={series}
      />
    </div>
  );
}
