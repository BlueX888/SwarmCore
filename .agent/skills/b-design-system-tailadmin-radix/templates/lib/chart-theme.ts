import type { ApexOptions } from "apexcharts";

import { deepMergeOptions } from "./merge-options";

/**
 * TailAdmin semantic palette — hex values for ApexCharts runtime.
 * Each key maps to token-index.md and host/example CSS variables (see chartPaletteCssVars).
 */
export const chartPalette = {
  brand: "#465fff", // token: brand-500 · CSS: --brand-500
  purple: "#7a5af8", // token: theme-purple-500 · CSS: --purple-500
  success: "#12b76a", // token: success-500 · CSS: --success-500
  info: "#0ba5ec", // token: blue-light-500 · CSS: --blue-light-500
  pink: "#ee46bc", // token: theme-pink-500
} as const;

/** CSS custom property names — align with the example app :root and host @theme */
export const chartPaletteCssVars = {
  brand: "var(--brand-500)",
  purple: "var(--purple-500)",
  success: "var(--success-500)",
  info: "var(--blue-light-500)",
  pink: "var(--theme-pink-500, #ee46bc)",
} as const;

/** Resolve palette for CSS-based chart mocks (non-ApexCharts) */
export const chartPaletteForCss = Object.fromEntries(
  Object.entries(chartPalette).map(([key, hex]) => [
    key,
    chartPaletteCssVars[key as keyof typeof chartPaletteCssVars] ?? hex,
  ]),
) as Record<keyof typeof chartPalette, string>;

export const chartColors = Object.values(chartPalette);

export const chartFontFamily = "Outfit, sans-serif";

export const chartAxisLabelStyle = {
  colors: "#667085",
  fontSize: "12px",
} as const;

export const chartGridBorderColor = "#e4e7ec";

const baseChartOptions: ApexOptions = {
  colors: chartColors,
  chart: {
    fontFamily: chartFontFamily,
    toolbar: { show: false },
    animations: {
      enabled: true,
      speed: 450,
      animateGradually: { enabled: true, delay: 80 },
      dynamicAnimation: { enabled: true, speed: 300 },
    },
  },
  dataLabels: { enabled: false },
  grid: {
    borderColor: chartGridBorderColor,
    strokeDashArray: 0,
    yaxis: { lines: { show: true } },
  },
  xaxis: {
    labels: { style: chartAxisLabelStyle },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: { style: chartAxisLabelStyle },
  },
  legend: {
    fontFamily: chartFontFamily,
    labels: { colors: "#344054" },
  },
  stroke: {
    show: true,
    width: 4,
    colors: ["transparent"],
  },
  markers: {
    size: 0,
    strokeColors: "#fff",
    strokeWidth: 2,
    hover: { size: 6 },
  },
  states: {
    hover: { filter: { type: "lighten", value: 0.04 } },
    active: {
      allowMultipleDataPointsSelection: false,
      filter: { type: "darken", value: 0.08 },
    },
  } as NonNullable<ApexOptions["states"]>,
  tooltip: {
    enabled: true,
    theme: "light",
    shared: true,
    intersect: false,
  },
};

/** Deep merge — `chart.toolbar.show` 等嵌套 key 不会覆盖整个 chart 对象 */
export function getBaseChartOptions(overrides?: ApexOptions): ApexOptions {
  return deepMergeOptions(
    baseChartOptions as Record<string, unknown>,
    overrides as Record<string, unknown> | undefined
  ) as ApexOptions;
}

export const barChartPlotOptions: NonNullable<ApexOptions["plotOptions"]> = {
  bar: {
    horizontal: false,
    columnWidth: "39%",
    borderRadius: 5,
    borderRadiusApplication: "end",
  },
};

export const lineChartStrokeOptions: NonNullable<ApexOptions["stroke"]> = {
  curve: "smooth",
  width: 2,
};

export const areaChartFillOptions: NonNullable<ApexOptions["fill"]> = {
  type: "gradient",
  gradient: {
    shadeIntensity: 1,
    opacityFrom: 0.35,
    opacityTo: 0,
    stops: [0, 90, 100],
  },
};

export const donutChartPlotOptions: NonNullable<ApexOptions["plotOptions"]> = {
  pie: {
    donut: {
      size: "70%",
      labels: {
        show: true,
        name: { fontSize: "14px", color: "#667085" },
        value: { fontSize: "20px", fontWeight: 600, color: "#101828" },
        total: {
          show: true,
          label: "Total",
          fontSize: "14px",
          color: "#667085",
        },
      },
    },
  },
};

/** Copy into host src/index.css — dark mode uses html.dark */
export const apexChartsCssOverrides = `
.apexcharts-legend-text {
  @apply !text-gray-700 dark:!text-gray-400;
}

.apexcharts-text {
  @apply !fill-gray-700 dark:!fill-gray-400;
}

.apexcharts-tooltip.apexcharts-theme-light {
  @apply gap-1 !rounded-lg !border-gray-200 p-3 !shadow-theme-sm dark:!border-gray-800 dark:!bg-gray-900;
}

.apexcharts-tooltip-series-group,
.apexcharts-tooltip-y-group {
  @apply !p-0;
}

.apexcharts-tooltip-title {
  @apply !mb-0 !border-b-0 !bg-transparent !p-0 !text-[10px] !leading-4 !text-gray-800 dark:!text-white/90;
}

.apexcharts-tooltip-text {
  @apply !text-theme-xs !text-gray-700 dark:!text-white/90;
}

.apexcharts-tooltip-text-y-value {
  @apply !font-medium;
}

.apexcharts-gridline {
  @apply !stroke-gray-100 dark:!stroke-gray-800;
}
`.trim();

export function createBarChartOptions(
  categories: string[],
  overrides?: ApexOptions,
): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "bar", height: 180 },
    plotOptions: barChartPlotOptions,
    xaxis: { categories },
    ...overrides,
  });
}

export function createHorizontalBarChartOptions(
  categories: string[],
  overrides?: ApexOptions,
): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "bar", height: 240 },
    plotOptions: {
      bar: {
        ...barChartPlotOptions.bar,
        horizontal: true,
        barHeight: "52%",
      },
    },
    xaxis: { categories },
    ...overrides,
  });
}

export function createStackedBarChartOptions(
  categories: string[],
  overrides?: ApexOptions,
): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "bar", height: 260, stacked: true },
    plotOptions: barChartPlotOptions,
    xaxis: { categories },
    legend: { position: "top", horizontalAlign: "right" },
    ...overrides,
  });
}

export function createLineChartOptions(
  categories: string[],
  overrides?: ApexOptions,
): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "line", height: 180 },
    stroke: lineChartStrokeOptions,
    xaxis: { categories },
    ...overrides,
  });
}

export function createAreaChartOptions(
  categories: string[],
  overrides?: ApexOptions,
): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "area", height: 240 },
    stroke: lineChartStrokeOptions,
    fill: areaChartFillOptions,
    xaxis: { categories },
    ...overrides,
  });
}

export function createPieChartOptions(overrides?: ApexOptions): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "pie", height: 280 },
    legend: { position: "bottom" },
    stroke: { show: false },
    ...overrides,
  });
}

export function createDonutChartOptions(overrides?: ApexOptions): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "donut", height: 280 },
    plotOptions: donutChartPlotOptions,
    legend: { position: "bottom" },
    ...overrides,
  });
}

export function createRadialBarChartOptions(overrides?: ApexOptions): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "radialBar", height: 280 },
    plotOptions: {
      radialBar: {
        hollow: { size: "58%" },
        track: { background: "#f2f4f7" },
        dataLabels: {
          name: { color: "#667085", fontSize: "14px" },
          value: { color: "#101828", fontSize: "28px", fontWeight: 600 },
        },
      },
    },
    stroke: { lineCap: "round" },
    ...overrides,
  });
}

export function createRadarChartOptions(
  categories: string[],
  overrides?: ApexOptions,
): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "radar", height: 300 },
    xaxis: { categories },
    stroke: { width: 2 },
    fill: { opacity: 0.18 },
    markers: { size: 4 },
    ...overrides,
  });
}

export function createFunnelChartOptions(
  categories: string[],
  overrides?: ApexOptions,
): ApexOptions {
  return getBaseChartOptions({
    chart: { type: "bar", height: 260 },
    plotOptions: {
      bar: {
        horizontal: true,
        isFunnel: true,
        borderRadius: 4,
      },
    },
    xaxis: { categories },
    ...overrides,
  });
}
