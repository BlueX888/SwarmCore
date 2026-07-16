# S03-D03 流水线运行详情

## 复制入口

```tsx
import { PipelineRunDetailPage } from "@/templates/scenarios/devops/pipeline-run-detail-page";
```

## 组件组合

- `PipelineStageBar` — 可点击阶段条，切换日志上下文
- `LogStreamPanel` — 阶段日志流（暂停/搜索/自动滚动）
- `ArtifactTable` — 制品下载与扫描报告
- `ApprovalTimeline` — 发布审批记录
- `RollbackDialog` — 危险回滚确认（需输入运行号）

## PRD

`docs/spec/b-design-system-tailadmin-radix/prd/scenarios/S03-devops.md#s03-d03`

## Example 路由

`showcase-scenario-pipeline-run-detail`
