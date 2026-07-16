# Maps 主题 — 地图卡壳

独立 Maps 主题 shard。源：`components/maps/others/*`、`pages/Maps/Maps.tsx`。

可复制模板：`templates/lib/maps-theme.ts`

## 检索别名

| 意图 | 读本节 |
|---|---|
| 页面栅格 | `#page-layout` |
| MapLibre 卡 | `#maplibre` |
| iframe embed | `#iframe-embed` |
| Leaflet 卡 | `#leaflet` |
| Zoom 控件 | `#zoom-controls` |
| 自定义 marker | `#custom-markers` |
| 加载/错误 | `#data-states` |

## Page Layout

路由：`/maps`（见 `route-index.md` Charts & Maps）。

```tsx
import { mapsPageGridClass } from "@/lib/maps-theme";

<div className={mapsPageGridClass}>
  <MapLibreCard />
  <IframeMapCard />
  <LeafletMapCard />
</div>
```

- 页面栅格：`grid grid-cols-1 lg:grid-cols-2 gap-6`
- 第三张卡可 `lg:col-span-2` 或保持半宽（源项目为 2+1 布局）

## Map Card Shell

```tsx
import { mapCardShellClass, mapCardTitleClass, mapCardSubtitleClass } from "@/lib/maps-theme";

<div className={mapCardShellClass}>
  <div className="mb-5 flex items-start justify-between">
    <div>
      <h3 className={mapCardTitleClass}>Map View</h3>
      <p className={mapCardSubtitleClass}>Clear view of locations at a glance</p>
    </div>
  </div>
  <div className={mapContainerWrapperClass}>
    {/* map instance */}
  </div>
</div>
```

- 卡壳：`rounded-2xl border border-gray-200 bg-white p-5 sm:p-6 dark:border-gray-800 dark:bg-white/[0.03]`
- 地图容器外包：`relative z-0 overflow-hidden rounded-2xl border border-gray-200 dark:border-gray-800`
- 地图高度：`h-[300px] w-full`

## MapLibre

```ts
import { defaultMapLibreOptions } from "@/lib/maps-theme";
import maplibregl from "maplibre-gl";

const map = new maplibregl.Map({
  container: containerRef.current!,
  ...defaultMapLibreOptions,
});
```

- 默认 style：`https://tiles.openfreemap.org/styles/bright`
- `scrollZoom: false`、`attributionControl: false`
- cleanup：`map.remove()` on unmount

## iframe Embed

```tsx
import { iframeMapClass } from "@/lib/maps-theme";

<iframe
  src={embedUrl}
  className={iframeMapClass}
  allowFullScreen
  loading="lazy"
  referrerPolicy="no-referrer-when-downgrade"
  title="Location map"
/>
```

- `!w-full h-[300px] rounded-xl border border-gray-200 grayscale dark:border-gray-800`

## Leaflet

```ts
import L from "leaflet";
import { defaultLeafletTileUrl, defaultLeafletOptions } from "@/lib/maps-theme";

const map = L.map(containerRef.current!, defaultLeafletOptions);
L.tileLayer(defaultLeafletTileUrl).addTo(map);
```

- 自定义 marker：见 `templates/lib/maps-theme.ts` 中 `createLeafletDivIcon`
- marker 样式：圆形 `border-brand-200 bg-brand-50` + 底部 label pill

## Zoom Controls

```tsx
import { mapZoomControlWrapperClass, mapZoomButtonClass } from "@/lib/maps-theme";

<div className={mapZoomControlWrapperClass}>
  <button type="button" className={mapZoomButtonClass} aria-label="Zoom in">+</button>
  <button type="button" className={mapZoomButtonClass} aria-label="Zoom out">−</button>
</div>
```

- 定位：`absolute top-3 right-3 z-[999]`
- 按钮栈：`flex flex-col rounded-lg border bg-white dark:bg-gray-900`
- 单按钮：`h-9 w-9`；上按钮 `border-b`

## Data States

| 状态 | 模式 |
|---|---|
| loading | 地图区 `Skeleton h-[300px]` + `aria-busy="true"` |
| error | `Alert variant="error"` 替换地图区，保留卡壳标题 |
| empty | 居中 `text-gray-500` + outline Button 重试 |

## 工程约束

- MapLibre / Leaflet / iframe 三模式按场景选型，不统一替换
- Vector Maps（`@react-jvectormap` `/vector-map`）为独立路由，见 `vector-map-theme.md`
- 地图区必须 `role="application"` 或 iframe `title` 以满足 a11y

## 与 third-party-template 关系

`third-party-template.md#maps` 保留简要入口；本 shard 为 Maps 深化参考。
