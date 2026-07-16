# DS-05 生态资源大数据平台

L3 地图主导布局 + 内蒙古 MapScene 城市标注浮层 + KPI×6、设施仪表、水资源趋势、产业环图、交通柱图、公共卫生四宫格、矿藏排行与底 Timeline。

```tsx
import { EcologicalResourcesPlatformScreen } from "@/templates/scenarios/data-screen/ds-05-ecological-resources-platform";
```

**依赖**：L3、`ScreenKpiStrip`、`ScreenMapScene`、`ScreenGaugeRing`、`ScreenLineAreaChart`、`ScreenDonutChart`、`ScreenGroupedBarChart`、`ScreenRankBarList`、`ScreenTimeline`

**交互**：地图城市标注 click/hover 信息浮层；刷新徽章；图表 tooltip；时间轴节点状态色。
