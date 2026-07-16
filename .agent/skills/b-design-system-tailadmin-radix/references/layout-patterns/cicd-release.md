# 布局模式 — CI/CD 流水线与发布

适用：流水线列表、构建详情、发布审批、灰度发布、回滚。

## 页面类型

| 页面 | 模式 | 说明 |
|---|---|---|
| Pipeline List | Table List | 仓库、分支、状态、触发人、耗时 |
| Pipeline Detail | Detail Page | stage bar + logs + artifacts |
| Release Flow | Form Flow + Timeline | 环境、版本、策略、审批 |
| Environment Detail | Dashboard + Table | 服务版本、实例、最近部署 |

## Pipeline Detail 结构

```tsx
<AppLayout>
  <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
    <div className="flex flex-col gap-6 xl:col-span-2">
      <ComponentCard title="Pipeline stages">{/* PipelineStageBar */}</ComponentCard>
      <ComponentCard title="Build logs">{/* LogStreamPanel */}</ComponentCard>
      <ComponentCard title="Artifacts">{/* Table */}</ComponentCard>
    </div>
    <div className="flex flex-col gap-6">
      <ComponentCard title="Run details">{/* dl */}</ComponentCard>
      <ComponentCard title="Actions">{/* retry/cancel/rollback */}</ComponentCard>
    </div>
  </div>
</AppLayout>
```

## 场景组件

| 组件 | 用途 | 状态 | 模板 |
|---|---|---|---|
| PipelineStageBar | checkout/test/build/deploy | queued/running/success/failed/skipped/canceled | `templates/devops/pipeline-stage-bar.tsx` |
| LogStreamPanel | 构建日志 | live/paused/search/filter severity | `templates/devops/log-stream-panel.tsx` |
| ArtifactTable | 镜像、包、报告 | available/expired/downloading | `templates/devops/artifact-table.tsx` |
| ApprovalTimeline | 发布与审批历史 | pending/approved/rejected | `templates/devops/approval-timeline.tsx` |
| CicdRunDetail | 页面组合 | stage bar + logs + artifacts + sidebar | `templates/devops/cicd-run-detail.tsx` |
| DangerZone | 危险操作区 | destructive + name confirm | `templates/devops/danger-zone.tsx` |
| RollbackDialog | 回滚确认 | destructive + target version | `templates/devops/danger-zone.tsx` |
| EnvironmentSelector | dev/staging/prod | disabled when locked | — |

## 发布表单

- 版本：Select 或 Combobox
- 环境：RadioGroup 或 Select
- 策略：全量/金丝雀/蓝绿
- 窗口：DatePicker + time input
- 审批人：MultiSelect
- 风险说明：Textarea，生产发布必填

## 危险操作

- Cancel running job：确认 Dialog + job id
- Rollback：必须显示当前版本、目标版本、影响环境
- Force deploy：需要权限提示和审计理由

## 视觉验收

- stage bar 不得因为长 stage name 挤压日志区。
- 日志用等宽字体和固定滚动容器。
- 右侧详情栏不得把主日志区压到不可读。
