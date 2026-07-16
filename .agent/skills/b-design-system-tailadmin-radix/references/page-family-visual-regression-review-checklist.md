# Page Family Visual Regression 评审清单

> DOCS-041 / G90 产物。对 Agent 生成或人工改写的 **TailAdmin 页面族布局** 执行**可复现视觉回归抽检**，覆盖内容宽度利用率、framing 对齐、文本裁切、视口响应与主题对比度，并与 `responsive-review-checklist.md`（RESP-01～05）、`ui-drift-review-checklist.md`（REV-01～05）、`visual-token-review-checklist.md`（VIS-01～05）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前页面族视觉抽检 | 对应 PFVR 块 + `quality-rubric.md` 综合美学 |
| Dashboard/AI/Auth 等页面族 tab 矩阵抽检 | PFVR-01～05 各抽 1 族 |
| 首屏大面积空白或窄列 | PFVR-01 + `page-family-visual-regression-gates.png` |
| 内容压入侧栏或 framing 错位 | PFVR-02 + `decision-matrix.md` G90 选型表 |
| KPI/表格文本裁切或溢出 | PFVR-03 + `preview-qa.md` 截图红线 |
| desktop/tablet/mobile 比例失衡 | PFVR-04 + `responsive-review-checklist.md` |
| light/dark 对比度不足 | PFVR-05 + `visual-token-review-checklist.md` |

## 通用前置

1. 先完成 `ui-drift-review-checklist.md` REV-01～02（golden 对照与 framing）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/page-family-visual-regression-gates.png` 与 `verifyPageFamilyTabs` 矩阵截图。
3. 抽检视口 **desktop 1440×1000**、**tablet 1024×768**、**mobile 390×844** 各至少 1 次。
4. 场景级 7 大页面族抽检见 `scene-page-family-visual-regression-review-checklist.md` PFVR-06～10。
5. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。
6. 检索路径见 `agent-retrieval-guide.md` 页面族视觉回归抽检行。

## PFVR-01 — 内容宽度利用率

**对照 reference**：`page-family-visual-regression-gates.png`、`dashboard-family-layout`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 宽度占比 | 主内容区宽度利用率 ≥ 80%，无右侧大面积无意义空白 | PFVR-01 · RESP-01 |
| 2 | 栅格展开 | KPI 卡片、表格、图表按容器宽度响应式展开 | PFVR-01 · VIS-02 |
| 3 | 首屏密度 | 首屏主任务信息可见，不堆在窄列中央 | PFVR-01 · REV-03 |
| 4 | data-state | `data-audit="pfvr-width"` `data-state` 反映当前利用率档位 | PFVR-01 · COV-05 |
| 5 | example runtime | `verifyPageFamilyVisualRegressionGates` width gate 全过 | PFVR-01 · PREVIEW-* |

**交互动作**：打开 Dashboard Families → 切换 desktop/tablet/mobile → 确认宽度利用率 ≥ 80% → 对照 runtime `widthUtilization: true`。

## PFVR-02 — Framing 与侧栏边界

**对照 golden**：`layout-variants-mobile-layer.png`、`pfvr-framing` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 内容边界 | 主内容左边界不压入侧栏区域 | PFVR-02 · REV-02 |
| 2 | 顶栏对齐 | 顶栏、内容区、页头标题 framing 一致 | PFVR-02 · VIS-03 |
| 3 | active tab | 页面族 tab 切换后内容仍在主容器内 | PFVR-02 · PAT-03 |
| 4 | data-state | `data-audit="pfvr-framing"` `data-state=aligned` | PFVR-02 · COV-05 |
| 5 | example runtime | framing gate 切换 misaligned 可复现并恢复 | PFVR-02 · PREVIEW-* |

**交互动作**：点击 framing 门禁「模拟错位」→ 确认 `data-state=misaligned` → 点击「恢复对齐」。

## PFVR-03 — 文本裁切与溢出

**对照 reference**：`preview-qa.md` 截图红线、`pfvr-clipping` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 标题完整 | h1/h2/KPI 数值不被裁切或遮挡 | PFVR-03 · COPY-03 |
| 2 | 表格单元格 | 长文本 ellipsis 或换行，不重叠相邻列 | PFVR-03 · VIS-04 |
| 3 | 按钮标签 | 按钮、标签、导航文本不溢出容器 | PFVR-03 · REV-04 |
| 4 | data-state | `data-audit="pfvr-clipping"` `data-state=pass` | PFVR-03 · COV-05 |
| 5 | example runtime | clipping gate 模拟 fail 后可恢复 pass | PFVR-03 · PREVIEW-* |

**交互动作**：点击裁切门禁「模拟裁切」→ `data-state=fail` → 点击「恢复通过」。

## PFVR-04 — 视口响应式矩阵

**对照 golden**：`verifyPageFamilyTabs` 42 子页截图、`pfvr-viewport` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 三视口 | desktop/tablet/mobile 均可切换并更新布局态 | PFVR-04 · RESP-02 |
| 2 | 移动首屏 | mobile 主任务内容在首屏可见 | PFVR-04 · RESP-03 |
| 3 | 平板栅格 | tablet KPI 至少 2 列，不全堆叠为 1 列 | PFVR-04 · RESP-04 |
| 4 | data-state | `data-audit="pfvr-viewport"` 跟随当前视口 | PFVR-04 · COV-05 |
| 5 | example runtime | 三视口切换后 runtime 全过 | PFVR-04 · PREVIEW-* |

**交互动作**：依次点击「桌面」「平板」「移动」→ 确认 `data-state` 与布局预览同步。

## PFVR-05 — 主题对比度与层级

**对照 reference**：`visual-token-review-checklist.md`、`pfvr-theme` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light/dark | 两主题下边框、背景、文字层级可辨认 | PFVR-05 · VIS-05 |
| 2 | 控件对比 | 主按钮、表格斑马纹、卡片阴影在两主题下可读 | PFVR-05 · A11Y-02 |
| 3 | 图表可读 | runtime 图表 grid/legend 在 dark 下不丢失 | PFVR-05 · VIS-01 |
| 4 | data-state | `data-audit="pfvr-theme"` 跟随 light/dark | PFVR-05 · COV-05 |
| 5 | example runtime | 主题切换后 `page-family-visual-regression-gates.png` 可复现 | PFVR-05 · PREVIEW-* |

**交互动作**：切换 light/dark → 确认边框与文字对比度 → 对照 runtime `themeContrast: true`。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | PFVR-01～05 |
| 场景/页面族级 | `scene-page-family-visual-regression-review-checklist.md` | PFVR-06～10 |

## 交叉引用

- `scene-page-family-visual-regression-review-checklist.md` — PFVR-06～10
- `responsive-review-checklist.md` — RESP-01～05
- `ui-drift-review-checklist.md` — REV-01～05
- `decision-matrix.md` — G90 页面族视觉回归选型表
- `upgrade-troubleshooting.md` — PFVR-01～10 症状路由
- `agent-retrieval-guide.md` — 页面族视觉回归检索路径
- `quality-rubric.md` — 综合美学维度
