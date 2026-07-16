export const ds07Mock = {
  kpis: [
    { label: "四轨综合同步成功率", value: "98.6%" },
    { label: "在线端点（共 28 实例）", value: 24 },
    { label: "配额余量（840K / 1M）", value: "16%" },
    { label: "今日 API 调用（较昨日 +6.2%）", value: "128万" },
  ],
  endpointProbePie: [
    { name: "就绪", value: 18 },
    { name: "失败", value: 4 },
    { name: "未知", value: 6 },
  ],
  syncTrackSuccess: [
    { rank: 1, label: "配额同步", value: 99.2 },
    { rank: 2, label: "报表同步", value: 98.1 },
    { rank: 3, label: "HMAC 心跳", value: 96.5 },
    { rank: 4, label: "许可校验", value: 100 },
  ],
  apiCallTrend: {
    categories: ["00", "04", "08", "12", "16", "20", "24"],
    series: [
      { name: "API 调用量（万次）", data: [3.2, 2.8, 4.1, 6.5, 8.2, 7.4, 5.6] },
      { name: "成功请求", data: [3.1, 2.7, 4.0, 6.3, 8.0, 7.2, 5.5] },
    ],
  },
  quotaConsumeTrend: {
    categories: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    series: [
      { name: "配额消耗（元）", data: [8200, 9100, 8800, 10200, 11500, 6400, 5900] },
      { name: "余额扣减（元）", data: [7600, 8400, 8100, 9600, 10800, 6000, 5500] },
    ],
  },
  endpointFailTop: [
    { rank: 1, label: "edge.airgap.local", value: 12 },
    { rank: 2, label: "api.staging.internal", value: 8 },
    { rank: 3, label: "gw-backup-02", value: 5 },
    { rank: 4, label: "api.dr.internal", value: 3 },
    { rank: 5, label: "gw-edge-03", value: 2 },
  ],
  alertRows: [
    {
      id: "al-1",
      time: "14:22",
      location: "生产集群",
      content: "端点 gw-prod-02 探测超时，已连续失败 3 次",
      status: "critical" as const,
    },
    {
      id: "al-2",
      time: "14:18",
      location: "配额中心",
      content: "企业池配额余量低于 20%，建议扩容或限流",
      status: "warning" as const,
    },
    {
      id: "al-3",
      time: "14:05",
      location: "同步服务",
      content: "HMAC 心跳延迟升至 8 分钟，出口连通性待核查",
      status: "warning" as const,
    },
    {
      id: "al-4",
      time: "13:48",
      location: "许可服务",
      content: "离线节点 license 校验已通过本地缓存",
      status: "info" as const,
    },
    {
      id: "al-5",
      time: "13:30",
      location: "端点探测",
      content: "staging 环境 2 个实例状态由未知恢复为就绪",
      status: "resolved" as const,
    },
  ],
} as const;

export type Ds07Mock = typeof ds07Mock;

export const ds07Kpis = ds07Mock.kpis.map((item) => ({ ...item }));
export const ds07EndpointProbePie = ds07Mock.endpointProbePie.map((item) => ({ ...item }));
export const ds07SyncTrackSuccess = ds07Mock.syncTrackSuccess.map((item) => ({ ...item }));
export const ds07ApiCallTrend = {
  categories: [...ds07Mock.apiCallTrend.categories],
  series: ds07Mock.apiCallTrend.series.map((item) => ({
    name: item.name,
    data: [...item.data],
  })),
};
export const ds07QuotaConsumeTrend = {
  categories: [...ds07Mock.quotaConsumeTrend.categories],
  series: ds07Mock.quotaConsumeTrend.series.map((item) => ({
    name: item.name,
    data: [...item.data],
  })),
};
export const ds07EndpointFailTop = ds07Mock.endpointFailTop.map((item) => ({ ...item }));
export const ds07AlertRows = ds07Mock.alertRows.map((item) => ({ ...item }));
