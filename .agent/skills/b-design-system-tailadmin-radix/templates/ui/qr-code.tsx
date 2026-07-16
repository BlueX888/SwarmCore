import * as React from "react";
import { cn } from "@/lib/utils";

export type QRCodeProps = {
  value: string;
  size?: number;
  level?: "L" | "M" | "Q" | "H";
  className?: string;
  alt?: string;
};

/**
 * Lightweight QR placeholder using external `qrcode` when available in host project.
 * Falls back to a linked API image for examples without the peer installed.
 */
export function QRCode({
  value,
  size = 128,
  level = "M",
  className,
  alt = "二维码",
}: QRCodeProps) {
  const [src, setSrc] = React.useState<string>("");

  React.useEffect(() => {
    let cancelled = false;

    async function generate() {
      try {
        const QR = await import("qrcode");
        const url = await QR.toDataURL(value, {
          width: size,
          errorCorrectionLevel: level,
          margin: 1,
        });
        if (!cancelled) setSrc(url);
      } catch {
        const encoded = encodeURIComponent(value);
        if (!cancelled) {
          setSrc(
            `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encoded}`,
          );
        }
      }
    }

    generate();
    return () => {
      cancelled = true;
    };
  }, [value, size, level]);

  if (!src) {
    return (
      <div
        className={cn(
          "animate-pulse rounded-lg bg-gray-100 dark:bg-white/10",
          className,
        )}
        style={{ width: size, height: size }}
        aria-busy="true"
      />
    );
  }

  return (
    <img
      src={src}
      width={size}
      height={size}
      alt={alt}
      className={cn("rounded-lg border border-gray-200 dark:border-gray-800", className)}
    />
  );
}
