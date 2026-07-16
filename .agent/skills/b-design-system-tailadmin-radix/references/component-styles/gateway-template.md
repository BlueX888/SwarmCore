# 企业网关 / 控制平面组件模板

技术栈：**React + shadcn/ui + Radix + Tailwind v4**

## 读取顺序

1. `references/deployment-mode-matrix.md` — 部署模式分叉规则
2. `references/layout-patterns/control-plane.md` — 控制平面页面结构
3. `references/gateway-visual.md` · `gateway-interaction.md` — 视觉与交互
4. 本文件选可复制模板
5. `templates/gateway/control-plane-hub.tsx` — 页面级组合入口

## 控制平面场景组件

| 组件 | 状态覆盖 | 模板 |
|---|---|---|
| DeploymentModeMatrix | connected/airgap/local/cloud/private | `templates/gateway/deployment-mode-matrix.tsx` |
| LicenseIssuePanel | issue/renew · valid/expiring/expired · one-time copy | `templates/gateway/license-issue-panel.tsx` |
| SyncHealthPanel | ok/pending/error/stale/frozen · 四轨 | `templates/gateway/sync-health-panel.tsx` |
| EndpointProbeTable | ready/failed/unknown/testing · debounce 300ms | `templates/gateway/endpoint-probe-table.tsx` |
| ApiKeyRevealPanel | one-time reveal · copy · rotate · revoke | `templates/gateway/api-key-reveal-panel.tsx` |
| BalanceQuotaSummary | balance · quota · low/critical/frozen | `templates/gateway/balance-quota-summary.tsx` |
| ControlPlaneHub | 页面组合 | `templates/gateway/control-plane-hub.tsx` |

## 视觉验收

- 部署模式 chip：长描述 `truncate`，选中态 brand 浅底
- KPI 行：`grid-cols-4` desktop，金额 `tabular-nums`，低余额 Badge 不裁切
- 同步四轨：error 轨显示 hint + Retry，frozen 显示全局 Alert
- Endpoint 表：`font-mono` 标识符，`truncate` + title tooltip，Probe debounce 防连点
- License/API Key：一次性展示区 brand 浅底边框，复制后 dismiss

## 分叉规则

| 模式 | 显示同步 | 显示余额 |
|---|---|---|
| connected | ✓ | ✓ |
| airgap | ✗ | ✗ |
| local/cloud/private | 按配置 | 按配置 |

## 组合示例

```tsx
import { ControlPlaneHub } from "@/components/gateway/control-plane-hub";
import { DeploymentModeMatrix } from "@/components/gateway/deployment-mode-matrix";
import { EndpointProbeTable } from "@/components/gateway/endpoint-probe-table";
```
