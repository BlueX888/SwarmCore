export type SyncTrackStatus = "ok" | "pending" | "error" | "stale" | "frozen";

export type SyncTrack = {
  id: string;
  label: string;
  status: SyncTrackStatus;
  lastSuccess?: string;
  lastError?: string;
  hint?: string;
};

export type SyncHealthKpi = {
  overallStatus: "healthy" | "degraded" | "frozen";
  degradedCount: number;
  lastFullSync: string;
  nextScheduledSync: string;
  instanceId: string;
  orgName: string;
};

export type SyncEventEntry = {
  id: string;
  occurredAt: string;
  trackId: string;
  trackLabel: string;
  action: "auto" | "manual" | "retry" | "frozen";
  result: "success" | "error" | "skipped";
  message: string;
};

export const syncHealthKpi: SyncHealthKpi = {
  overallStatus: "degraded",
  degradedCount: 2,
  lastFullSync: "2026-06-29 08:42:18",
  nextScheduledSync: "2026-06-29 09:00:00",
  instanceId: "gw-prod-cn-east-01",
  orgName: "华东制造集团",
};

export const syncHealthTracks: SyncTrack[] = [
  { id: "quota", label: "配额同步", status: "ok", lastSuccess: "12 秒前" },
  {
    id: "report",
    label: "报表同步",
    status: "error",
    lastSuccess: "18 分钟前",
    lastError: "上游报表服务返回 503，已自动退避重试",
    hint: "请检查报表聚合服务健康状态或联系平台运维",
  },
  {
    id: "hmac",
    label: "HMAC 心跳",
    status: "stale",
    lastSuccess: "8 分钟前",
    hint: "出口网络延迟升高，建议检查白名单与代理配置",
  },
  { id: "heartbeat", label: "实例心跳", status: "ok", lastSuccess: "5 秒前" },
];

export const syncEventEntries: SyncEventEntry[] = [
  {
    id: "evt-1",
    occurredAt: "2026-06-29 08:42:18",
    trackId: "quota",
    trackLabel: "配额同步",
    action: "auto",
    result: "success",
    message: "配额池余额与席位用量已对齐",
  },
  {
    id: "evt-2",
    occurredAt: "2026-06-29 08:40:02",
    trackId: "report",
    trackLabel: "报表同步",
    action: "retry",
    result: "error",
    message: "报表聚合服务不可用，已进入退避队列",
  },
  {
    id: "evt-3",
    occurredAt: "2026-06-29 08:38:55",
    trackId: "hmac",
    trackLabel: "HMAC 心跳",
    action: "auto",
    result: "success",
    message: "HMAC 签名握手成功",
  },
  {
    id: "evt-4",
    occurredAt: "2026-06-29 08:35:00",
    trackId: "heartbeat",
    trackLabel: "实例心跳",
    action: "auto",
    result: "success",
    message: "实例在线，延迟 42ms",
  },
  {
    id: "evt-5",
    occurredAt: "2026-06-29 08:30:12",
    trackId: "report",
    trackLabel: "报表同步",
    action: "manual",
    result: "error",
    message: "手动触发同步失败，请稍后重试",
  },
];

export const syncActionLabel: Record<SyncEventEntry["action"], string> = {
  auto: "自动同步",
  manual: "手动同步",
  retry: "重试",
  frozen: "冻结阻断",
};

export const syncResultLabel: Record<SyncEventEntry["result"], string> = {
  success: "成功",
  error: "失败",
  skipped: "跳过",
};
