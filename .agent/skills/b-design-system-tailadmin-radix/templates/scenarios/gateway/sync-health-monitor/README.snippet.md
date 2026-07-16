# S02-G06 同步健康监控

## 用途

Gateway 控制面专用同步监控页，展示 quota / report / HMAC / heartbeat 四轨健康状态，支持全部刷新、单轨重试与事件审计。

## 复制入口

```tsx
import { SyncHealthMonitorPage } from "@/templates/scenarios/gateway/sync-health-monitor";

<SyncHealthMonitorPage
  onRefreshAll={() => console.log("refresh all")}
  onRetry={(trackId) => console.log("retry", trackId)}
/>
```

## 页面结构

| 区块 | 组件 | 说明 |
|------|------|------|
| KPI 摘要 | 四格卡片 | 综合健康、绑定实例、上次/下次同步 |
| 四轨面板 | SyncHealthPanel | quota/report/HMAC/heartbeat + frozen Alert |
| 刷新 | Button | 全部刷新，刷新中 disabled + spin |
| 事件审计 | 内联表格 | 自动/手动/重试动作留痕 |

## 关联 PRD

- `docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g06`
- `references/layout-patterns/control-plane.md`
- `templates/gateway/sync-health-panel.tsx`
