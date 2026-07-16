export type DensityLevel = "comfortable" | "compact" | "dense";

export type DensityPreset = {
  level: DensityLevel;
  label: string;
  controlHeight: string;
  tableCellPy: string;
  cardPadding: string;
  pageGap: string;
};

export const comfortableDensity: DensityPreset = {
  level: "comfortable",
  label: "舒适",
  controlHeight: "2.75rem",
  tableCellPy: "1rem",
  cardPadding: "1.5rem",
  pageGap: "1.5rem",
};

export const compactDensity: DensityPreset = {
  level: "compact",
  label: "紧凑",
  controlHeight: "2.5rem",
  tableCellPy: "0.75rem",
  cardPadding: "1.25rem",
  pageGap: "1.25rem",
};

export const denseDensity: DensityPreset = {
  level: "dense",
  label: "密集",
  controlHeight: "2.25rem",
  tableCellPy: "0.5rem",
  cardPadding: "1rem",
  pageGap: "1rem",
};

export const densityPresets: Record<DensityLevel, DensityPreset> = {
  comfortable: comfortableDensity,
  compact: compactDensity,
  dense: denseDensity,
};

export function densityPresetToCssVars(preset: DensityPreset): Record<string, string> {
  return {
    "--control-height": preset.controlHeight,
    "--table-cell-py": preset.tableCellPy,
    "--card-padding": preset.cardPadding,
    "--page-gap": preset.pageGap,
  };
}
