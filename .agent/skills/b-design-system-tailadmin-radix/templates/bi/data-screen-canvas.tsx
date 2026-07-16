import * as React from "react";
import { cn } from "@/lib/utils";

export type {
  RefreshStatus,
  ScreenShellProps,
} from "./screen/screen-shell";
export {
  DataScreenCanvas,
  RefreshStatusBadge,
  ScreenShell,
} from "./screen/screen-shell";

export type DataScreenAspect = "16:9" | "21:9" | "32:9";

export type DataScreenCanvasProps = {
  title?: React.ReactNode;
  aspectRatio?: DataScreenAspect;
  theme?: "dark" | "light";
  refreshStatus?: import("./screen/screen-shell").RefreshStatus;
  children?: React.ReactNode;
  className?: string;
};

export type BigNumberTileProps = {
  label: React.ReactNode;
  value: React.ReactNode;
  unit?: React.ReactNode;
  delta?: React.ReactNode;
  className?: string;
};

export function BigNumberTile({ label, value, unit, delta, className }: BigNumberTileProps) {
  return (
    <div
      className={cn(
        "flex flex-col justify-center rounded-lg border border-white/10 bg-white/5 p-4 backdrop-blur-sm",
        className,
      )}
    >
      <span className="text-theme-xs text-white/60">{label}</span>
      <div className="mt-1 flex items-baseline gap-1">
        <strong className="text-title-md font-bold tabular-nums text-white">{value}</strong>
        {unit ? <span className="text-theme-sm text-white/50">{unit}</span> : null}
      </div>
      {delta ? <span className="mt-1 text-theme-xs text-success-400">{delta}</span> : null}
    </div>
  );
}

export type GeoMapPanelProps = {
  fallback?: "mock" | "live";
  className?: string;
};

export function GeoMapPanel({ fallback = "mock", className }: GeoMapPanelProps) {
  return (
    <div
      className={cn(
        "relative flex items-center justify-center overflow-hidden rounded-lg border border-white/10 bg-slate-800/80",
        className,
      )}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-brand-500/20 via-transparent to-success-500/10" />
      <span className="relative text-theme-sm text-white/40">地图区域</span>
      {fallback === "mock" ? (
        <Badge className="absolute bottom-2 right-2 bg-white/10 text-theme-xs text-white/60">
          示例数据
        </Badge>
      ) : null}
    </div>
  );
}
