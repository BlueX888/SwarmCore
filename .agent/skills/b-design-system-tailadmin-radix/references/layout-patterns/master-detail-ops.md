# 布局模式 — Master-Detail Ops

典型路由：`/alerts`、`/endpoints`、`/pipelines/:id`、`/resources/mysql`

关联：`table-list.md`、`detail-page.md`、`content-state-contract.md`、`templates/layout/master-detail-ops.tsx`

## 适用场景

- 告警/事件列表 + 右侧详情
- API Endpoint 列表 + 探测详情
- CI/CD 构建列表 + 日志/阶段详情
- PaaS 资源列表 + Metrics/Events/Logs tabs

## 结构（高度链）

```tsx
<AppLayout mainClassName="flex flex-col min-h-[calc(100vh-64px)]">
  <div className="flex min-h-0 flex-1 flex-col gap-4 xl:flex-row">
  {/* Master — 列表 */}
  <aside className="flex w-full shrink-0 flex-col xl:w-[360px] xl:max-w-[40%]">
    <DataTableCard compact … />
  </aside>
  {/* Detail — 详情 */}
  <section className="flex min-h-0 min-w-0 flex-1 flex-col">
    <MasterDetailOps detailTabs={…} activeDetailTab={…}>
      <QueryShell status={detailStatus}>…</QueryShell>
    </MasterDetailOps>
  </section>
  </div>
</AppLayout>
```

## 高度链要点

- 外层 `min-h-0` + `flex-1` 传递，避免 flex 子项撑破视口
- 列表区 `overflow-y-auto custom-scrollbar`
- 详情区 tab 内容 `flex-1 overflow-auto`
- 宽表 `overflow-x-auto`，表头 sticky

## Master 列表

- 行选中：`bg-brand-50 border-l-2 border-brand-500`
- 键盘：`↑↓` 切换选中，`Enter` 打开详情
- 空列表：左侧 empty，右侧 placeholder「Select an item」
- 加载：列表 Skeleton 行，保留表头

## Detail 多 Tab

| Tab | 内容 | 滚动 |
|---|---|---|
| Overview | KPI + 元信息 | 纵向 |
| Events | Timeline | 纵向 |
| Logs | LogStreamPanel | 独立滚动容器 mono |
| Config | YAML/Code | 横向+纵向 |

## 宽表横滚

```tsx
<div className="overflow-x-auto custom-scrollbar">
  <table className="min-w-[720px] w-full">…</table>
</div>
```

## 响应式

- `< xl`：master 全宽在上，detail 折叠为 Sheet 或下方 stack
- 选中项 mobile 用 `Sheet` 展示详情，保留返回列表

## 状态矩阵

| Master | Detail | UI |
|---|---|---|
| loading | — | 左 Skeleton，右 loading |
| empty | — | 左 empty，右引导 |
| success | loading | 左列表，右 detail spinner |
| success | error | 左列表保持，右 ErrorState + retry |

## 截图验收

- desktop：左右分栏比例约 35/65，主表全宽无窄列空白
- detail tab 打开态截图
- 日志/宽表区域有稳定滚动条，文本不重叠
