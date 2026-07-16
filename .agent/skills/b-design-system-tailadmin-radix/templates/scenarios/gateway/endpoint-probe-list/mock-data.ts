export type EndpointProbeStatus = "ready" | "failed" | "unknown" | "testing";

export type EndpointProbeRow = {
  id: string;
  endpoint: string;
  instanceId: string;
  status: EndpointProbeStatus;
  latency?: string;
  hint?: string;
};

export type EndpointProbeKpi = {
  total: number;
  readyCount: number;
  failedCount: number;
  unknownCount: number;
  lastBatchProbeAt: string;
  regionLabel: string;
};

export type EndpointProbeEvent = {
  id: string;
  occurredAt: string;
  endpoint: string;
  instanceId: string;
  action: "single" | "batch";
  result: "ready" | "failed" | "unknown";
  latency?: string;
  message: string;
};

export const endpointProbeKpi: EndpointProbeKpi = {
  total: 8,
  readyCount: 4,
  failedCount: 2,
  unknownCount: 2,
  lastBatchProbeAt: "2026-06-29 08:55:12",
  regionLabel: "华东 · 生产集群",
};

export const endpointProbeRows: EndpointProbeRow[] = [
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
  {
    id: "ep-6",
    endpoint: "https://api.canary.internal/v1",
    instanceId: "gw-canary-01",
    status: "failed",
    latency: "502",
    hint: "上游网关返回 502，灰度路由可能未就绪",
  },
  {
    id: "ep-7",
    endpoint: "https://api.partner.internal/v1",
    instanceId: "gw-partner-02",
    status: "unknown",
    hint: "新注册实例，尚未完成首次探测",
  },
  {
    id: "ep-8",
    endpoint: "https://api.prod.internal/v2",
    instanceId: "gw-prod-02",
    status: "ready",
    latency: "38ms",
  },
];

export const endpointProbeEvents: EndpointProbeEvent[] = [
  {
    id: "evt-1",
    occurredAt: "2026-06-29 08:55:12",
    endpoint: "批量探测",
    instanceId: "全部实例",
    action: "batch",
    result: "ready",
    message: "8 个端点完成批量探测，2 个失败、2 个未知",
  },
  {
    id: "evt-2",
    occurredAt: "2026-06-29 08:52:40",
    endpoint: "https://edge.airgap.local/v1",
    instanceId: "gw-edge-01",
    action: "single",
    result: "failed",
    latency: "超时",
    message: "TCP 连接超时，离线实例可能未启动",
  },
  {
    id: "evt-3",
    occurredAt: "2026-06-29 08:48:15",
    endpoint: "https://api.prod.internal/v1",
    instanceId: "gw-prod-01",
    action: "single",
    result: "ready",
    latency: "42ms",
    message: "HTTP 200，健康检查通过",
  },
  {
    id: "evt-4",
    occurredAt: "2026-06-29 08:45:00",
    endpoint: "https://api.canary.internal/v1",
    instanceId: "gw-canary-01",
    action: "single",
    result: "failed",
    latency: "502",
    message: "上游返回 502 Bad Gateway",
  },
];

export const probeActionLabel: Record<EndpointProbeEvent["action"], string> = {
  single: "单点探测",
  batch: "批量探测",
};

export const probeResultLabel: Record<EndpointProbeEvent["result"], string> = {
  ready: "就绪",
  failed: "失败",
  unknown: "未知",
};
