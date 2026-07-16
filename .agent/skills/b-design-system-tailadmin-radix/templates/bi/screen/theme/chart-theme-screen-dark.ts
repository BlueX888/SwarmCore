import type { ApexOptions } from "apexcharts";

import { deepMergeOptions } from "../../../lib/merge-options";

export const screenChartSeriesColors = [
  "#22d3ee",
  "#4ade80",
  "#a78bfa",
  "#fbbf24",
  "#f87171",
] as const;

const baseScreenChartThemeDark: ApexOptions = {
  colors: [...screenChartSeriesColors],
  chart: {
    background: "transparent",
    fontFamily: "Outfit, sans-serif",
    toolbar: { show: false },
    animations: {
      enabled: true,
      speed: 450,
    },
  },
  grid: {
    borderColor: "rgba(255,255,255,0.15)",
    strokeDashArray: 4,
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } },
  },
  xaxis: {
    labels: {
      style: {
        colors: "rgba(255,255,255,0.7)",
        fontSize: "11px",
      },
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: {
      style: {
        colors: "rgba(255,255,255,0.7)",
        fontSize: "11px",
      },
    },
  },
  legend: {
    position: "top",
    horizontalAlign: "right",
    fontSize: "11px",
    labels: { colors: "rgba(255,255,255,0.7)" },
  },
  tooltip: {
    theme: "dark",
    style: { fontSize: "11px" },
  },
  dataLabels: { enabled: false },
  stroke: {
    show: true,
    width: 2,
    curve: "smooth",
  },
  fill: {
    type: "gradient",
    gradient: {
      shadeIntensity: 0.4,
      opacityFrom: 0.45,
      opacityTo: 0.05,
      stops: [0, 90, 100],
    },
  },
};

export const screenChartThemeDark = baseScreenChartThemeDark;

export function applyScreenChartTheme(
  overrides?: ApexOptions,
  theme: "dark" | "light" = "dark",
): ApexOptions {
  if (theme === "light") {
    return deepMergeOptions(
      baseScreenChartThemeDark as Record<string, unknown>,
      overrides as Record<string, unknown> | undefined,
    ) as ApexOptions;
  }
  return deepMergeOptions(
    baseScreenChartThemeDark as Record<string, unknown>,
    overrides as Record<string, unknown> | undefined,
  ) as ApexOptions;
}
