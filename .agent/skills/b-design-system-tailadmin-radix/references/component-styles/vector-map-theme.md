# Vector Map 主题 — jVectorMap

独立 Vector Map 主题 shard。源：`components/maps/vector-map/*`、`pages/Maps/VectorMap.tsx`。

**库**：`@react-jvectormap/core` + geodata 包（`world`、`unitedstates`）。

可复制模板：`templates/lib/vector-map-theme.ts`

## 检索别名

| 意图 | 读本节 |
|---|---|
| 页面布局 | `#page-layout` |
| 全球 markers | `#global-markers` |
| 国家流量热力 | `#traffic-heatmap` |
| 美国州级热力 | `#us-heatmap` |
| region/marker 预设 | `#region-marker-presets` |
| Zoom 控件 | `#zoom-controls` |
| CSS 覆盖 | `#css-overrides` |
| 加载/错误 | `#data-states` |

## Page Layout

路由：`/vector-map`（见 `route-index.md` Charts & Maps）。

```tsx
import { vectorMapPageStackClass } from "@/lib/vector-map-theme";

<div className={vectorMapPageStackClass}>
  <GlobalDistributionCard />
  <TrafficAnalyticsCard />
  <UsHeatmapCard />
</div>
```

- 页面：`flex flex-col gap-6`（源为三卡纵向堆叠，非栅格）
- 与 `/maps`（MapLibre/iframe/Leaflet）分离选型

## Global Markers

```tsx
import { VectorMap } from "@react-jvectormap/core";
import { worldMill } from "@react-jvectormap/world";
import {
  vectorMapContainerClass,
  defaultVectorMapZoomOptions,
  globalMarkerRegionStyle,
  globalMarkerStyle,
} from "@/lib/vector-map-theme";

<div className={vectorMapInnerWrapperClass}>
  <div className={`map-btn w-full ${vectorMapContainerClass}`}>
    <VectorMap
      map={worldMill}
      {...defaultVectorMapZoomOptions}
      regionStyle={globalMarkerRegionStyle}
      markers={markers}
      markerStyle={globalMarkerStyle}
      onRegionTipShow={() => {}}
      style={{ width: "100%", height: "100%" }}
    />
  </div>
</div>
```

- 区域初始 `#D9D9D9` 无描边；hover `#465FFF` opacity 0.7
- markers：`fill #465FFF`，hover `#3538CD`

## Traffic Heatmap

```tsx
import { createTrafficRegionStyleInjector, trafficRegionStyle } from "@/lib/vector-map-theme";

useEffect(() => createTrafficRegionStyleInjector("mapTrafficAnalytics"), []);

<div id="mapTrafficAnalytics" className={`map-btn w-full ${vectorMapContainerClass}`}>
  <VectorMap map={worldMill} regionStyle={trafficRegionStyle} mapRef={mapRef} ... />
</div>
```

- 基础 fill `#C5D8FF` + 白描边 0.5px
- 重点国家通过 `trafficRegionFills` 注入（US `#3538CD`，CA/CN `#8098F9` 等）

## US Heatmap

```tsx
import { usAea } from "@react-jvectormap/unitedstates";
import { usHeatmapRegionStyle, usHeatmapMarkerStyle } from "@/lib/vector-map-theme";

<VectorMap
  map={usAea}
  regionStyle={usHeatmapRegionStyle}
  markers={cityMarkers}
  markerStyle={usHeatmapMarkerStyle}
  mapRef={mapRef}
/>
```

- 州级默认 `#C5D8FF`；高亮州 `US-CA`/`US-NV` → `#465FFF`，`US-NY` 等 → `#3538CD`
- city markers：白描边 `strokeWidth 2`

## Zoom Controls

```tsx
import { vectorMapZoomWrapperClass, vectorMapZoomStackClass, vectorMapZoomButtonClass } from "@/lib/vector-map-theme";
import { createVectorMapZoomHandlers } from "@/lib/vector-map-theme";

const { zoomIn, zoomOut } = createVectorMapZoomHandlers(mapRef);

<div className={vectorMapZoomWrapperClass}>
  <div className={vectorMapZoomStackClass}>
    <button type="button" className={vectorMapZoomButtonTopClass} onClick={zoomIn} aria-label="Zoom in">+</button>
    <button type="button" className={vectorMapZoomButtonClass} onClick={zoomOut} aria-label="Zoom out">−</button>
  </div>
</div>
```

- 定位：`absolute bottom-3 right-3 z-10`
- 隐藏库自带 `.jvectormap-zoomin/out`（见 CSS 覆盖）

## CSS Overrides

宿主 `index.css` 引入 `jvectormapCssOverrides`：

- container 背景 `gray-50` / dark `gray-900`
- 默认 region `fill-gray-300` hover `brand-500`
- tip `bg-brand-500`；内置 zoom 按钮 `hidden`

scoped 选择器：`#mapTrafficAnalytics`、`#mapCustomerPinPoint` 见 `usStateHeatmapFills`。

## Data States

| 状态 | 模式 |
|---|---|
| loading | 地图区 `Skeleton` `h-[274px]` + `aria-busy="true"` |
| error | `Alert variant="error"` 替换地图区 |
| empty | 居中文案 + outline Button 重试 |

## 工程约束

- geodata 按需引入（`worldMill` / `usAea`），避免打包全部地图
- `zoomOnScroll: false` 防止页面滚动冲突
- `mapRef` + `setScale` 实现自定义 zoom；步进 `1.5`
- 与 `maps-theme.md`（栅格地图）职责分离；本 shard 专用于 SVG 矢量区域图

## 与 third-party-template 关系

`third-party-template.md#vector-maps` 保留简要入口；本 shard 为 Vector Map 深化参考。
