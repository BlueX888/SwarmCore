# 布局模式 — Hub Tabs

典型路由：`/settings?tab=general`、`/gateway?tab=endpoints`、`/tenant?tab=quota`

关联：`form-flow.md`、`master-detail-ops.md`、`templates/layout/hub-tabs-layout.tsx`

## 适用场景

- 设置中心（General / Security / Notifications / Billing）
- 控制平面 Hub（Overview / Endpoints / Keys / Quota / Usage）
- 资源详情多面板（Metrics / Events / Logs / Config）

## 结构

```tsx
<AppLayout>
  <PageHeader title="Gateway Settings" breadcrumbs={…} />
  <HubTabsLayout
    tabs={[
      { id: "general", label: "General", href: "?tab=general" },
      { id: "quota", label: "Quota", href: "?tab=quota" },
      { id: "usage", label: "Usage", href: "?tab=usage" },
    ]}
    activeTab={searchParams.get("tab") ?? "general"}
    onTabChange={(id) => setSearchParams({ tab: id })}
  >
    <QueryShell status={status} …>{/* tab panel */}</QueryShell>
  </HubTabsLayout>
</AppLayout>
```

## URL 同步规则

- 默认 tab 写入 URL：`?tab=general`（可省略 default 时仍支持深链）
- 浏览器前进/后退必须恢复 tab 与滚动位置
- 非法 `tab` 值回退 default + `replace`（避免脏历史）
- 子路由 tab 内嵌套筛选：`?tab=usage&range=7d`

## Tab 状态

| 状态 | 表现 | 组件 |
|---|---|---|
| loading | tab 条可点，内容区 Spinner | `QueryShell` + `Spinner` |
| empty | 居中文案 + CTA | `ContentState` |
| error | Alert + Retry | `ErrorState` |
| disabled | tab `aria-disabled` + tooltip | `TabsTrigger` |

## 视觉规则

- Tab 条 `border-b` + active `border-brand-500` 下划线
- 内容区 `min-h-[320px]`，禁止 tab 切换时高度塌陷
- 宽表单 tab 使用 `max-w-3xl` 左对齐，数据 tab 全宽
- mobile：`tabs` 横向滚动 `overflow-x-auto`，不折行标签

## 页头组合

```tsx
<div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
  <div>
    <Breadcrumb … />
    <h1 className="text-title-md font-semibold text-gray-900 dark:text-white/90">…</h1>
    <p className="text-theme-sm text-gray-500">…</p>
  </div>
  <div className="flex gap-2">{/* Save / Test connection */}</div>
</div>
```

## 危险操作

- 切换 tab 前有未保存更改 → `Dialog` 确认
- Quota / Billing tab 的 destructive 操作带对象名

## 截图验收

- desktop 1440px：tab 内容区占满 `max-w-(--breakpoint-2xl)` 宽度
- 空态/错态 tab 不得出现右侧大面积空白
- active tab 下划线与文字对齐，不可裁切
