# 治理安全组件模板

技术栈：**React + shadcn/ui + Radix + Tailwind v4**

## 读取顺序

1. `references/domain-scenarios.md` — 治理/审计/密钥场景路由
2. `references/decision-matrix.md` — 权限页 vs 审计页 vs 密钥面板选型
3. 本文件选可复制模板
4. `templates/gateway/api-key-reveal-panel.tsx` — 密钥展示细化

## 组件索引

| 组件 | 状态覆盖 | 模板 |
|---|---|---|
| PermissionMatrix | inherited/custom/disabled、冲突提示 | `templates/governance/permission-matrix.tsx` |
| AuditLogTable | 搜索/导出/空态/加载/行点击 | `templates/governance/audit-log-table.tsx` |
| ComplianceAlert | low/medium/high/critical | `templates/governance/compliance-alert.tsx` |
| AuthProviderWizard | LDAP/OAuth/OIDC/SAML、探测、回滚 | `templates/governance/auth-provider-wizard.tsx` |
| SecretKeyPanel | mask/copy/rotate/revoke、审计说明 | `templates/governance/secret-key-panel.tsx` |
| ApiKeyRevealPanel | 一次性展示、网关场景 | `templates/gateway/api-key-reveal-panel.tsx` |

## 页面组合建议

| 场景 | 推荐结构 | 不要使用 |
|---|---|---|
| RBAC 配置 | Hub Tabs + PermissionMatrix + 保存条 | 单页无分组的巨型矩阵 |
| 审计日志 | 筛选栏 + AuditLogTable + 详情 Drawer | 卡片瀑布流冒充日志 |
| 合规提示 | ComplianceAlert 置于相关操作上方 | 全屏营销 Banner |
| 密钥管理 | SecretKeyPanel 或 ApiKeyRevealPanel + 审计说明 | 明文长期展示 |
| 认证源配置 | AuthProviderWizard + SecretKeyPanel | 单页堆叠所有 IdP 字段 |

## 文案与摩擦

- 危险动作（吊销、封禁、降级权限）必须二次确认。
- 合规说明保持克制，一行标题 + 两行说明即可。
- 审计表时间列使用 `tabular-nums`，对象列 `font-mono` + `truncate`。
- 移动端矩阵表必须 `overflow-x-auto`，不得挤压复选框列。

## 组合示例

```tsx
import { PermissionMatrix } from "@/components/governance/permission-matrix";
import { AuditLogTable } from "@/components/governance/audit-log-table";
import { ComplianceAlert } from "@/components/governance/compliance-alert";
```
