# 布局模式 — 运维监控 / 告警中心

适用：NOC 大盘、服务健康、主机/Pod 监控、告警列表、事件响应。

## 页面结构

```tsx
<AppLayout>
  <div className="flex flex-col gap-6">
    <PageHeader title="Operations Overview" actions={<Button>Mute alerts</Button>} />
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard label="Healthy services" />
      <MetricCard label="Critical alerts" />
      <MetricCard label="P95 latency" />
      <MetricCard label="Error rate" />
    </div>
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <ComponentCard className="xl:col-span-2" title="Traffic and errors">{/* chart */}</ComponentCard>
      <ComponentCard title="Alert severity">{/* severity stack */}</ComponentCard>
    </div>
    <ComponentCard title="Active incidents">{/* table + filters */}</ComponentCard>
  </div>
</AppLayout>
```

## 核心组件

| 区域 | 组件 | 状态 |
|---|---|---|
| 健康指标 | MetricCard + Badge | healthy/degraded/down/unknown |
| 趋势图 | Chart wrapper | loading/empty/error |
| 告警列表 | Table + FilterDrawer | acknowledged/muted/escalated |
| 事件详情 | Detail Page + Timeline | investigating/resolved |
| 日志预览 | LogStreamPanel | streaming/paused/error |

## 告警表格列

- Severity：Badge `error/warning/info`
- Resource：服务名 + 环境 + namespace
- Message：单行截断 + tooltip
- Started：相对时间
- Owner：Avatar + team
- Status：open/ack/resolved
- Actions：Acknowledge、Silence、Open runbook

## 交互规则

- Critical 告警不隐藏，只允许 mute/silence，并记录操作者。
- 点击告警行进入详情，详情包含 metric snapshot、events、logs、runbook。
- FilterDrawer 支持 severity、service、environment、owner、time range。
- 自动刷新要有暂停开关，避免用户阅读日志时跳动。

## 视觉验收

- 1440px 下 KPI 四列必须完整显示，数字不裁切。
- 告警表格占满主内容宽度，不出现窄列大空白。
- 日志区域固定高度滚动，不撑破页面。
