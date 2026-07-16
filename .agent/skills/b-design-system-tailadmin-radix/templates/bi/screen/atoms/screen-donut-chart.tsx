import * as React from "react";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";

import { applyScreenChartTheme } from "../theme/chart-theme-screen-dark";
import { applyScreenChartThemeLight } from "../theme/chart-theme-screen-light";

export type ScreenDonutChartProps = {
  series: { name: string; value: number }[];
  centerLabel?: string;
  height?: number;
  theme?: "dark" | "light";
};

export function ScreenDonutChart({
  series,
  centerLabel,
  height = 220,
  theme = "dark",
}: ScreenDonutChartProps) {
  const total = series.reduce((sum, item) => sum + item.value, 0);

  const options: ApexOptions = {
    ...(theme === "light" ? applyScreenChartThemeLight() : applyScreenChartTheme()),
    chart: { type: "donut", background: "transparent" },
    labels: series.map((item) => item.name),
    legend: { show: true, position: "bottom" },
    // Area-chart gradient fill from the shared theme makes donut slices nearly invisible.
    fill: { type: "solid", opacity: 1 },
    stroke: {
      show: true,
      width: 2,
      colors: theme === "light" ? ["#ffffff"] : ["#0f172a"],
    },
    plotOptions: {
      pie: {
        donut: {
          size: "68%",
          labels: {
            show: Boolean(centerLabel),
            name: { show: false },
            value: { show: false },
            total: {
              show: Boolean(centerLabel),
              label: centerLabel ?? "",
              formatter: () => `${total}`,
              color: theme === "light" ? "#0f172a" : "#e2e8f0",
              fontSize: "14px",
            },
          },
        },
      },
    },
  };

  return (
    <div data-screen-donut-chart>
      <Chart
        type="donut"
        height={height}
        width="100%"
        options={options}
        series={series.map((item) => item.value)}
      />
    </div>
  );
}
