import type { EndpointProbeRow } from "../../../gateway/endpoint-probe-table";
import type { SyncTrack } from "../../../gateway/sync-health-panel";

export type ControlPlaneDashboardKpi = {
  syncStatus: "正常" | "过期" | "异常";
  onlineEndpoints: number;
  quotaRemainingPercent: number;
  todayCalls: string;
};

export const controlPlaneDashboardKpi: ControlPlaneDashboardKpi = {
  syncStatus: "过期",
  onlineEndpoints: 5,
  quotaRemainingPercent: 16,
  todayCalls: "128.4万",
};

export const controlPlaneDashboardSyncTracks: SyncTrack[] = [
  { id: "quota", label: "配额同步", status: "ok", lastSuccess: "12 秒前" },
  { id: "report", label: "报表同步", status: "ok", lastSuccess: "45 秒前" },
  {
    id: "hmac",
    label: "HMAC 心跳",
    status: "stale",
    lastSuccess: "8 分钟前",
    hint: "请检查出口网络与白名单配置",
  },
  { id: "license", label: "许可校验", status: "ok", lastSuccess: "2 分钟前" },
];

export const controlPlaneDashboardEndpoints: EndpointProbeRow[] = [
  {
    id: "ep-1",
    endpoint: "https://api.prod.internal/v1",
    instanceId: "gw-prod-01",
    status: "ready",
    latency: "42ms",
  },
  {
    id: "ep-2",
    endpoint: "https://api.staging.internal/v1",
    instanceId: "gw-stg-02",
    status: "unknown",
    hint: "过去 24 小时无探测记录",
  },
  {
    id: "ep-3",
    endpoint: "https://edge.cn-east.internal/v1",
    instanceId: "gw-edge-03",
    status: "ready",
    latency: "58ms",
  },
  {
    id: "ep-4",
    endpoint: "https://edge.airgap.local/v1",
    instanceId: "gw-edge-01",
    status: "failed",
    latency: "超时",
    hint: "连接被拒绝，请检查本地监听端口",
  },
  {
    id: "ep-5",
    endpoint: "https://api.dr.internal/v1",
    instanceId: "gw-dr-01",
    status: "ready",
    latency: "96ms",
  },
];

export type ControlPlaneQuickLink = {
  id: string;
  title: string;
  desc: string;
  targetId: string;
};

export const controlPlaneQuickLinks: ControlPlaneQuickLink[] = [
  {
    id: "g02",
    title: "部署模式 Hub",
    desc: "查看联网/离线部署矩阵与同步策略说明",
    targetId: "S02-G02",
  },
  {
    id: "g07",
    title: "端点探测列表",
    desc: "批量探测、筛选与异常端点处理",
    targetId: "S02-G07",
  },
  {
    id: "g08",
    title: "API Key 密钥 Hub",
    desc: "密钥列表、一次性展示与轮换",
    targetId: "S02-G08",
  },
];
