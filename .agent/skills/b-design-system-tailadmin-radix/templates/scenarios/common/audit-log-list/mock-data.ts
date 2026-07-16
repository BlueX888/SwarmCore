export type AuditLogRow = {
  id: string;
  time: string;
  operator: string;
  ip: string;
  action: string;
  resource: string;
  result: "success" | "failure";
};

export const auditLogListMock: AuditLogRow[] = [
  { id: "1", time: "2026-06-28 09:12:03", operator: "周敏", ip: "10.12.8.44", action: "登录系统", resource: "控制台", result: "success" },
  { id: "2", time: "2026-06-28 09:18:27", operator: "林越", ip: "10.12.9.18", action: "导出审计日志", resource: "审计中心", result: "success" },
  { id: "3", time: "2026-06-28 09:25:11", operator: "陈可", ip: "10.12.7.92", action: "修改角色权限", resource: "角色管理/运营管理员", result: "success" },
  { id: "4", time: "2026-06-28 09:31:45", operator: "王磊", ip: "10.12.6.33", action: "删除 API 密钥", resource: "密钥管理/prod-gateway", result: "failure" },
  { id: "5", time: "2026-06-28 09:38:02", operator: "赵婷", ip: "10.12.8.51", action: "创建资源组", resource: "资源组/华东生产", result: "success" },
  { id: "6", time: "2026-06-28 09:44:19", operator: "周敏", ip: "10.12.8.44", action: "审批通过", resource: "变更单/CHG-2026-0612", result: "success" },
  { id: "7", time: "2026-06-28 09:52:33", operator: "guest", ip: "203.0.113.18", action: "登录系统", resource: "控制台", result: "failure" },
  { id: "8", time: "2026-06-28 10:03:07", operator: "林越", ip: "10.12.9.18", action: "重置用户密码", resource: "用户管理/lihua", result: "success" },
  { id: "9", time: "2026-06-28 10:11:54", operator: "陈可", ip: "10.12.7.92", action: "更新配额", resource: "租户配额/深度对话企业版", result: "success" },
  { id: "10", time: "2026-06-28 10:19:28", operator: "王磊", ip: "10.12.6.33", action: "禁用账号", resource: "用户管理/temp-audit", result: "success" },
  { id: "11", time: "2026-06-28 10:27:41", operator: "赵婷", ip: "10.12.8.51", action: "同步配置", resource: "网关配置/prod-cn", result: "failure" },
  { id: "12", time: "2026-06-28 10:35:16", operator: "周敏", ip: "10.12.8.44", action: "查看敏感字段", resource: "密钥详情/sk-live-01", result: "success" },
  { id: "13", time: "2026-06-28 10:42:03", operator: "林越", ip: "10.12.9.18", action: "批量导出", resource: "审计中心", result: "success" },
  { id: "14", time: "2026-06-28 10:48:55", operator: "陈可", ip: "10.12.7.92", action: "撤销审批", resource: "变更单/CHG-2026-0610", result: "success" },
  { id: "15", time: "2026-06-28 10:56:22", operator: "王磊", ip: "10.12.6.33", action: "删除资源", resource: "对象存储/backup-2025-q4", result: "failure" },
  { id: "16", time: "2026-06-28 11:04:38", operator: "赵婷", ip: "10.12.8.51", action: "绑定 MFA", resource: "安全设置", result: "success" },
];
