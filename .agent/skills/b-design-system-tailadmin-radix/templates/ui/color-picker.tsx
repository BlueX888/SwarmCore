import * as React from "react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export type ColorFormat = "hex" | "rgb" | "hsl";

export type ColorPickerProps = {
  value?: string;
  onChange?: (value: string) => void;
  format?: ColorFormat;
  presets?: string[];
  showInput?: boolean;
  trigger?: "swatch" | "input";
  disabled?: boolean;
  className?: string;
};

type HexColorPickerProps = {
  color: string;
  onChange: (color: string) => void;
};

const HexColorPicker = React.lazy(async () => {
  const module = await import("react-colorful");
  return { default: module.HexColorPicker };
});

function normalizeHex(value?: string): string {
  if (!value) return "#000000";
  const trimmed = value.trim();
  if (/^#[0-9a-fA-F]{6}$/.test(trimmed)) return trimmed;
  if (/^#[0-9a-fA-F]{3}$/.test(trimmed)) {
    const [, r, g, b] = trimmed;
    return `#${r}${r}${g}${g}${b}${b}`;
  }
  if (/^[0-9a-fA-F]{6}$/.test(trimmed)) return `#${trimmed}`;
  return "#000000";
}

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const normalized = normalizeHex(hex).slice(1);
  return {
    r: Number.parseInt(normalized.slice(0, 2), 16),
    g: Number.parseInt(normalized.slice(2, 4), 16),
    b: Number.parseInt(normalized.slice(4, 6), 16),
  };
}

function hexToHsl(hex: string): { h: number; s: number; l: number } {
  const { r, g, b } = hexToRgb(hex);
  const rn = r / 255;
  const gn = g / 255;
  const bn = b / 255;
  const max = Math.max(rn, gn, bn);
  const min = Math.min(rn, gn, bn);
  const delta = max - min;
  let h = 0;
  const l = (max + min) / 2;
  const s = delta === 0 ? 0 : delta / (1 - Math.abs(2 * l - 1));

  if (delta !== 0) {
    switch (max) {
      case rn:
        h = ((gn - bn) / delta) % 6;
        break;
      case gn:
        h = (bn - rn) / delta + 2;
        break;
      default:
        h = (rn - gn) / delta + 4;
        break;
    }
    h *= 60;
    if (h < 0) h += 360;
  }

  return {
    h: Math.round(h),
    s: Math.round(s * 100),
    l: Math.round(l * 100),
  };
}

function formatColor(hex: string, format: ColorFormat): string {
  const normalized = normalizeHex(hex);
  if (format === "hex") return normalized;
  if (format === "rgb") {
    const { r, g, b } = hexToRgb(normalized);
    return `rgb(${r}, ${g}, ${b})`;
  }
  const { h, s, l } = hexToHsl(normalized);
  return `hsl(${h}, ${s}%, ${l}%)`;
}

function ColorPanel({ color, onChange }: HexColorPickerProps) {
  return (
    <React.Suspense
      fallback={
        <div className="flex h-[160px] w-[200px] items-center justify-center text-sm text-gray-500">
          加载色板…
        </div>
      }
    >
      <HexColorPicker color={color} onChange={onChange} className="!w-full" />
    </React.Suspense>
  );
}

export function ColorPicker({
  value = "#000000",
  onChange,
  format = "hex",
  presets,
  showInput = true,
  trigger = "swatch",
  disabled = false,
  className,
}: ColorPickerProps) {
  const [open, setOpen] = React.useState(false);
  const hexValue = normalizeHex(value);
  const displayValue = formatColor(hexValue, format);

  const handleHexChange = (nextHex: string) => {
    onChange?.(formatColor(nextHex, format));
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange?.(event.target.value);
  };

  return (
    <Popover open={open} onOpenChange={(next) => !disabled && setOpen(next)}>
      <PopoverTrigger asChild>
        {trigger === "input" ? (
          <button
            type="button"
            disabled={disabled}
            className={cn(
              "flex h-11 w-full items-center gap-2 rounded-lg border border-gray-300 bg-transparent px-3 text-left text-sm shadow-theme-xs dark:border-gray-700 dark:bg-gray-900",
              disabled && "cursor-not-allowed opacity-40",
              className,
            )}
          >
            <span
              className="size-5 shrink-0 rounded-md border border-gray-200 dark:border-gray-700"
              style={{ backgroundColor: hexValue }}
              aria-hidden="true"
            />
            <span className="truncate text-gray-800 dark:text-white/90">{displayValue}</span>
          </button>
        ) : (
          <button
            type="button"
            disabled={disabled}
            aria-label={`当前颜色 ${displayValue}`}
            className={cn(
              "size-11 rounded-lg border border-gray-300 shadow-theme-xs dark:border-gray-700",
              disabled && "cursor-not-allowed opacity-40",
              className,
            )}
            style={{ backgroundColor: hexValue }}
          />
        )}
      </PopoverTrigger>
      <PopoverContent className="w-auto p-3" align="start">
        <ColorPanel color={hexValue} onChange={handleHexChange} />
        {presets?.length ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {presets.map((preset) => {
              const presetHex = normalizeHex(preset);
              return (
                <button
                  key={presetHex}
                  type="button"
                  aria-label={`选择 ${presetHex}`}
                  className="size-6 rounded-md border border-gray-200 transition-transform hover:scale-105 dark:border-gray-700"
                  style={{ backgroundColor: presetHex }}
                  onClick={() => handleHexChange(presetHex)}
                />
              );
            })}
          </div>
        ) : null}
        {showInput ? (
          <div className="mt-3">
            <Input
              value={displayValue}
              onChange={handleInputChange}
              inputSkin="outlined"
              aria-label="颜色值"
            />
          </div>
        ) : null}
      </PopoverContent>
    </Popover>
  );
}
