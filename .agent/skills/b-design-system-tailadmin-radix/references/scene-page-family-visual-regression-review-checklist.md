# 场景 Page Family Visual Regression 评审清单

> DOCS-041 / G90 产物。对 Agent 生成或人工改写的 **7 大 TailAdmin 页面族与 42 子页矩阵** 执行**可复现场景级视觉回归抽检**，覆盖 Dashboard/AI/Auth/Ecommerce/Email/Workflow/Platform 页面族 tab 矩阵、Layout Variants 与 BI runtime 截图，并与 `page-family-visual-regression-review-checklist.md`（PFVR-01～05）、`scene-responsive-review-checklist.md`（RESP-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前页面族矩阵抽检 | 对应 PFVR 块 + `quality-rubric.md` |
| 7 大页面族 42 子页 tab 矩阵 | PFVR-06 + `verifyPageFamilyTabs` |
| Dashboard 10 套仪表盘 framing | PFVR-07 + `dashboard-family-*.png` |
| Layout Variants 移动层 framing | PFVR-08 + `layout-variants-mobile-layer.png` |
| BI Chart Builder 首屏宽度 | PFVR-09 + `bi-chart-builder-runtime.png` |
| 页面族视觉回归束缺门禁 | PFVR-10 + `verify:runtime` `pageFamilyVisualRegressionStates` |

## 通用前置

1. 先完成 `page-family-visual-regression-review-checklist.md` PFVR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/page-family-*.png` 与 `dashboard-family-*.png`。
3. 抽检至少 **Dashboard Families + 1 个非 Dashboard 页面族 + Layout Variants**。
4. 视口 **desktop 1440×1000** 与 **mobile 390×844** 各 1 次首屏宽度检查。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景页面族视觉回归（G90）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 页面族视觉回归抽检行。

## PFVR-06 — 42 子页 Tab 矩阵截图

**对照 golden**：`verifyPageFamilyTabs`、`pageFamilyTabChecks = 42`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tab 数量 | 7 族合计 42 个子页 tab 均可打开 | PFVR-06 · COV-06 |
| 2 | active 校验 | 每个 tab active 状态与 label 一致 | PFVR-06 · GEN-06 |
| 3 | 画布可见 | 切换后 `.dashboard-family-layout` 或等效画布可见 | PFVR-06 · REV-06 |
| 4 | 截图归档 | 每 tab 生成 `*-family-*.png` 或等效 element screenshot | PFVR-06 · PREVIEW-* |
| 5 | example runtime | `pageFamilyTabChecks >= 42` runtime 全过 | PFVR-06 · VAL-* |

**交互动作**：跑 `verify:runtime` → 确认 `pageFamilyTabChecks = 42` → 抽查 3 族各 1 tab 截图 framing。

## PFVR-07 — Dashboard Families 10 套仪表盘

**对照 golden**：`dashboard-family-analytics.png` 等 10 张、`tailadmin-dashboard-families`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立节奏 | 每套 dashboard 保留独立 KPI、图表、表格 widget | PFVR-07 · PAT-07 |
| 2 | 宽度利用 | 4 列 KPI 栅格在 desktop 展开，无窄列堆叠 | PFVR-07 · RESP-07 |
| 3 | runtime 图表 | 每族至少 1 个 ApexCharts runtime 画布 | PFVR-07 · COV-07 |
| 4 | 中文文案 | 指标、表格、按钮使用中文 mock | PFVR-07 · COPY-07 |
| 5 | example runtime | Dashboard Families 门禁 + 10 tab 截图全过 | PFVR-07 · PREVIEW-* |

**交互动作**：打开 Dashboard Families → 切换 Analytics/CRM/SaaS → 检查 KPI 栅格与图表 framing。

## PFVR-08 — Layout Variants 移动层 Framing

**对照 golden**：`layout-variants-mobile-layer.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 6 变体 | SidebarOne～Six + Header 变体可切换 | PFVR-08 · COV-08 |
| 2 | 移动层 | Layout Five 移动 Backdrop 可打开且 framing 正常 | PFVR-08 · RESP-08 |
| 3 | 收起侧栏 | 收起侧栏后内容区宽度正确扩展 | PFVR-08 · VIS-08 |
| 4 | 不压侧栏 | 移动层打开时内容不压入侧栏区域 | PFVR-08 · REV-08 |
| 5 | example runtime | `layout-variants-mobile-layer.png` 可复现 | PFVR-08 · PREVIEW-* |

**交互动作**：打开 Layout Variants → Layout Five → 移动层 → 对照 mobile layer 截图。

## PFVR-09 — BI Chart Builder 首屏宽度

**对照 golden**：`bi-chart-builder-runtime.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 首屏利用 | Chart Builder 主内容宽度 ≥ 80%，图表区可见 | PFVR-09 · RESP-09 |
| 2 | 10 runtime | Builder 内 `apexcharts-canvas >= 10` | PFVR-09 · COV-09 |
| 3 | 门禁共存 | state + interaction + visual regression 三门禁同页可访问 | PFVR-09 · REV-09 |
| 4 | 不互相遮挡 | 图表 tooltip 不永久遮挡后续组件 | PFVR-09 · INTER-09 |
| 5 | example runtime | `bi-chart-builder-runtime.png` fullPage 可复现 | PFVR-09 · PREVIEW-* |

**交互动作**：打开 BI 场景 Chart Builder → 检查首屏宽度与 10 图表 → 对照 fullPage 截图。

## PFVR-10 — 页面族视觉回归束

**对照 golden**：`page-family-visual-regression-gates.png`、`verifyPageFamilyVisualRegressionGates`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 统一门禁 | `page-family-visual-regression-gates` + runtime 验证全过 | PFVR-10 · VAL-* |
| 2 | 五项交互 | 宽度/framing/裁切/视口/主题 5 门禁可切换 | PFVR-10 · INTER-10 |
| 3 | 截图证据 | `page-family-visual-regression-gates.png` 含三视口态 | PFVR-10 · REV-10 |
| 4 | audit 静态 | `audit` 含 `verifyPageFamilyVisualRegressionGates` marker | PFVR-10 · COV-10 |
| 5 | 矩阵串联 | visual regression gates 与 `pageFamilyTabChecks` 同轮验证 | PFVR-10 · PREVIEW-* |

**交互动作**：跑 `npm run verify:runtime` → 确认 `pageFamilyVisualRegressionStates` → 对照五门禁截图。

## 交叉引用

- `page-family-visual-regression-review-checklist.md` — PFVR-01～05
- `scene-responsive-review-checklist.md` — RESP-06～10
- `scene-ui-drift-review-checklist.md` — REV-06～10
- `business-validation-checklist.md` — VAL-* 页面族冒烟
- `decision-matrix.md` — G90 页面族视觉回归选型表
- `upgrade-troubleshooting.md` — PFVR-01～10 症状路由
- `agent-retrieval-guide.md` — 页面族视觉回归检索路径
- `quality-rubric.md` — 综合美学维度
