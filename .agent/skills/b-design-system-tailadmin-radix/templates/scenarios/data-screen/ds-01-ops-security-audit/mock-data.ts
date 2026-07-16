export const ds01Mock = {
  kpis: [
    { label: "在线会话", value: 0 },
    { label: "用户总数", value: 13 },
    { label: "资产总数", value: 5 },
  ],
  assetActivityPie: [
    { name: "TEST", value: 40 },
    { name: "Default", value: 40 },
    { name: "SYSTEM", value: 20 },
  ],
  userLoginDay: [
    { rank: 1, label: "admin", value: 12 },
    { rank: 2, label: "operator", value: 8 },
    { rank: 3, label: "audit", value: 5 },
    { rank: 4, label: "guest", value: 3 },
    { rank: 5, label: "devops", value: 2 },
  ],
  userLoginWeek: [
    { rank: 1, label: "admin", value: 45 },
    { rank: 2, label: "audit", value: 30 },
    { rank: 3, label: "operator", value: 22 },
    { rank: 4, label: "devops", value: 18 },
    { rank: 5, label: "guest", value: 9 },
  ],
  activeTrend: {
    categories: ["09-02", "09-03", "09-04", "09-05"],
    series: [
      { name: "活跃用户数", data: [2, 4, 3, 5] },
      { name: "活跃资产数", data: [3, 3, 4, 4] },
      { name: "会话数", data: [5, 8, 6, 9] },
    ],
  },
  dangerCommands: [
    {
      user: "Administrator(admin)",
      asset: "192.168.1.10",
      input: "rm -rf test_directory",
      time: "09-05 14:22",
    },
    {
      user: "operator",
      asset: "192.168.1.20",
      input: "shutdown -h now",
      time: "09-05 13:58",
    },
    {
      user: "audit",
      asset: "10.0.0.5",
      input: "iptables -F",
      time: "09-05 12:11",
    },
  ],
  assetGroupPie: [
    { name: "TEST", value: 33.33 },
    { name: "Default", value: 33.33 },
    { name: "SYSTEM", value: 33.34 },
  ],
  assetTopDay: [
    { rank: 1, label: "192.168.1.10", value: 20 },
    { rank: 2, label: "10.0.0.5", value: 14 },
    { rank: 3, label: "192.168.1.20", value: 11 },
    { rank: 4, label: "172.16.0.8", value: 7 },
    { rank: 5, label: "10.0.0.12", value: 4 },
  ],
  assetTopWeek: [
    { rank: 1, label: "192.168.1.10", value: 88 },
    { rank: 2, label: "10.0.0.5", value: 62 },
    { rank: 3, label: "192.168.1.20", value: 51 },
    { rank: 4, label: "172.16.0.8", value: 33 },
    { rank: 5, label: "10.0.0.12", value: 19 },
  ],
} as const;

export type Ds01Mock = typeof ds01Mock;

export const ds01Kpis = ds01Mock.kpis.map((item) => ({ ...item }));
export const ds01AssetActivityPie = ds01Mock.assetActivityPie.map((item) => ({ ...item }));
export const ds01UserLoginDay = ds01Mock.userLoginDay.map((item) => ({ ...item }));
export const ds01UserLoginWeek = ds01Mock.userLoginWeek.map((item) => ({ ...item }));
export const ds01ActiveTrend = {
  categories: [...ds01Mock.activeTrend.categories],
  series: ds01Mock.activeTrend.series.map((item) => ({
    name: item.name,
    data: [...item.data],
  })),
};
export const ds01DangerCommands = ds01Mock.dangerCommands.map((item) => ({ ...item }));
export const ds01AssetGroupPie = ds01Mock.assetGroupPie.map((item) => ({ ...item }));
export const ds01AssetTopDay = ds01Mock.assetTopDay.map((item) => ({ ...item }));
export const ds01AssetTopWeek = ds01Mock.assetTopWeek.map((item) => ({ ...item }));
