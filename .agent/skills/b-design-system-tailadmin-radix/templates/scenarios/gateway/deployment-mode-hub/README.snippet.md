# S02-G02 部署模式 Hub

## 用途

平台管理员在 Hub Tabs 中配置部署模式、查看同步策略与连通性要求。适用于企业网关控制面「联网 / 离线」分叉场景。

## 复制入口

```tsx
import { DeploymentModeHubPage } from "@/templates/scenarios/gateway/deployment-mode-hub";

<DeploymentModeHubPage
  deploymentMode="connected"
  onDeploymentModeChange={(mode) => console.log(mode)}
/>
```

## 页面结构

| Tab | 内容 |
|-----|------|
| 部署模式 | `DeploymentModeMatrix` + connected/airgap Banner |
| 同步策略 | 四轨同步项按模式启用/不适用 |
| 连通性说明 | 出站/入站/双向规则卡片 |

## 关联 PRD

- `docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g02`
- `references/layout-patterns/hub-tabs.md`
- `references/deployment-mode-matrix.md`
