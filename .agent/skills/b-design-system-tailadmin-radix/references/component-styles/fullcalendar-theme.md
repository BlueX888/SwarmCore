# FullCalendar 主题 — 日程页

独立 FullCalendar 主题 shard。源：`pages/Calendar.tsx`、`index.css` `.fc-*` / `.event-fc-color`。

可复制模板：`templates/lib/fullcalendar-theme.ts`

## 检索别名

| 意图 | 读本节 |
|---|---|
| 日程页布局 | `#calendar-container` |
| Toolbar / 视图切换 | `#toolbar` |
| 事件色 | `#event-colors` |
| 今日高亮 | `#today` |
| TimeGrid 样式 | `#timegrid` |
| 暗色 CSS | `#dark-mode-css` |
| 加载/空态 | `#data-states` |
| 编辑事件 Dialog | `#event-dialog` |

## Calendar Container

日程页路由：`/calendar`（见 `route-index.md`）。

```tsx
<div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
  <div className="custom-calendar">
    <FullCalendar
      plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
      {...getDefaultFullCalendarOptions()}
      events={events}
      eventContent={renderEventContent}
      customButtons={{
        addEventButton: {
          text: "Add Event +",
          click: openCreateDialog,
        },
      }}
    />
  </div>
</div>
```

- 外包 `rounded-2xl border-gray-200` 卡壳（非 `min-h-screen` 全屏 demo）
- 内层 `.custom-calendar` 触发 scoped CSS
- 横向滚动：`fc-view-harness` + `min-w-[718px]` 月视图

## Toolbar

源默认 header：

| 区域 | 内容 |
|---|---|
| left | prev, next, addEventButton |
| center | title（`text-lg font-medium text-gray-800`） |
| right | dayGridMonth, timeGridWeek, timeGridDay |

视觉规则：

- prev/next：`h-10 w-10 rounded-lg border-gray-200`；隐藏默认 `.fc-icon`，用 SVG data-url
- Add Event：`bg-brand-500 hover:bg-brand-600 rounded-lg px-4 py-2.5 text-sm`
- 视图切换 pill：`rounded-lg bg-gray-100 p-0.5`；active → `bg-white dark:bg-gray-800`

```ts
import {
  defaultHeaderToolbar,
  getDefaultFullCalendarOptions,
} from "@/lib/fullcalendar-theme";
```

## Event Colors

`extendedProps.calendar` 映射四级语义色：

| Level | 背景 | Dot |
|---|---|---|
| Primary | `bg-brand-50 border-brand-50` | `bg-brand-500` |
| Success | `bg-success-50` | `bg-success-500` |
| Danger | `bg-error-50` | `bg-error-500` |
| Warning | `bg-orange-50` | `bg-orange-500` |

```tsx
import { getEventContentClassName, type EventLevel } from "@/lib/fullcalendar-theme";

const renderEventContent = (eventInfo: EventContentArg) => {
  const level = (eventInfo.event.extendedProps?.calendar as EventLevel) ?? "Primary";
  const colorClass = getEventContentClassName(level);

  return (
    <div className={colorClass}>
      <div className="fc-daygrid-event-dot" />
      <div className="fc-event-time">{eventInfo.timeText}</div>
      <div className="fc-event-title">{eventInfo.event.title}</div>
    </div>
  );
};
```

- 事件 pill：`rounded-lg py-2.5 pl-4 pr-3`
- 左侧 dot：`w-1 h-5 rounded-sm`（非 FullCalendar 默认圆点）
- 标题：`text-sm font-normal text-gray-700`

## Today

- 单元格本身 `bg-transparent`
- 内层 sync-inner：`rounded-sm bg-gray-100 dark:bg-white/[0.03]`
- 日期数字：`text-sm font-medium text-gray-700 dark:text-gray-400`
- 非当月：`text-gray-400 dark:text-white/30`

## TimeGrid

- slot label：`text-sm font-medium text-gray-500 px-3 py-1.5`
- axis cushion：同上
- 水平事件：`.custom-calendar .fc-h-event` → `background transparent; border none`

## Dark Mode CSS

复制 `templates/lib/fullcalendar-theme.ts` 中 `fullCalendarCssOverrides` 到宿主 `src/index.css`。

关键覆盖：

- toolbar title：`dark:text-white/90`
- grid border：`dark:border-gray-800`
- header cell：`dark:bg-gray-900`
- prev/next SVG：dark stroke `#98A2B3`

源证据：TailAdmin React Pro v2.3.1 `index.css` L601–733（已内化至 `fullcalendar-theme.ts` 与 example runtime）。

## Data States

| 状态 | 模式 | 实现 |
|---|---|---|
| loading | 事件请求中 | `Skeleton` 覆盖 `.custom-calendar` 区 `min-h-[400px]` + `aria-busy="true"` |
| empty | 无事件 | 保留 grid；可选 Card 内居中 `text-gray-500` + outline Button 创建 |
| error | 加载失败 | `Alert variant="error"` 替换 calendar 区，保留卡壳 |

禁止用装饰动画掩盖空日程；业务密度优先。

## Event Dialog

编辑/创建事件使用 shadcn `Dialog`（非源项目手写 Modal）：

- 标题：`text-theme-xl font-semibold text-gray-800`
- 字段：`h-11 rounded-lg border-gray-300 shadow-theme-xs`
- 色级 radio：源项目 Danger/Success/Primary/Warning 四级
- 主操作：`bg-brand-500 hover:bg-brand-600`
- 取消：outline `border-gray-300`

`select` 拖拽选日期 → 打开 Dialog 预填 start/end。

## 工程约束

- 保留 `@fullcalendar/react` v6 + dayGrid/timeGrid/interaction plugins
- 禁止替换为 react-big-calendar 或纯 CSS grid 重写
- CSS 使用 TailAdmin 语义 Token（`brand-*`、`success-*`、`error-*`、`orange-*`）
- 与 `templates/ui/calendar.tsx`（react-day-picker DatePicker）职责分离：DatePicker 用于表单日期；FullCalendar 用于日程页

## 与 third-party-template 关系

`third-party-template.md#calendar` 保留简要入口；本 shard 为 FullCalendar 深化参考。Agent 任务涉及 `/calendar` 日程页时优先读本文件。
