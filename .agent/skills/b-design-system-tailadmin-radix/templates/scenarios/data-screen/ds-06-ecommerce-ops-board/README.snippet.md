# DS-06 电商运营数据看板

## 复制入口

```tsx
import { EcommerceOpsBoardScreen } from "@/templates/scenarios/data-screen/ds-06-ecommerce-ops-board";
```

## 依赖

- L4：`templates/bi/screen/layouts/l4-light-analytics-board.tsx`
- 原子：A04 Donut、A07 Funnel、A08 Radar、A10 GroupedBar、A11 WordCloud（tag 云降级）
- 主题：`chart-theme-screen-light` + `ScreenPanel variant="light"`

## 布局

左列目标环图 + 转化漏斗；中部热词/雷达、消费柱图、用户分类；右列营收趋势 + 省份排行；底栏 12 月增长 + 渠道流量。

## PRD

`docs/spec/b-design-system-tailadmin-radix/prd/data-screens/pages.md#ds-06`
