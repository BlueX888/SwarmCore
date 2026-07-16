import type { LucideIcon } from "lucide-react";
import { LayoutDashboard, Settings, Shield, Server, BarChart3 } from "lucide-react";

export type IconSource = "tailadmin-svg" | "lucide" | "project";

export type IconPresetEntry = {
  semanticKey: string;
  source: IconSource;
  tailadminIcon?: string;
  lucideIcon?: LucideIcon;
  ariaLabel: string;
};

/** Prefer TailAdmin SVG from templates/icons; lucide only when no SVG exists. */
export const defaultIconPreset: IconPresetEntry[] = [
  { semanticKey: "nav.dashboard", source: "tailadmin-svg", tailadminIcon: "dashboard-alt", ariaLabel: "仪表盘" },
  { semanticKey: "nav.settings", source: "lucide", lucideIcon: Settings, ariaLabel: "设置" },
  { semanticKey: "nav.security", source: "lucide", lucideIcon: Shield, ariaLabel: "安全" },
  { semanticKey: "nav.devops", source: "lucide", lucideIcon: Server, ariaLabel: "运维" },
  { semanticKey: "nav.bi", source: "lucide", lucideIcon: BarChart3, ariaLabel: "分析" },
  { semanticKey: "nav.home", source: "lucide", lucideIcon: LayoutDashboard, ariaLabel: "首页" },
];

export function resolveIconPreset(key: string): IconPresetEntry | undefined {
  return defaultIconPreset.find((entry) => entry.semanticKey === key);
}
