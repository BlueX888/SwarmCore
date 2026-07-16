/** TailAdmin Maps theme — card shell, zoom controls, provider defaults */

export const mapsPageGridClass = "grid grid-cols-1 lg:grid-cols-2 gap-6";

export const mapCardShellClass =
  "rounded-2xl border border-gray-200 bg-white p-5 sm:p-6 dark:border-gray-800 dark:bg-white/[0.03]";

export const mapCardTitleClass =
  "text-lg font-semibold text-gray-800 dark:text-white/90";

export const mapCardSubtitleClass =
  "text-theme-sm mt-1 text-gray-500 dark:text-gray-400";

export const mapContainerWrapperClass =
  "relative z-0 overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800";

export const mapContainerClass = "h-[300px] w-full";

export const mapZoomControlWrapperClass = "absolute top-3 right-3 z-[999]";

export const mapZoomControlStackClass =
  "flex flex-col overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900";

export const mapZoomButtonClass =
  "flex h-9 w-9 items-center justify-center text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-white/5 dark:hover:text-white";

export const mapZoomButtonTopClass = `${mapZoomButtonClass} border-b border-gray-200 dark:border-gray-800`;

export const iframeMapClass =
  "!w-full h-[300px] rounded-xl border border-gray-200 grayscale dark:border-gray-800";

export const defaultMapLibreOptions = {
  style: "https://tiles.openfreemap.org/styles/bright",
  center: [-77.0369, 38.9072] as [number, number],
  zoom: 8.5,
  scrollZoom: false,
  attributionControl: false,
} as const;

/** Shallow merge for MapLibre init — center/zoom/style 等业务 override */
export function mergeMapLibreOptions(
  overrides?: Partial<typeof defaultMapLibreOptions>
) {
  return { ...defaultMapLibreOptions, ...overrides };
}

export const defaultLeafletTileUrl =
  "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

export const defaultLeafletOptions = {
  center: [40.772, -74.43] as [number, number],
  zoom: 13,
  scrollWheelZoom: false,
  zoomControl: false,
  attributionControl: false,
} as const;

/** Shallow merge for Leaflet init */
export function mergeLeafletOptions(
  overrides?: Partial<typeof defaultLeafletOptions>
) {
  return { ...defaultLeafletOptions, ...overrides };
}

/** Leaflet divIcon HTML for Home/Office style markers */
export function createLeafletDivIcon(label: string, svgPath: string): string {
  return `
    <div style="display:flex;flex-direction:column;align-items:center;">
      <div style="
        width:40px;height:40px;border-radius:50%;
        border:1px solid #c7d7fe;
        background:#eff4ff;color:#3538CD;
        display:flex;align-items:center;justify-content:center;
      ">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${svgPath}</svg>
      </div>
      <div style="
        margin-top:6px;background:#fff;color:#1d2939;
        border-radius:999px;padding:2px 10px;font-size:11px;
        font-weight:500;box-shadow:0 2px 8px rgba(0,0,0,0.12);
        white-space:nowrap;
      ">${label}</div>
    </div>
  `;
}

export const leafletMarkerSvgs = {
  home: '<path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  office:
    '<rect x="2" y="7" width="20" height="15" rx="1"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><line x1="12" y1="12" x2="12" y2="12.01"/>',
} as const;
