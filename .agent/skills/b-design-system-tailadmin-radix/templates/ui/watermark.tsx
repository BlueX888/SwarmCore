import * as React from "react";
import { cn } from "@/lib/utils";

export type WatermarkProps = {
  content: string | string[];
  gap?: [number, number];
  rotate?: number;
  fontSize?: number;
  fontColor?: string;
  className?: string;
  children?: React.ReactNode;
};

function buildWatermarkDataUrl(
  lines: string[],
  rotate: number,
  fontSize: number,
  fontColor: string,
  gap: [number, number],
): string {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";

  const [gapX, gapY] = gap;
  canvas.width = gapX;
  canvas.height = gapY;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate((rotate * Math.PI) / 180);
  ctx.font = `${fontSize}px sans-serif`;
  ctx.fillStyle = fontColor;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  lines.forEach((line, i) => {
    ctx.fillText(line, 0, i * (fontSize + 4) - ((lines.length - 1) * (fontSize + 4)) / 2);
  });

  return canvas.toDataURL();
}

export function Watermark({
  content,
  gap = [200, 160],
  rotate = -22,
  fontSize = 14,
  fontColor = "rgba(0,0,0,0.08)",
  className,
  children,
}: WatermarkProps) {
  const lines = Array.isArray(content) ? content : [content];
  const [bg, setBg] = React.useState<string>("");

  React.useEffect(() => {
    setBg(buildWatermarkDataUrl(lines, rotate, fontSize, fontColor, gap));
  }, [lines.join("|"), rotate, fontSize, fontColor, gap[0], gap[1]]);

  return (
    <div className={cn("relative", className)}>
      {bg ? (
        <div
          className="pointer-events-none absolute inset-0 z-0"
          style={{
            backgroundImage: `url(${bg})`,
            backgroundRepeat: "repeat",
          }}
          aria-hidden
        />
      ) : null}
      <div className="relative z-[1]">{children}</div>
    </div>
  );
}
