export type CopyTone = "saas" | "enterprise" | "government" | "devtools";

export type CopyPreset = {
  tone: CopyTone;
  label: string;
  emptyState: string;
  errorState: string;
  saveSuccess: string;
  confirmDanger: string;
  loadingLabel: string;
};

export const saasCopyPreset: CopyPreset = {
  tone: "saas",
  label: "SaaS 产品",
  emptyState: "暂无数据，调整筛选条件或创建第一条记录。",
  errorState: "加载失败，请稍后重试或联系管理员。",
  saveSuccess: "保存成功，变更已同步。",
  confirmDanger: "此操作不可撤销，请确认后继续。",
  loadingLabel: "正在加载…",
};

export const enterpriseCopyPreset: CopyPreset = {
  tone: "enterprise",
  label: "企业内网",
  emptyState: "当前条件下无匹配记录。",
  errorState: "系统繁忙，请稍后重试。",
  saveSuccess: "提交成功，已进入审批流程。",
  confirmDanger: "该操作将影响生产环境，需二次确认。",
  loadingLabel: "数据加载中…",
};

export const governmentCopyPreset: CopyPreset = {
  tone: "government",
  label: "政务系统",
  emptyState: "暂无符合条件的数据。",
  errorState: "服务暂时不可用，请稍后再试。",
  saveSuccess: "保存成功。",
  confirmDanger: "请确认是否执行该操作。",
  loadingLabel: "请稍候…",
};

export const devtoolsCopyPreset: CopyPreset = {
  tone: "devtools",
  label: "开发者工具",
  emptyState: "No records match the current filter.",
  errorState: "Request failed. Retry or check API logs.",
  saveSuccess: "Changes saved.",
  confirmDanger: "This action cannot be undone.",
  loadingLabel: "Loading…",
};

export const copyPresets: Record<CopyTone, CopyPreset> = {
  saas: saasCopyPreset,
  enterprise: enterpriseCopyPreset,
  government: governmentCopyPreset,
  devtools: devtoolsCopyPreset,
};

export function resolveCopyPreset(tone: CopyTone = "saas"): CopyPreset {
  return copyPresets[tone];
}
