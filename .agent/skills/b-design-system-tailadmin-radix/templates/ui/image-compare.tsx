import * as React from "react";
import { cn } from "@/lib/utils";

export type ImageCompareProps = {
  beforeSrc: string;
  afterSrc: string;
  beforeLabel?: string;
  afterLabel?: string;
  initialPosition?: number;
  className?: string;
};

/**
 * 双图前后对比滑块 — 配置 Diff、发布前后对比。
 */
export function ImageCompare({
  beforeSrc,
  afterSrc,
  beforeLabel = "变更前",
  afterLabel = "变更后",
  initialPosition = 50,
  className,
}: ImageCompareProps) {
  const [pos, setPos] = React.useState(initialPosition);
  const safePos = Math.min(100, Math.max(0, pos));
  const beforeWidth = safePos > 0 ? `${100 / (safePos / 100)}%` : "100%";

  return (
    <div
      className={cn(
        "relative aspect-video overflow-hidden rounded-2xl border border-gray-200 bg-gray-100 dark:border-gray-800 dark:bg-white/[0.03]",
        className,
      )}
    >
      <img
        src={afterSrc}
        alt={afterLabel}
        className="absolute inset-0 size-full object-cover"
      />
      <div className="absolute inset-0 overflow-hidden" style={{ width: `${safePos}%` }}>
        <img
          src={beforeSrc}
          alt={beforeLabel}
          className="size-full object-cover"
          style={{ width: beforeWidth }}
        />
      </div>

      <div
        className="pointer-events-none absolute inset-y-0 z-[1] w-0.5 bg-white shadow-theme-sm"
        style={{ left: `${safePos}%` }}
        aria-hidden
      />

      <span className="pointer-events-none absolute left-3 top-3 rounded-lg bg-black/50 px-2 py-1 text-theme-xs font-medium text-white">
        {beforeLabel}
      </span>
      <span className="pointer-events-none absolute right-3 top-3 rounded-lg bg-black/50 px-2 py-1 text-theme-xs font-medium text-white">
        {afterLabel}
      </span>

      <input
        type="range"
        min={0}
        max={100}
        value={safePos}
        onChange={(event) => setPos(Number(event.target.value))}
        className="absolute inset-x-4 bottom-4 z-10 h-2 cursor-ew-resize accent-brand-500"
        aria-valuenow={safePos}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="对比位置"
      />
    </div>
  );
}
