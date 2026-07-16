# 布局模式 — Detail Page

典型路由：`/inbox-details`、`/billing`、`/single-invoice`、`/chat`

## 结构（主从）

```tsx
<AppLayout>
  <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
    {/* Main */}
    <div className="flex flex-col gap-6 xl:col-span-2">
      <ComponentCard>{/* Primary content */}</ComponentCard>
      <ComponentCard title="Activity">{/* Timeline / replies */}</ComponentCard>
    </div>
    {/* Sidebar meta */}
    <div className="flex flex-col gap-6">
      <ComponentCard title="Details">
        <dl className="grid gap-3 text-theme-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">Status</dt>
            <dd><Badge>Active</Badge></dd>
          </div>
        </dl>
      </ComponentCard>
      <ComponentCard title="Actions">
        <div className="flex flex-col gap-2">
          <Button variant="primary">Approve</Button>
          <Button variant="outline">Archive</Button>
        </div>
      </ComponentCard>
    </div>
  </div>
</AppLayout>
```

## 页头

- 面包屑 + 标题 + 状态 Badge
- 右侧 actions：outline 次要 + primary 主操作

## AI 布局（AlternativeLayout）

**源**：`layout/AlternativeLayout.tsx`

- 无 `max-w-(--breakpoint-2xl)` 限制
- 全高 split：侧栏历史 + 主生成区 + 顶栏 `GeneratorTopbar`

## 聊天/工单

- 消息列表 `custom-scrollbar` + 固定底部输入区
- 回复区 `border-t` + Textarea + Button
