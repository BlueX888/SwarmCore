# OrderList 优先级队列

单栏拖拽排序页壳（对标 PrimeVue OrderList）：

```
PageHeader
├── 说明文案（可选）
├── OrderList（items + onReorder）
└── 底部保存 Button
```

## 组件

- `order-list.tsx` + `use-sortable-list.ts`（`@dnd-kit`）

## 场景

- 功能开关优先级
- 导航菜单排序
- 审批步骤顺序（只读时可禁用拖拽）

## 决策

- 双栏穿梭 + 目标栏排序 → `Transfer` `targetSortable`
- 树形层级拖拽 → `Tree` `draggable` + `onDrop`
