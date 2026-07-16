# 场景 BI Chart Interaction 评审清单

> DOCS-040 / G89 产物。对 Agent 生成或人工改写的 **Chart Builder / BI 子页面与 MS 场景组合** 执行**可复现场景级 ApexCharts 深度交互抽检**，覆盖 Builder 门禁、cross-filter、drill-down 与 10 类 runtime 图表矩阵，并与 `bi-chart-interaction-review-checklist.md`（CHART-01～05）、`scene-interaction-review-checklist.md`（INTER-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 Chart Builder 交互抽检 | 对应 CHART 块 + `quality-rubric.md` |
| BI Analytics 5 子页面抽检 | CHART-01～05 + CHART-06～10 各抽 1 页 |
| Chart Builder 仅静态图 | CHART-06 + `bi-chart-interaction-gates.png` |
| Cross-filter 图表无联动 | CHART-07 + `bi-filter-linkage.md` |
| 指标页 10 类图无悬停 | CHART-08 + `RuntimeChartsGallery` |
| Drill-down 场景无路径 | CHART-09 + `bi-drill-down-dashboard.tsx` |
| BI runtime 缺交互束 | CHART-10 + `verify:runtime` `biChartInteractionStates` |

## 通用前置

1. 先完成 `bi-chart-interaction-review-checklist.md` CHART-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/bi-chart-*.png`。
3. 抽检至少 **Chart Builder + 指标与图表 + 1 个 BI 场景子页**。
4. 视口 **desktop 1440×1000** 与 **mobile 390×844** 各 1 次 tooltip 可读性检查。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景 BI 图表深度交互（G89）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` BI 图表深度交互抽检行。

## CHART-06 — Chart Builder 深度交互门禁

**对照 golden**：`bi-chart-builder-runtime.png`、`bi-chart-interaction-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 双门禁 | state gates + interaction gates 同 Builder 页可访问 | CHART-06 · COV-06 |
| 2 | 10 runtime | Builder 内 `apexcharts-canvas >= 10` | CHART-06 · COV-07 |
| 3 | 悬停 tooltip | 折线门禁悬停显示 `.apexcharts-tooltip` | CHART-06 · INTER-06 |
| 4 | 图例切换 | 点击图例可隐藏系列 | CHART-06 · INTER-07 |
| 5 | example runtime | `verifyBiChartInteractionGates` + `verifyBiChartStateGates` 全过 | CHART-06 · PREVIEW-* |

**交互动作**：打开 Chart Builder → 跑 interaction gates 四项交互 → 对照 `bi-chart-interaction-gates.png`。

## CHART-07 — Cross-filter 图表联动

**对照 golden**：`cross-filter-specimen`、`bi-filter-linkage.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 多图共存 | cross-filter 页至少 2 个 runtime 图表 | CHART-07 · PAT-06 |
| 2 | 筛选 chips | 筛选 chip 可清除；中文标签 | CHART-07 · COPY-06 |
| 3 | 悬停一致 | 各图 tooltip 样式与 chart-theme 一致 | CHART-07 · VIS-06 |
| 4 | 表格联动 | 图表旁表格反映筛选上下文 | CHART-07 · LOGIC-06 |
| 5 | example runtime | BI 场景 cross-filter tab 画布可见 | CHART-07 · PREVIEW-* |

**交互动作**：打开 BI cross-filter → 检查 2 图 + 筛选 chips → 悬停折线确认 tooltip。

## CHART-08 — 指标与图表 10 类 Runtime 矩阵

**对照 golden**：`RuntimeChartsGallery`、`verify:runtime` `chartCanvases`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 类型覆盖 | bar/h-bar/stacked/line/area/pie/donut/radial/radar/funnel 全渲染 | CHART-08 · COV-08 |
| 2 | 悬停抽检 | 至少 line + bar 2 类可触发 tooltip | CHART-08 · INTER-08 |
| 3 | 图例抽检 | 多系列图（line/radar/stacked）图例可辨 | CHART-08 · VIS-08 |
| 4 | 主题一致 | light/dark 下 grid/legend/tooltip 可读 | CHART-08 · RESP-08 |
| 5 | example runtime | `data-runtime="apexcharts-*"` 10 marker 全过 | CHART-08 · PREVIEW-* |

**交互动作**：打开指标与图表 → 确认 10 canvas → 悬停 line + bar 各 1 次。

## CHART-09 — 下钻仪表盘场景

**对照 golden**：`bi-drill-down.md`、`drill-down-dashboard.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 下钻路径 | 面包屑显示当前层级；中文 | CHART-09 · LOGIC-09 |
| 2 | 图表点击 | 图表点击可进入明细或切换视图 | CHART-09 · PAT-09 |
| 3 | 明细表 | 明细分页/导出态可见 | CHART-09 · COV-09 |
| 4 | 返回 | 面包屑或按钮可返回上级 | CHART-09 · INTER-09 |
| 5 | example runtime | interaction gates drill 态 + drill-down frame | CHART-09 · PREVIEW-* |

**交互动作**：interaction gates 点击柱条下钻 → BI drill-down frame 检查面包屑。

## CHART-10 — BI Runtime 交互束与 audit 门禁

**对照 golden**：`verifyBiChartInteractionGates`、`biChartStates`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 统一门禁 | `biChartInteractionStates` + state gates runtime 全过 | CHART-10 · VAL-* |
| 2 | 截图证据 | `bi-chart-interaction-gates.png` 含四项深度交互态 | CHART-10 · INTER-01 |
| 3 | 串联不遮挡 | interaction + state + 10 gallery 同 Builder 可读 | CHART-10 · REV-10 |
| 4 | audit 静态 | `audit` 含 interaction gates marker + verify 函数 | CHART-10 · COV-10 |
| 5 | 选型一致 | Chart Builder 用 ApexCharts + chart-theme；非假柱状条 | CHART-10 · FAIL-04 |

**交互动作**：跑 `npm run verify:runtime` → 确认 `biChartInteractionStates` → 对照双门禁截图。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | `bi-chart-interaction-review-checklist.md` | CHART-01～05 |
| 场景/BI 级 | 本文件 | CHART-06～10 |

## 交叉引用

- `bi-chart-interaction-review-checklist.md` — CHART-01～05
- `scene-interaction-review-checklist.md` — INTER-06～10
- `decision-matrix.md` — G89 场景 BI 图表深度交互选型表
- `upgrade-troubleshooting.md` — CHART-06～10 症状路由
- `business-validation-checklist.md` — VAL-* 业务验收
- `agent-retrieval-guide.md` — BI 图表深度交互检索路径
