export const ds04Mock = {
  mapMarkers: [
    { id: "office-a", label: "写字楼 A 座", x: 38, y: 42, category: "office" as const, status: "normal" as const, detail: "入驻率 92%，今日访客 186 人次" },
    { id: "office-b", label: "写字楼 B 座", x: 52, y: 35, category: "office" as const, status: "warning" as const, detail: "空调能耗偏高，建议巡检" },
    { id: "res-a", label: "居民楼 1 号院", x: 28, y: 58, category: "residential" as const, status: "normal" as const, detail: "人口 1,240，今日报修 3 单" },
    { id: "res-b", label: "居民楼 2 号院", x: 62, y: 62, category: "residential" as const, status: "normal" as const, detail: "垃圾分类达标率 98.6%" },
    { id: "park-1", label: "地下停车场 P1", x: 45, y: 68, category: "parking" as const, status: "alert" as const, detail: "剩余车位 12，周转率 86%" },
    { id: "park-2", label: "地面停车场 P2", x: 70, y: 48, category: "parking" as const, status: "warning" as const, detail: "高峰时段接近饱和" },
  ],
  facilityRanking: [
    { rank: 1, label: "社区健身中心", value: 96 },
    { rank: 2, label: "便民服务中心", value: 94 },
    { rank: 3, label: "智慧驿站", value: 91 },
    { rank: 4, label: "社区图书馆", value: 89 },
    { rank: 5, label: "老年活动中心", value: 87 },
  ],
  peopleFlowTrend: {
    categories: ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"],
    series: [
      { name: "进入人流", data: [420, 680, 920, 760, 840, 1120, 680] },
      { name: "离开人流", data: [380, 620, 880, 720, 800, 980, 720] },
    ],
  },
  smartDevices: [
    { name: "门禁", value: 28 },
    { name: "监控", value: 24 },
    { name: "烟感", value: 18 },
    { name: "环境传感", value: 16 },
    { name: "其他", value: 14 },
  ],
  securityRadar: {
    categories: ["门禁", "监控", "消防", "环境", "停车"],
    series: [
      { name: "在线率", data: [98, 96, 99, 92, 88] },
      { name: "告警处置", data: [95, 90, 97, 86, 82] },
    ],
  },
  monitorRows: [
    { point: "东门监控", status: "正常", lastEvent: "人员通行", time: "19:08:22" },
    { point: "P1 道闸", status: "告警", lastEvent: "车位不足", time: "19:05:11" },
    { point: "B 座烟感", status: "正常", lastEvent: "巡检通过", time: "18:52:40" },
    { point: "2 号院门禁", status: "维护", lastEvent: "固件升级中", time: "18:30:00" },
  ],
  parkingKpis: [
    { label: "总车位", value: 486, unit: "个" },
    { label: "已占用", value: 412, unit: "个" },
    { label: "周转率", value: 86, unit: "%" },
    { label: "平均停留", value: 2.4, unit: "小时" },
  ],
  vehicleTraffic: {
    categories: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    series: [
      { name: "入场", data: [820, 860, 910, 880, 940, 720, 680] },
      { name: "出场", data: [810, 850, 900, 870, 930, 710, 670] },
    ],
  },
  greeningProgress: [{ label: "绿化覆盖率", value: 78, unit: "%" }],
} as const;

export const {
  mapMarkers: ds04MapMarkers,
  facilityRanking: ds04FacilityRanking,
  peopleFlowTrend: ds04PeopleFlowTrend,
  smartDevices: ds04SmartDevices,
  securityRadar: ds04SecurityRadar,
  monitorRows: ds04MonitorRows,
  parkingKpis: ds04ParkingKpis,
  vehicleTraffic: ds04VehicleTraffic,
  greeningProgress: ds04GreeningProgress,
} = ds04Mock;
