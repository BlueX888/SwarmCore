export type OfflineActivationStepId = "airgap" | "license" | "done";

export const offlineActivationSteps: Array<{ id: OfflineActivationStepId; title: string }> = [
  { id: "airgap", title: "确认离线环境" },
  { id: "license", title: "上传 License" },
  { id: "done", title: "完成激活" },
];

export type OfflineActivationFormValues = {
  orgName: string;
  adminEmail: string;
  instanceHost: string;
};

export const defaultOfflineActivationFormValues: OfflineActivationFormValues = {
  orgName: "西南离线数据中心",
  adminEmail: "airgap-admin@corp.example.com",
  instanceHost: "edge.airgap.local",
};

export const offlineActivationSuccessResult = {
  instanceId: "gw-cn-west-airgap-2b9c",
  licenseEdition: "企业版（离线）",
  expiresAt: "2027年6月30日",
  activatedAt: "2026-06-28 23:50:12",
  fingerprint: "fp_a8k3m2x7q1",
};

export const licenseValidationPayload = {
  status: "valid",
  edition: "enterprise-airgap",
  seats: 500,
  expires_at: "2027-06-30T23:59:59+08:00",
  signature: "ed25519:verified-local",
};
