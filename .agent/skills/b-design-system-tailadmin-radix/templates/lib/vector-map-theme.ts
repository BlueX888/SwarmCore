/** TailAdmin Vector Map theme — @react-jvectormap presets and CSS helpers */

import type { RefObject } from "react";

export const vectorMapPageStackClass = "flex flex-col gap-6";

export const vectorMapCardShellClass =
  "rounded-2xl border border-gray-200 bg-white p-5 sm:p-6 dark:border-gray-800 dark:bg-white/[0.03]";

export const vectorMapCardTitleClass =
  "text-lg font-semibold text-gray-800 dark:text-white/90";

export const vectorMapCardSubtitleClass =
  "text-theme-sm mt-1 text-gray-500 dark:text-gray-400";

export const vectorMapInnerWrapperClass =
  "overflow-hidden rounded-2xl border border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900";

export const vectorMapContainerClass = "relative" as const;

export const vectorMapHeightStyle = { height: "274px" } as const;

export const vectorMapZoomWrapperClass = "absolute bottom-3 right-3 z-10";

export const vectorMapZoomStackClass =
  "flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900";

export const vectorMapZoomButtonClass =
  "flex h-9 w-9 items-center justify-center text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-white/5 dark:hover:text-white";

export const vectorMapZoomButtonTopClass = `${vectorMapZoomButtonClass} border-b border-gray-200 dark:border-gray-800`;

export const defaultVectorMapZoomOptions = {
  zoomOnScroll: false,
  zoomAnimate: true,
  zoomStep: 1.5,
  zoomMax: 12,
  zoomMin: 1,
} as const;

/** Gray base map with brand markers — VectorMapOne */
export const globalMarkerRegionStyle = {
  initial: {
    fontFamily: "Outfit",
    fill: "#D9D9D9",
    stroke: "none",
    strokeWidth: 0,
    strokeOpacity: 0,
  },
  hover: {
    fillOpacity: 0.7,
    fill: "#465FFF",
    cursor: "pointer",
  },
  selected: { fill: "#465FFF" },
  selectedHover: {},
} as const;

export const globalMarkerStyle = {
  initial: { strokeWidth: 1, fill: "#465FFF", fillOpacity: 1 },
  hover: { fill: "#3538CD", fillOpacity: 1 },
  selected: {},
  selectedHover: {},
} as const;

/** Blue-scale traffic map — VectorMapTwo */
export const trafficRegionStyle = {
  initial: {
    fill: "#C5D8FF",
    fillOpacity: 1,
    stroke: "white",
    strokeWidth: 0.5,
    strokeOpacity: 1,
  },
  hover: {
    fillOpacity: 0.8,
    fill: "#465FFF",
    cursor: "pointer",
  },
  selected: { fill: "#3538CD" },
  selectedHover: {},
} as const;

/** Per-country traffic fills for #mapTrafficAnalytics injector */
export const trafficRegionFills: Record<string, string> = {
  US: "#3538CD",
  CA: "#8098F9",
  CN: "#8098F9",
  FR: "#9CB9FF",
  BR: "#9CB9FF",
  RU: "#9CB9FF",
  AU: "#ADC6FF",
};

/** US state heatmap — VectorMapThree */
export const usHeatmapRegionStyle = {
  initial: {
    fill: "#C5D8FF",
    fillOpacity: 1,
    stroke: "white",
    strokeWidth: 2,
    strokeOpacity: 1,
  },
  hover: {
    fillOpacity: 0.8,
    fill: "#465FFF",
    cursor: "pointer",
  },
  selected: { fill: "#465FFF" },
  selectedHover: {},
} as const;

export const usHeatmapMarkerStyle = {
  initial: { fill: "#465FFF", stroke: "white", strokeWidth: 2 },
  hover: { fill: "#3538CD" },
  selected: {},
  selectedHover: {},
} as const;

/** Highlighted US states for customer density map */
export const usStateHeatmapFills: Record<string, string> = {
  "US-CA": "#465FFF",
  "US-NV": "#465FFF",
  "US-NY": "#3538CD",
  "US-FL": "#3538CD",
  "US-MI": "#3538CD",
  "US-WA": "#3538CD",
  "US-TX": "#8098F9",
  "US-IL": "#8098F9",
  "US-PA": "#8098F9",
  "US-OH": "#8098F9",
  "US-GA": "#8098F9",
  "US-NC": "#8098F9",
  "US-CO": "#9CB9FF",
  "US-AZ": "#9CB9FF",
};

/** Inject per-region fill styles for traffic analytics map */
export function createTrafficRegionStyleInjector(
  containerId: string,
  fills: Record<string, string> = trafficRegionFills,
): () => void {
  const styleId = `${containerId}-traffic-styles`;
  const rules = Object.entries(fills)
    .map(([code, fill]) => `#${containerId} path[data-code="${code}"] { fill: ${fill} !important; }`)
    .join("\n");
  const style = document.createElement("style");
  style.id = styleId;
  style.innerHTML = rules;
  document.head.appendChild(style);
  return () => {
    const existing = document.getElementById(styleId);
    if (existing) document.head.removeChild(existing);
  };
}

/** jVectorMap ref zoom handlers — matches VectorMapTwo/Three */
export function createVectorMapZoomHandlers(mapRef: RefObject<{ scale: number; width: number; height: number; setScale: (...args: unknown[]) => void } | null>) {
  const zoom = (factor: number) => {
    const map = mapRef.current;
    if (!map) return;
    map.setScale(map.scale * factor, map.width / 2, map.height / 2, false, true);
  };
  return {
    zoomIn: () => zoom(1.5),
    zoomOut: () => zoom(1 / 1.5),
  };
}

/** Global jvectormap CSS overrides for host index.css */
export const jvectormapCssOverrides = `
.jvectormap-container {
  background-color: var(--color-gray-50) !important;
}
.dark .jvectormap-container {
  background-color: var(--color-gray-900) !important;
}
.jvectormap-region.jvectormap-element {
  fill: var(--color-gray-300);
}
.jvectormap-region.jvectormap-element:hover {
  fill: var(--color-brand-500);
}
.dark .jvectormap-region.jvectormap-element {
  fill: var(--color-gray-700);
}
.dark .jvectormap-region.jvectormap-element:hover {
  fill: var(--color-brand-500);
}
.jvectormap-marker.jvectormap-element {
  stroke: var(--color-gray-200);
}
.dark .jvectormap-marker.jvectormap-element {
  stroke: var(--color-gray-800);
}
.jvectormap-tip {
  background-color: var(--color-brand-500) !important;
  border: none !important;
  padding: 4px 8px !important;
}
.jvectormap-zoomin,
.jvectormap-zoomout {
  display: none !important;
}
` as const;
