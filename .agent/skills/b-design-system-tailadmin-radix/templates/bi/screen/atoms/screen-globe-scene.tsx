import * as React from "react";

import { cn } from "../lib/cn";

export type GlobeNode = {
  id: string;
  label: string;
  /** 0–360 经度角 */
  lon: number;
  /** -90–90 纬度角 */
  lat: number;
  status?: "normal" | "warning" | "alert";
  detail?: string;
};

export type ScreenGlobeSceneProps = {
  nodes?: GlobeNode[];
  selectedNodeId?: string | null;
  onNodeClick?: (id: string) => void;
  hintText?: string;
  height?: number | string;
  theme?: "dark";
  className?: string;
};

const statusColors: Record<NonNullable<GlobeNode["status"]>, string> = {
  normal: "#22d3ee",
  warning: "#fbbf24",
  alert: "#fb7185",
};

function polarToXY(lon: number, lat: number, radius: number, cx: number, cy: number) {
  const lonRad = ((lon - 90) * Math.PI) / 180;
  const latRad = (lat * Math.PI) / 180;
  const r = radius * Math.cos(latRad);
  return {
    x: cx + r * Math.cos(lonRad),
    y: cy + radius * Math.sin(latRad) * 0.92,
  };
}

/**
 * 地球场景 — CSS/SVG 占位地球，智慧城市/Global 态势适用。
 * @see prd/data-screens/atoms.md#task-ds-a16
 */
export function ScreenGlobeScene({
  nodes = [],
  selectedNodeId = null,
  onNodeClick,
  hintText = "CSS/SVG 地球占位 · 点击节点查看城市态势",
  height = "100%",
  theme = "dark",
  className,
}: ScreenGlobeSceneProps) {
  const [hoveredId, setHoveredId] = React.useState<string | null>(null);
  const activeId = selectedNodeId ?? hoveredId;
  const activeNode = nodes.find((node) => node.id === activeId);

  return (
    <div
      data-screen-globe-scene
      data-theme={theme}
      className={cn("relative w-full overflow-hidden rounded-md", className)}
      style={{ height }}
    >
      <div
        aria-hidden
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(34,211,238,0.15)_0%,_transparent_60%),linear-gradient(180deg,_#020617_0%,_#0f172a_50%,_#1e3a5f_100%)]"
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative animate-[spin_48s_linear_infinite]" style={{ width: "72%", maxWidth: 320, aspectRatio: "1" }}>
          <svg viewBox="0 0 200 200" className="h-full w-full drop-shadow-[0_0_24px_rgba(34,211,238,0.35)]">
            <defs>
              <radialGradient id="globe-fill" cx="35%" cy="30%" r="65%">
                <stop offset="0%" stopColor="#1e40af" />
                <stop offset="55%" stopColor="#0c4a6e" />
                <stop offset="100%" stopColor="#020617" />
              </radialGradient>
              <clipPath id="globe-clip">
                <circle cx="100" cy="100" r="88" />
              </clipPath>
            </defs>
            <circle cx="100" cy="100" r="88" fill="url(#globe-fill)" stroke="rgba(34,211,238,0.35)" strokeWidth="1.5" />
            <g clipPath="url(#globe-clip)" opacity="0.55">
              {[...Array(8)].map((_, i) => (
                <ellipse
                  key={`lat-${i}`}
                  cx="100"
                  cy="100"
                  rx={88 - i * 10}
                  ry={12 + i * 8}
                  fill="none"
                  stroke="rgba(34,211,238,0.18)"
                  strokeWidth="0.8"
                />
              ))}
              {[...Array(12)].map((_, i) => {
                const angle = (i * 180) / 12;
                return (
                  <ellipse
                    key={`lon-${i}`}
                    cx="100"
                    cy="100"
                    rx="88"
                    ry="22"
                    fill="none"
                    stroke="rgba(34,211,238,0.12)"
                    strokeWidth="0.6"
                    transform={`rotate(${angle} 100 100)`}
                  />
                );
              })}
            </g>
            {nodes.map((node) => {
              const { x, y } = polarToXY(node.lon, node.lat, 78, 100, 100);
              const color = statusColors[node.status ?? "normal"];
              const isActive = activeId === node.id;
              return (
                <g key={node.id}>
                  <circle
                    cx={x}
                    cy={y}
                    r={isActive ? 5 : 3.5}
                    fill={color}
                    className={onNodeClick ? "cursor-pointer" : undefined}
                    onClick={() => onNodeClick?.(node.id)}
                    onMouseEnter={() => setHoveredId(node.id)}
                    onMouseLeave={() => setHoveredId(null)}
                  />
                  {isActive ? (
                    <circle cx={x} cy={y} r="9" fill="none" stroke={color} strokeOpacity="0.5" strokeWidth="1">
                      <animate attributeName="r" values="6;12;6" dur="2s" repeatCount="indefinite" />
                      <animate attributeName="stroke-opacity" values="0.6;0;0.6" dur="2s" repeatCount="indefinite" />
                    </circle>
                  ) : null}
                </g>
              );
            })}
          </svg>
        </div>
      </div>
      <p className="absolute bottom-2 left-0 right-0 text-center text-[10px] text-cyan-200/60">{hintText}</p>
      {activeNode ? (
        <div className="absolute left-3 top-3 max-w-[200px] rounded-md border border-cyan-400/30 bg-slate-900/90 px-3 py-2 text-xs shadow-lg backdrop-blur-sm">
          <p className="font-semibold text-cyan-100">{activeNode.label}</p>
          {activeNode.detail ? <p className="mt-1 text-white/70">{activeNode.detail}</p> : null}
        </div>
      ) : null}
    </div>
  );
}
