export type ShellMode = "single-portal" | "dual-portal" | "microfrontend" | "embed";

export type ShellPreset = {
  mode: ShellMode;
  label: string;
  sidebarWidth: string;
  headerHeight: string;
  showBreadcrumb: boolean;
  showSearch: boolean;
  contentMaxWidth: string;
};

export const singlePortalShell: ShellPreset = {
  mode: "single-portal",
  label: "单门户",
  sidebarWidth: "290px",
  headerHeight: "4rem",
  showBreadcrumb: true,
  showSearch: true,
  contentMaxWidth: "var(--breakpoint-2xl, 1536px)",
};

export const dualPortalShell: ShellPreset = {
  mode: "dual-portal",
  label: "双门户（运维/业务）",
  sidebarWidth: "260px",
  headerHeight: "3.75rem",
  showBreadcrumb: true,
  showSearch: false,
  contentMaxWidth: "100%",
};

export const microfrontendShell: ShellPreset = {
  mode: "microfrontend",
  label: "微前端嵌入",
  sidebarWidth: "0px",
  headerHeight: "3.5rem",
  showBreadcrumb: false,
  showSearch: false,
  contentMaxWidth: "100%",
};

export const embedShell: ShellPreset = {
  mode: "embed",
  label: "iframe/卡片嵌入",
  sidebarWidth: "0px",
  headerHeight: "0px",
  showBreadcrumb: false,
  showSearch: false,
  contentMaxWidth: "100%",
};

export const shellPresets: Record<ShellMode, ShellPreset> = {
  "single-portal": singlePortalShell,
  "dual-portal": dualPortalShell,
  microfrontend: microfrontendShell,
  embed: embedShell,
};

export function shellPresetToLayoutFlags(preset: ShellPreset) {
  return {
    sidebarWidth: preset.sidebarWidth,
    headerHeight: preset.headerHeight,
    showBreadcrumb: preset.showBreadcrumb,
    showSearch: preset.showSearch,
    contentMaxWidth: preset.contentMaxWidth,
  };
}
