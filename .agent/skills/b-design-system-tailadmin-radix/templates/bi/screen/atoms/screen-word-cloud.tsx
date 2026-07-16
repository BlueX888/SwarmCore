import * as React from "react";

import { cn } from "../lib/cn";

export type WordCloudItem = {
  text: string;
  weight: number;
};

export type ScreenWordCloudProps = {
  words: WordCloudItem[];
  theme?: "dark" | "light";
  /** CSS tag 云降级 — 无第三方词云库 */
  fallback?: "tag-cloud";
  className?: string;
};

function sizeClass(weight: number, max: number) {
  const ratio = weight / max;
  if (ratio > 0.85) return "text-lg font-semibold";
  if (ratio > 0.65) return "text-base font-medium";
  if (ratio > 0.45) return "text-sm";
  return "text-xs";
}

/**
 * 热词气泡 — CSS tag 云降级实现（标注 fallback="tag-cloud"）。
 * @see prd/data-screens/atoms.md#task-ds-a11
 */
export function ScreenWordCloud({
  words,
  theme = "light",
  fallback = "tag-cloud",
  className,
}: ScreenWordCloudProps) {
  const isDark = theme === "dark";
  const max = Math.max(...words.map((word) => word.weight), 1);
  const palette = isDark
    ? ["text-cyan-300", "text-blue-300", "text-violet-300", "text-emerald-300", "text-amber-300"]
    : ["text-blue-600", "text-cyan-600", "text-violet-600", "text-emerald-600", "text-amber-600"];

  return (
    <div
      className={cn(
        "flex min-h-[160px] flex-wrap content-center justify-center gap-2 p-2",
        className,
      )}
      data-screen-word-cloud
      data-fallback={fallback}
      aria-label="热词云"
    >
      {words.map((word, index) => (
        <span
          key={word.text}
          className={cn(
            "rounded-full px-2 py-1 transition-transform hover:scale-105",
            sizeClass(word.weight, max),
            palette[index % palette.length],
            isDark ? "bg-white/5" : "bg-white/80 shadow-sm",
          )}
        >
          {word.text}
        </span>
      ))}
    </div>
  );
}
