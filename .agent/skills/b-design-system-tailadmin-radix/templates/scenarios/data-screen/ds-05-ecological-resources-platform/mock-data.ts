export const ds05Mock = {
  kpiStrip: [
    { label: "森林覆盖率", value: "22.1", unit: "%" },
    { label: "草原面积", value: "7.88", unit: "亿亩" },
    { label: "水资源总量", value: "412", unit: "亿m³" },
    { label: "矿产储量", value: "186", unit: "种" },
    { label: "生态产业总值", value: "3,280", unit: "亿元" },
    { label: "监测站点", value: "1,246", unit: "个" },
  ],
  mapMarkers: [
    { id: "hhht", label: "呼和浩特", x: 42, y: 52, category: "facility" as const, status: "normal" as const, detail: "首府 · 空气质量优良率 92.4%，草原修复面积 12.6 万亩" },
    { id: "bt", label: "包头", x: 35, y: 48, category: "office" as const, status: "normal" as const, detail: "工业重镇 · 黄河流域水质达标率 96.8%" },
    { id: "eeds", label: "鄂尔多斯", x: 38, y: 62, category: "other" as const, status: "warning" as const, detail: "能源基地 · 荒漠化治理进度 78%，需加强防风固沙" },
    { id: "hlbe", label: "呼伦贝尔", x: 72, y: 28, category: "residential" as const, status: "normal" as const, detail: "草原明珠 · 天然林保护面积 3,420 万亩" },
    { id: "cf", label: "赤峰", x: 58, y: 45, category: "facility" as const, status: "normal" as const, detail: "辽河流域 · 湿地恢复率 85.2%" },
    { id: "wlcb", label: "乌兰察布", x: 44, y: 42, category: "parking" as const, status: "alert" as const, detail: "风电光伏集中区 · 沙尘预警，建议启动应急响应" },
  ],
  facilityGauges: [
    { label: "监测站在线", value: 98, unit: "%" },
    { label: "遥感覆盖", value: 94, unit: "%" },
    { label: "无人机巡检", value: 86, unit: "%" },
    { label: "物联网传感", value: 91, unit: "%" },
  ],
  waterResources: {
    categories: ["1月", "2月", "3月", "4月", "5月", "6月"],
    series: [
      { name: "地表水", data: [38, 42, 45, 48, 52, 49] },
      { name: "地下水", data: [28, 30, 32, 31, 33, 34] },
    ],
  },
  industryDonut: [
    { name: "生态旅游", value: 32 },
    { name: "清洁能源", value: 28 },
    { name: "绿色农牧", value: 22 },
    { name: "碳汇交易", value: 12 },
    { name: "其他", value: 6 },
  ],
  trafficBars: {
    categories: ["公路", "铁路", "航空", "水运", "管道"],
    series: [
      { name: "货运量", data: [4200, 2800, 680, 320, 1560] },
      { name: "客运量", data: [3100, 2400, 920, 180, 0] },
    ],
  },
  publicHealthGauges: [
    { label: "饮用水达标", value: 99.2, unit: "%" },
    { label: "空气质量优良", value: 88.6, unit: "%" },
    { label: "土壤监测合格", value: 96.4, unit: "%" },
    { label: "噪声达标率", value: 94.1, unit: "%" },
  ],
  mineralRanking: [
    { rank: 1, label: "煤炭", value: 92 },
    { rank: 2, label: "稀土", value: 88 },
    { rank: 3, label: "铁矿", value: 76 },
    { rank: 4, label: "铜矿", value: 68 },
    { rank: 5, label: "金矿", value: 54 },
  ],
  timeline: [
    { id: "t1", date: "2024-03", title: "三北防护林五期启动", description: "规划造林 1,200 万亩", status: "done" as const },
    { id: "t2", date: "2024-08", title: "黄河流域生态治理", description: "水质达标率提升至 96%", status: "done" as const },
    { id: "t3", date: "2025-01", title: "草原禁牧休牧", description: "覆盖 4,800 万亩草场", status: "done" as const },
    { id: "t4", date: "2025-06", title: "碳汇交易平台上线", description: "累计交易量 128 万吨", status: "active" as const },
    { id: "t5", date: "2025-12", title: "荒漠化零增长目标", description: "沙化土地治理 85%", status: "pending" as const },
    { id: "t6", date: "2026-06", title: "生物多样性普查", description: "物种名录更新计划", status: "pending" as const },
  ],
} as const;

export const {
  kpiStrip: ds05KpiStrip,
  mapMarkers: ds05MapMarkers,
  facilityGauges: ds05FacilityGauges,
  waterResources: ds05WaterResources,
  industryDonut: ds05IndustryDonut,
  trafficBars: ds05TrafficBars,
  publicHealthGauges: ds05PublicHealthGauges,
  mineralRanking: ds05MineralRanking,
  timeline: ds05Timeline,
} = ds05Mock;
