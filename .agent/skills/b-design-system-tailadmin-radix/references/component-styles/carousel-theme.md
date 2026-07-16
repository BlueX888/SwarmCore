# Carousel 主题 — Swiper

独立 Carousel 主题 shard。源：`components/ui/carousel/*`、`pages/UiElements/Carousel.tsx`。

**库**：`swiper/react` + `swiper/modules`。

可复制模板：`templates/lib/carousel-theme.ts`

## 检索别名

| 意图 | 读本节 |
|---|---|
| 页面布局 | `#page-layout` |
| Slides Only | `#slide-only` |
| With Controls | `#with-controls` |
| With Indicators | `#with-indicators` |
| Controls + Indicators | `#controls-and-indicators` |
| Stocks 外置导航 | `#stocks-slider` |
| CSS 覆盖 | `#css-overrides` |
| 加载/空态 | `#data-states` |

## Page Layout

路由：`/carousel`（见 `route-index.md` UI Elements）。

```tsx
import { carouselPageGridClass } from "@/lib/carousel-theme";

<div className={carouselPageGridClass}>
  <ComponentCard title="Slides Only"><SlideOnly /></ComponentCard>
  <ComponentCard title="With controls"><WithControl /></ComponentCard>
  <ComponentCard title="With indicators"><WithIndicators /></ComponentCard>
  <ComponentCard title="With controls and indicators"><WithControlAndIndicators /></ComponentCard>
</div>
```

- 外包 `PageBreadcrumb pageTitle="Carousel"`
- 栅格：`grid-cols-1 gap-5 xl:grid-cols-2 xl:gap-6`

## Slide Only

```tsx
import { Swiper, SwiperSlide } from "swiper/react";
import { Autoplay } from "swiper/modules";
import { carouselShellClass, slideOnlySwiperOptions } from "@/lib/carousel-theme";

<div className={`${carouselShellClass} carouselOne`}>
  <Swiper modules={[Autoplay]} {...slideOnlySwiperOptions}>
    {slides.map((item, i) => (
      <SwiperSlide key={i}>
        <div className="overflow-hidden rounded-lg">
          <img src={item.thumbnail} className="rounded-lg" alt="" />
        </div>
      </SwiperSlide>
    ))}
  </Swiper>
</div>
```

## With Controls

```tsx
import { Navigation, Autoplay } from "swiper/modules";
import { withControlSwiperOptions, carouselNavPrevClass, carouselNavNextClass } from "@/lib/carousel-theme";

<div className={`relative ${carouselShellClass} carouselTwo`}>
  <Swiper modules={[Navigation, Autoplay]} {...withControlSwiperOptions}>
    {/* slides */}
  </Swiper>
  <div className={`swiper-button-prev prev-style-one ${carouselNavPrevClass}`}>{/* chevron svg */}</div>
  <div className={`swiper-button-next next-style-one ${carouselNavNextClass}`}>{/* chevron svg */}</div>
</div>
```

- 导航：`navigation.nextEl: ".next-style-one"` / `prevEl: ".prev-style-one"`
- 按钮：`h-10 w-10 rounded-full bg-white/90 backdrop-blur-[10px]`

## With Indicators

```tsx
import { Pagination, Autoplay } from "swiper/modules";
import { withIndicatorsSwiperOptions } from "@/lib/carousel-theme";

<div className={`relative ${carouselShellClass} carouselThree`}>
  <Swiper modules={[Pagination, Autoplay]} {...withIndicatorsSwiperOptions}>
    {/* slides */}
    <div className="swiper-pagination" />
  </Swiper>
</div>
```

- 分页 pill：`rounded-[40px] bg-white/60 backdrop-blur` bottom-center
- Active bullet 拉长：`w-6.5 rounded-xl`

## Controls and Indicators

- 合并 Navigation + Pagination；scoped `carouselFour`
- 导航选择器：`.prev-style-two` / `.next-style-two`

## Stocks Slider

业务场景（`TrendingStocks`）外置导航：

```tsx
import { stocksSliderNavClass } from "@/lib/carousel-theme";

<div className="stocks-slider-outer">
  <div className={`swiper-button-prev ${stocksSliderNavClass}`} />
  <div className={`swiper-button-next ${stocksSliderNavClass}`} />
  <Swiper modules={[Navigation]} ... />
</div>
```

- `!static` 导航；`h-8 w-9` 圆形边框按钮

## CSS Overrides

宿主 `index.css` 引入 `swiperCssOverrides`：

- 隐藏 `.swiper-button-next:after` / `:after` on carouselTwo/Four
- disabled 态 `bg-white/60 opacity-100`
- pagination bullet 白底 + active 拉长

## Data States

| 状态 | 模式 |
|---|---|
| loading | slide 区 `Skeleton` `aspect-video rounded-lg` |
| empty | 居中文案 + outline Button |
| error | `Alert variant="error"` 替换轮播区 |
| single slide | 隐藏导航与分页 |

## 工程约束

- 全局引入 `swiper/swiper-bundle.css`（`main.tsx`）
- 每个 variant 使用独立 scoped class（`carouselOne`–`carouselFour`）避免导航选择器冲突
- 图片 `alt` 必填；自动播放 respect `prefers-reduced-motion`

## 与 third-party-template 关系

`third-party-template.md#carousel` 保留简要入口；本 shard 为 Swiper 轮播深化参考。
