export type BrandPreset = {
  id: string;
  label: string;
  primary: string;
  primaryHover: string;
  fontFamily: string;
  radius: string;
  shadow: string;
};

/** Default TailAdmin brand — do not override host CSS vars without merge. */
export const defaultBrandPreset: BrandPreset = {
  id: "tailadmin-default",
  label: "TailAdmin 默认",
  primary: "var(--brand-500, #465fff)",
  primaryHover: "var(--brand-600, #3641f5)",
  fontFamily: "Outfit, sans-serif",
  radius: "0.75rem",
  shadow: "0 1px 3px rgba(16, 24, 40, 0.1)",
};

export const enterpriseBrandPreset: BrandPreset = {
  id: "enterprise-navy",
  label: "企业深蓝",
  primary: "var(--brand-500, #3641f5)",
  primaryHover: "var(--brand-600, #2a31d8)",
  fontFamily: "Outfit, sans-serif",
  radius: "0.5rem",
  shadow: "0 1px 2px rgba(16, 24, 40, 0.08)",
};

export function brandPresetToCssVars(preset: BrandPreset): Record<string, string> {
  return {
    "--brand-500": preset.primary,
    "--brand-600": preset.primaryHover,
    "--radius-lg": preset.radius,
    "--font-sans": preset.fontFamily,
    "--shadow-card": preset.shadow,
  };
}

export function applyBrandPreset(preset: BrandPreset = defaultBrandPreset): Record<string, string> {
  return brandPresetToCssVars(preset);
}
