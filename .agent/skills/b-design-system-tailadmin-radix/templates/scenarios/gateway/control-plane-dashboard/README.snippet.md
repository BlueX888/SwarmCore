# S02-G01 控制面总览 Dashboard

## 复制入口

```tsx
import { ControlPlaneDashboardPage } from "@/templates/scenarios/gateway/control-plane-dashboard";
```

## 组件组合

- KPI 行：同步状态、在线端点、配额余量、今日调用
- `SyncHealthPanel` — 四轨同步健康摘要
- `BalanceQuotaSummary` — 余额/配额/License/实例 KPI
- `EndpointProbeTable` — 精简 5 行端点探测
- 快捷入口卡片 — 链到 S02-G02 / S02-G07 / S02-G08

## 与 ControlPlaneHub 区别

本页从 `ControlPlaneHub` 拆出 Dashboard 视图，**不包含** DeploymentModeMatrix、LicenseIssuePanel、ApiKeyRevealPanel，避免 Hub 嵌套。

## PRD

`docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g01`

## Example 路由

`showcase-scenario-gateway-control-plane`
