export const ds06Mock = {
  goalCompletion: 57,
  funnelStages: [
    { label: "访问", value: 12840, rate: "100%" },
    { label: "浏览商品", value: 8620, rate: "67.1%" },
    { label: "加入购物车", value: 4210, rate: "32.8%" },
    { label: "完成支付", value: 2380, rate: "18.5%" },
  ],
  hotWords: [
    { text: "夏季新品", weight: 96 },
    { text: "限时折扣", weight: 88 },
    { text: "会员专享", weight: 82 },
    { text: "包邮", weight: 76 },
    { text: "爆款", weight: 71 },
    { text: "直播同款", weight: 65 },
    { text: "满减", weight: 58 },
    { text: "新品首发", weight: 52 },
  ],
  userRadar: {
    categories: ["消费频次", "客单价", "复购率", "活跃度", "满意度"],
    series: [
      { name: "男性用户", data: [72, 65, 58, 70, 68] },
      { name: "女性用户", data: [80, 78, 72, 85, 82] },
    ],
  },
  spendingBars: {
    categories: ["产品 A", "产品 B", "产品 C", "产品 D"],
    series: [
      { name: "男性", data: [420, 380, 290, 210] },
      { name: "女性", data: [510, 460, 390, 320] },
    ],
  },
  userCategoryPie: [
    { name: "新客", value: 28 },
    { name: "活跃会员", value: 42 },
    { name: "沉睡用户", value: 18 },
    { name: "高价值客户", value: 12 },
  ],
  monthlyGrowth: {
    categories: ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
    series: [{ name: "新增用户（千人）", data: [12, 15, 18, 14, 22, 26, 24, 28, 31, 29, 35, 38] }],
  },
  channelTraffic: {
    pie: [
      { name: "自然搜索", value: 32 },
      { name: "付费投放", value: 28 },
      { name: "社交裂变", value: 22 },
      { name: "直接访问", value: 18 },
    ],
    table: [
      { channel: "自然搜索", visits: "128,420", share: "32.0%", trend: "+8.2%" },
      { channel: "付费投放", visits: "112,860", share: "28.1%", trend: "+5.4%" },
      { channel: "社交裂变", visits: "88,640", share: "22.1%", trend: "+12.6%" },
      { channel: "直接访问", visits: "72,580", share: "17.8%", trend: "+2.1%" },
    ],
  },
  revenueTrend: {
    categories: ["2019", "2020", "2021", "2022", "2023", "2024"],
    series: [
      { name: "营收（百万元）", data: [82, 96, 118, 142, 168, 195] },
    ],
  },
  provinceActiveUsers: [
    { rank: 1, label: "广东", value: 12840 },
    { rank: 2, label: "浙江", value: 11260 },
    { rank: 3, label: "江苏", value: 9860 },
    { rank: 4, label: "上海", value: 8420 },
    { rank: 5, label: "北京", value: 7980 },
  ],
};

export const {
  goalCompletion: ds06GoalCompletion,
  funnelStages: ds06FunnelStages,
  hotWords: ds06HotWords,
  userRadar: ds06UserRadar,
  spendingBars: ds06SpendingBars,
  userCategoryPie: ds06UserCategoryPie,
  monthlyGrowth: ds06MonthlyGrowth,
  channelTraffic: ds06ChannelTraffic,
  revenueTrend: ds06RevenueTrend,
  provinceActiveUsers: ds06ProvinceActiveUsers,
} = ds06Mock;
