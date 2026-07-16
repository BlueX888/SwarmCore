import * as React from "react";

import { cn } from "../lib/cn";
import { screenTokens } from "../theme/screen-tokens";

export type MapMarkerCategory = "office" | "residential" | "parking" | "facility" | "other";

export type MapMarker = {
  id: string;
  label: string;
  /** 0–100 百分比坐标 */
  x: number;
  y: number;
  category?: MapMarkerCategory;
  status?: "normal" | "warning" | "alert";
  detail?: string;
};

export type ScreenMapSceneProps = {
  markers: MapMarker[];
  fallback?: "mock";
  selectedMarkerId?: string | null;
  onMarkerClick?: (id: string) => void;
  hintText?: string;
  height?: number | string;
  theme?: "dark";
  className?: string;
};

const categoryColors: Record<MapMarkerCategory, string> = {
  office: "bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.8)]",
  residential: "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]",
  parking: "bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.8)]",
  facility: "bg-violet-400 shadow-[0_0_10px_rgba(167,139,250,0.8)]",
  other: "bg-slate-300 shadow-[0_0_8px_rgba(148,163,184,0.6)]",
};

const statusRing: Record<NonNullable<MapMarker["status"]>, string> = {
  normal: "ring-cyan-400/40",
  warning: "ring-amber-400/70",
  alert: "ring-rose-500/80",
};

/**
 * 地图场景 — 渐变/mock 底图 + 标注点；大屏社区/生态地图适用。
 * @see prd/data-screens/atoms.md#task-ds-a12
 */
export function ScreenMapScene({
  markers,
  fallback = "mock",
  selectedMarkerId = null,
  onMarkerClick,
  hintText = "mock 社区底图 · 悬停或点击标注查看详情",
  height = "100%",
  theme = "dark",
  className,
}: ScreenMapSceneProps) {
  const [hoveredId, setHoveredId] = React.useState<string | null>(null);
  const activeId = selectedMarkerId ?? hoveredId;

  return (
    <div
      data-screen-map-scene
      data-fallback={fallback}
      data-theme={theme}
      className={cn("relative w-full overflow-hidden rounded-md", className)}
      style={{ height }}
    >
      <div
        aria-hidden
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(34,211,238,0.12)_0%,_transparent_55%),linear-gradient(160deg,_#0f172a_0%,_#1e293b_45%,_#0c4a6e_100%)]"
      />
      <div
        aria-hidden
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage:
            "linear-gradient(rgba(34,211,238,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.08) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />
      <div aria-hidden className="absolute inset-4 rounded-full border border-cyan-500/10" />
      <div aria-hidden className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-400/20" />

      {markers.map((marker) => {
        const category = marker.category ?? "other";
        const status = marker.status ?? "normal";
        const isActive = activeId === marker.id;

        return (
          <button
            key={marker.id}
            type="button"
            aria-label={marker.label}
            aria-pressed={selectedMarkerId === marker.id}
            className={cn(
              "group absolute z-10 -translate-x-1/2 -translate-y-1/2 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300",
            )}
            style={{ left: `${marker.x}%`, top: `${marker.y}%` }}
            onClick={() => onMarkerClick?.(marker.id)}
            onMouseEnter={() => setHoveredId(marker.id)}
            onMouseLeave={() => setHoveredId((prev) => (prev === marker.id ? null : prev))}
          >
            <span
              className={cn(
                "relative flex h-3 w-3 items-center justify-center rounded-full ring-2 ring-offset-2 ring-offset-slate-900 transition-transform",
                categoryColors[category],
                statusRing[status],
                isActive && "scale-125",
              )}
            >
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400/40 opacity-60" />
            </span>
            <span
              className={cn(
                "pointer-events-none absolute left-1/2 top-4 z-20 -translate-x-1/2 whitespace-nowrap rounded border border-cyan-500/30 bg-slate-900/95 px-2 py-0.5 text-[10px] text-cyan-100 opacity-0 shadow-lg transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100",
                isActive && "opacity-100",
              )}
            >
              {marker.label}
            </span>
          </button>
        );
      })}

      {activeId ? (
        <div className="absolute bottom-2 left-2 right-2 rounded border border-cyan-500/25 bg-slate-950/80 px-2 py-1.5 text-[11px] text-cyan-100/90">
          {markers.find((m) => m.id === activeId)?.detail ??
            markers.find((m) => m.id === activeId)?.label ??
            "地图标注"}
        </div>
      ) : (
        <p className={cn("absolute bottom-2 left-3 text-[10px]", screenTokens.kpiLabel)}>
          {hintText}
        </p>
      )}
    </div>
  );
}
