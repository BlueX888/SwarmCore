export type ActivationWizardStepId = "form" | "verify" | "done";

export const activationWizardSteps: Array<{ id: ActivationWizardStepId; title: string }> = [
  { id: "form", title: "填写网关信息" },
  { id: "verify", title: "验证连通" },
  { id: "done", title: "完成激活" },
];

export type ActivationFormValues = {
  gatewayUrl: string;
  adminEmail: string;
  orgName: string;
};

export const defaultActivationFormValues: ActivationFormValues = {
  gatewayUrl: "https://gateway.corp.example.com",
  adminEmail: "ops-admin@corp.example.com",
  orgName: "华东研发中心",
};

export const activationSuccessResult = {
  instanceId: "gw-cn-east-prod-7f3a",
  connectionId: "conn_9k2m8x1p",
  activatedAt: "2026-06-28 14:32:18",
  region: "华东一区",
};

export const probeSuccessPayload = {
  status: "ok",
  latency_ms: 38,
  tls: "1.3",
  endpoint: "https://gateway.corp.example.com/health",
};
