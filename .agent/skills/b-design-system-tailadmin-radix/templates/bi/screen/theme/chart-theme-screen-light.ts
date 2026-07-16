import type { ApexOptions } from "apexcharts";

import { deepMergeOptions } from "../../../lib/merge-options";
import { screenChartSeriesColors } from "./chart-theme-screen-dark";

const baseScreenChartThemeLight: ApexOptions = {
  colors: [...screenChartSeriesColors],
  chart: {
    background: "transparent",
    fontFamily: "Outfit, sans-serif",
    toolbar: { show: false },
  },
  grid: {
    borderColor: "#e2e8f0",
    strokeDashArray: 4,
  },
  xaxis: {
    labels: {
      style: {
        colors: "#64748b",
        fontSize: "11px",
      },
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: {
        colors: "#64748b",
        fontSize: "11px",
      },
    },
  },
  legend: {
    position: "top",
    horizontalAlign: "right",
    fontSize: "11px",
    labels: { colors: "#475569" },
  },
  tooltip: {
    theme: "light",
    style: { fontSize: "11px" },
  },
  dataLabels: { enabled: false },
};

export const screenChartThemeLight = baseScreenChartThemeLight;

export function applyScreenChartThemeLight(overrides?: ApexOptions): ApexOptions {
  return deepMergeOptions(
    baseScreenChartThemeLight as Record<string, unknown>,
    overrides as Record<string, unknown> | undefined,
  ) as ApexOptions;
}
