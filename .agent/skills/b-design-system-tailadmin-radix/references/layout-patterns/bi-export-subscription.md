# 布局模式 — BI 报表、导出与订阅

典型路由：`/bi/dashboards/:id/export`、`/bi/reports/subscriptions`

关联：`bi-drill-down.md`、`bi-dashboard-builder.md`、`bi-data-screen.md`、`templates/bi/export-menu.tsx`、`templates/bi/export-job-panel.tsx`、`templates/bi/export-subscription-dashboard.tsx`

## 适用场景

- **即时导出**：图表卡片、仪表盘、明细表导出 PNG/PDF/Excel/CSV
- **异步导出任务**：大数据量、跨多图表、服务端渲染 PDF
- **定时订阅**：邮件推送报表、仪表盘快照、失败重试与过期
- **大屏截图**：固定画布尺寸 + 主题记录，供运维/监控大屏归档

## 导出格式矩阵

| 格式 | 适用上下文 | 说明 |
|---|---|---|
| PNG | chart、dashboard、data-screen | 单图或整页截图；大屏必须记录画布尺寸 |
| PDF | dashboard、report | 多页排版；queued 优先 |
| Excel | table、detail | 明细表、透视结果 |
| CSV | table、detail | 轻量明细；DrillDetailTable 默认 |

## ExportMenu 能力

| 能力 | 说明 |
|---|---|
| 格式菜单 | PNG / PDF / Excel / CSV，按 context 过滤可用项 |
| 大屏选项 | `dataScreenSize`（如 1920×1080）、`theme`（light/dark/current） |
| 触发态 | idle / exporting 禁用重复提交 |
| 位置 | ChartPanel actions、Dashboard 顶栏、DrillDetailTable toolbar |

```tsx
<ExportMenu
  context="data-screen"
  dataScreenSize="1920×1080"
  theme="dark"
  formats={["png", "pdf"]}
  onExport={(format) => enqueueExport(format)}
/>
```

## Export Job 状态机

| 状态 | UI | 用户动作 |
|---|---|---|
| `queued` | 排队中 badge + 预计等待 | 可取消 |
| `exporting` | 进度条 / spinner + 百分比 | 不可重复提交 |
| `ready` | 下载就绪 + 文件大小 | 下载、复制链接 |
| `failed` | 错误摘要 + 重试 | 重试、查看日志 |
| `expired` | 链接已过期 | 重新导出 |

**过期规则**：ready 状态默认 24h 有效；`expiresAt` 展示相对时间。

## 订阅能力

| 字段 | 说明 |
|---|---|
| 频率 | 每日 / 每周 / 每月 |
| 收件人 | 邮箱列表，支持团队组 |
| 格式 | PDF / Excel / PNG 快照 |
| 范围 | 当前仪表盘 / 单图表 / 大屏画布 |
| 状态 | active / paused / failed |

## 结构

```tsx
<ExportSubscriptionDashboard
  title="经营分析"
  exportContext="dashboard"
  jobs={exportJobs}
  subscriptions={subscriptions}
  onExport={handleExport}
  onDownloadJob={handleDownload}
  onRetryJob={handleRetry}
  onCancelJob={handleCancel}
  renderMain={() => <DashboardGrid … />}
/>
```

或组合式：

```tsx
<ChartPanel
  title="各区域收入"
  actions={<ExportMenu context="chart" onExport={…} />}
/>
<ExportJobPanel jobs={jobs} onDownload={…} onRetry={…} />
```

## 与 DrillDetailTable 分工

- `DrillDetailTable`：行内 CSV 快捷导出 + `exportStatus` 单行态
- `ExportMenu` + `ExportJobPanel`：多格式、异步任务、订阅、大屏截图

## 视觉规则

- ExportMenu 使用 `outline` 按钮 + `▾`，菜单项左侧格式图标
- Job 列表：`ready` 用 `success` badge，`failed` 用 `error`，`expired` 用 `muted`
- 进度条高度 4px，`brand-500` 填充
- 订阅卡片：频率 + 下次发送时间 + 暂停/编辑
- 大屏导出选项区：`画布 1920×1080 · 深色主题` 一行摘要

## 反例

- 大数据导出不要用同步前端下载冒充 ready
- 不要把订阅配置塞进普通 FormDialog 无 cron 说明
- 大屏 PNG 导出不得丢失画布比例与主题标记
- 不要用英文 placeholder 作为默认导出文件名

## Agent 检索

- 组件索引 → `ExportMenu` / `ExportJobPanel` / `ExportSubscriptionDashboard`
- 选型矩阵 → BI 导出 vs DrillDetailTable 单行导出
- preview → `#bi-export-subscription`
