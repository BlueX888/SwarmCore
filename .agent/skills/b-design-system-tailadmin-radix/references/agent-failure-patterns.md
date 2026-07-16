# Agent 失败案例库

> go.md Phase 6 产物。把 Cursor Agent 常见落地失败变成可检索、可测试、可修复的知识。可复现抽检见 `agent-failure-patterns-review-checklist.md`（FAIL-01～05）与 `scene-agent-failure-review-checklist.md`（FAIL-06～10）。

## 使用方式

1. 生成或改写页面后，按 ID 对照本表自检。
2. PR 前配合 `agent-failure-patterns-review-checklist.md` FAIL-01～05 与 `scene-agent-failure-review-checklist.md` FAIL-06～10 及 `npm run verify:runtime` 截图证据。
3. 发现新模式时写回 `decision-matrix.md` 反例规则，并在此表追加 FAIL-* 行。

## 失败模式索引

| ID | 失败模式 | 典型症状 | 检测方式 | 修复路径 |
|---|---|---|---|---|
| FAIL-01 | 主内容列过窄 | 首屏大面积空白、KPI 挤在窄列 | screenshot + bounding box；`verify-runtime-ui.mjs` 主内容区宽高 | `app-layout.tsx` + `max-w-(--breakpoint-2xl)`；REV-01 |
| FAIL-02 | 卡片套卡片导致营销页感 | 多层 Card 嵌套、hero 级标题 | DOM class / visual review；DRIFT-02 | `layout-patterns/*.md` 页面壳层；减少嵌套 Card |
| FAIL-03 | 表格移动端不可读 | 列被裁切、操作按钮不可点 | mobile screenshot；RESP-03 | 受控横向滚动 + sticky 操作列；`data-table-card.tsx` |
| FAIL-04 | dark 边界丢失 | 边框/分隔线与背景融合 | dark screenshot；VIS-02 | `gray-800`/`gray-700` 语义边框；`theme-context` |
| FAIL-05 | 手写 Modal / click outside | 无 focus trap、无 aria | import / source scan；A11Y-03 | `form-dialog.tsx` / Radix Dialog；禁止 div+fixed 自写 |
| FAIL-06 | Token 硬编码 hex | 页面散落 `#465fff` 等 | `rg "#[0-9a-fA-F]{6}"` src/；CON-01 | `token-index.md` + CSS 变量；chart-theme 仅 lib 层允许 palette |
| FAIL-07 | 英文 mock 泛滥 | placeholder/表头为英文 | 中文文案抽检；COPY-01 | `copy-preset.ts` + `chinese-copy-review-checklist.md` |
| FAIL-08 | 浮层打开态遮挡 | Dialog/Drawer 挡住主流程不可读 | Playwright open state；INTER-04 | z-index 分层 + 非 modal 用 Popover；example overlay sections |
| FAIL-09 | loading/empty/error 缺失 | 仅 happy path | data-state audit；ASYNC-01 | `query-shell.tsx` + `content-state` 模板；golden flow 边界态 |
| FAIL-10 | 只做静态截图不可交互 | 无 hover/click 证据 | runtime click audit；`verify:runtime` | `examples/b-design-system-tailadmin-radix` Specimen Lab |

## 自动化门禁映射

| 命令 | 覆盖 FAIL |
|---|---|
| `npm run audit -w examples/b-design-system-tailadmin-radix` | FAIL-09、FAIL-10（live specimen / runtime marker） |
| `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` | FAIL-01、FAIL-03、FAIL-08、FAIL-10 |
| `python3 create-design-system/scripts/run_token_hit_tests.py` | FAIL-06 |
| `references/chinese-copy-review-checklist.md` | FAIL-07 |

## 检索路径（≤3 跳）

| 任务 | 第 1 跳 | 第 2 跳 |
|---|---|---|
| 页面布局/宽度问题 | 本表 FAIL-01 | `ui-drift-review-checklist.md` REV-01 |
| 浮层/打开态问题 | 本表 FAIL-08 | `interaction-motion-review-checklist.md` |
| 状态矩阵缺失 | 本表 FAIL-09 | `state-index.md` → `query-shell.tsx` |
| 验收不可交互 | 本表 FAIL-10 | `examples/b-design-system-tailadmin-radix/README.md` |
