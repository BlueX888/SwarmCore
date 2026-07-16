export type LicenseSummaryStatus = "valid" | "expiring" | "expired";

export type LicenseAuditAction = "issue" | "renew" | "revoke";

export type LicenseAuditEntry = {
  id: string;
  action: LicenseAuditAction;
  operator: string;
  targetInstance: string;
  edition: string;
  occurredAt: string;
  note: string;
};

export const licenseSummary = {
  edition: "企业版",
  status: "expiring" as LicenseSummaryStatus,
  expiresAt: "2026-09-15",
  seats: 120,
  boundInstance: "gw-prod-cn-east-01",
  orgName: "华东制造集团",
};

export const licenseAuditEntries: LicenseAuditEntry[] = [
  {
    id: "audit-001",
    action: "issue",
    operator: "张运营",
    targetInstance: "gw-prod-cn-east-01",
    edition: "企业版",
    occurredAt: "2025-09-15 10:32",
    note: "年度续签签发，席位 120",
  },
  {
    id: "audit-002",
    action: "renew",
    operator: "李运维",
    targetInstance: "gw-prod-cn-east-01",
    edition: "企业版",
    occurredAt: "2026-03-01 14:08",
    note: "离线续期验签通过",
  },
  {
    id: "audit-003",
    action: "issue",
    operator: "张运营",
    targetInstance: "gw-staging-02",
    edition: "标准版",
    occurredAt: "2026-05-20 09:15",
    note: "预发环境新实例签发",
  },
];

export const mockIssuedLicense =
  "LIC-ED25519-eyJvcmdJZCI6ImVhc3QtbWFudWZhY3R1cmluZyIsImVkaXRpb24iOiJlbnRlcnByaXNlIiwic2VhdHMiOjEyMCwiZXhwaXJlc0F0IjoiMjAyNi0wOS0xNSJ9";

export const licenseDangerActions = [
  {
    id: "revoke",
    label: "吊销当前 License",
    description: "吊销后实例将进入只读模式，所有写入 API 将被拒绝，需重新签发恢复。",
    confirmLabel: "确认吊销",
    requiresNameConfirm: true,
    confirmPlaceholder: "gw-prod-cn-east-01",
  },
  {
    id: "force-renew",
    label: "强制覆盖续期",
    description: "跳过常规验签窗口，直接以新 License 覆盖当前绑定；仅用于紧急恢复。",
    confirmLabel: "强制续期",
    requiresNameConfirm: true,
    confirmPlaceholder: "强制续期",
  },
];

export const auditActionLabel: Record<LicenseAuditAction, string> = {
  issue: "签发",
  renew: "续期",
  revoke: "吊销",
};
