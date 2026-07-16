# 布局模式 — 自研代码仓库管理

适用：代码仓库、分支、提交、Merge Request / Pull Request、文件浏览、权限设置。

## 页面类型

| 页面 | 模式 | 核心组件 |
|---|---|---|
| Repository List | Table List | repo table + language/status badge |
| Repository Overview | Detail Page | README + activity + clone panel |
| File Browser | Tree Detail | file tree + code viewer |
| Merge Request Detail | Detail Page | diff viewer + review timeline |
| Branch / Tag List | Table List | protected badge + actions |
| Repository Settings | Form Flow | permissions + hooks + danger zone |

## 场景组件

| 组件 | 用途 | 状态 | 模板 |
|---|---|---|---|
| RepoTable | 仓库列表 | private/public/archived | — |
| FileTree | 目录浏览 | selected/loading/empty | `templates/devops/file-browser.tsx` |
| CodeViewer | 文件内容 | large file/error/binary | `templates/devops/file-browser.tsx` |
| FileBrowser | 树 + 代码 split | 240px + 1fr | `templates/devops/file-browser.tsx` |
| DiffViewer | MR/PR 变更 | added/removed/changed/collapse | `templates/devops/diff-viewer.tsx` |
| MrDetailShell | MR/PR 详情壳 | Overview/Commits/Changes/Checks | `templates/devops/mr-detail-shell.tsx` |
| ApprovalTimeline | 审查记录 | approved/rejected/pending | `templates/devops/approval-timeline.tsx` |
| BranchProtectionPanel | 分支保护 | inherited/custom/locked | — |
| ClonePanel | HTTPS/SSH clone | copied/error | — |

## MR/PR Detail

- Header：标题、状态 Badge、源/目标分支、作者、创建时间
- Tabs：Overview / Commits / Changes / Checks
- Sidebar：reviewers、labels、milestone、merge strategy
- Actions：Approve、Request changes、Merge、Close

## 视觉验收

- 文件树与代码区必须形成稳定 split，不得互相挤压。
- Diff 行号、代码列、评论气泡不能重叠。
- 长仓库名、分支名、commit sha 需要截断 + tooltip。
