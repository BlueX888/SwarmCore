# S02-G07 端点探测列表

## 用途

Gateway 控制面专用端点探测全页，展示已注册 API 端点健康状态，支持搜索筛选、单点 debounce 探测与批量探测。

## 复制入口

```tsx
import { EndpointProbeListPage } from "@/templates/scenarios/gateway/endpoint-probe-list";

<EndpointProbeListPage
  onProbe={(rowId) => console.log("probe", rowId)}
  onBatchProbe={() => console.log("batch probe")}
/>
```

## 页面结构

| 区块 | 组件 | 说明 |
|------|------|------|
| KPI 摘要 | 四格卡片 | 总数、就绪、失败、未知 |
| 筛选栏 | Input + 状态 Chip | 搜索端点/实例；ready/failed/unknown 过滤 |
| 探测表 | EndpointProbeTable | debounce 300ms；ready/failed/unknown/testing Badge |
| 批量探测 | Button | 全部探测，探测中 disabled |
| 事件审计 | 内联表格 | 单点/批量探测留痕 |

## 关联 PRD

- `docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S02-gateway.md#s02-g07`
- `references/layout-patterns/control-plane.md`
- `templates/gateway/endpoint-probe-table.tsx`
