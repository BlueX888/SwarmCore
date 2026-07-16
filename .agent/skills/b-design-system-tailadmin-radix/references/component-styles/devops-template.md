# DevOps / 代码平台组件模板

技术栈：**React + shadcn/ui + Radix + Tailwind v4**

## 读取顺序

1. `references/layout-patterns/cicd-release.md` — CI/CD 页面结构
2. `references/layout-patterns/code-repository.md` — 代码仓库 / MR 结构
3. 本文件选可复制模板
4. `templates/devops/cicd-run-detail.tsx` — 页面级组合入口

## CI/CD 场景组件

| 组件 | 状态覆盖 | 模板 |
|---|---|---|
| PipelineStageBar | queued/running/success/failed/skipped/canceled | `templates/devops/pipeline-stage-bar.tsx` |
| LogStreamPanel | live/paused/search/severity filter | `templates/devops/log-stream-panel.tsx` |
| ArtifactTable | available/expired/scanning/failed + download | `templates/devops/artifact-table.tsx` |
| ApprovalTimeline | pending/approved/rejected | `templates/devops/approval-timeline.tsx`（底层包装通用 `Timeline`） |
| DangerZone | destructive + name confirm | `templates/devops/danger-zone.tsx` |
| RollbackDialog | version confirm + environment impact | `templates/devops/danger-zone.tsx#RollbackDialog` |
| CicdRunDetail | 2/3 + 1/3 页面组合 | `templates/devops/cicd-run-detail.tsx` |

## 代码仓库场景组件

| 组件 | 状态覆盖 | 模板 |
|---|---|---|
| FileTree | selected/loading/empty | `templates/devops/file-browser.tsx#FileTree` |
| CodeViewer | ready/loading/error/binary/large | `templates/devops/file-browser.tsx#CodeViewer` |
| FileBrowser | tree + viewer split 240px+1fr | `templates/devops/file-browser.tsx` |
| DiffViewer | added/removed/changed + collapse + large fallback | `templates/devops/diff-viewer.tsx` |
| MrDetailShell | Overview/Commits/Changes/Checks + sidebar | `templates/devops/mr-detail-shell.tsx` |

## 视觉验收

- Pipeline stage bar：长 stage name 用 `truncate`，不得挤压日志区。
- LogStreamPanel：固定高度默认 `180px`，等宽字体，暗色底。
- FileBrowser：树 `240px` + 代码 `1fr`，不得互相挤压。
- DiffViewer：行号列固定宽度，大文件显示降级面板。
- MR shell：分支名 `font-mono`，长标题 `min-w-0` + truncate。

## 组合示例

```tsx
import { CicdRunDetail } from "@/components/devops/cicd-run-detail";
import { MrDetailShell } from "@/components/devops/mr-detail-shell";
import { FileBrowser } from "@/components/devops/file-browser";
```
