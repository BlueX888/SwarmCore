# BI Chart Interaction 评审清单

> DOCS-040 / G89 产物。对 Agent 生成或人工改写的 **ApexCharts 运行时图表** 执行**可复现深度交互抽检**，覆盖数据点悬停、图例切换、刷选缩放与下钻事件，并与 `interaction-motion-review-checklist.md`（INTER-01～05）、`scene-interaction-review-checklist.md`（INTER-06～10）、`component-coverage-review-checklist.md`（COV-02）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 BI 图表交互抽检 | 对应 CHART 块 + `quality-rubric.md` 交互与动效 |
| Chart Builder / 指标页 ApexCharts 抽检 | CHART-01～05 各抽 1 类图表 |
| 折线/面积图无 point hover | CHART-01 + `bi-chart-interaction-gates.png` |
| 多系列图例不可切换 | CHART-02 + `bi-chart-state-gates.png` |
| 趋势图无刷选/缩放 | CHART-03 + `decision-matrix.md` G89 选型表 |
| 柱状图点击无下钻路径 | CHART-04 + `bi-drill-down.md` |
| 10 类 runtime 图表缺交互门禁 | CHART-05 + `verify:runtime` `biChartInteractionStates` |

## 通用前置

1. 先完成 `interaction-motion-review-checklist.md` INTER-01～02（hover/tooltip 可见性）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/bi-chart-interaction-gates.png` 与 `bi-chart-state-gates.png`。
3. 抽检视口 **desktop 1440×1000**，**light + dark** 各至少 1 次悬停与图例切换。
4. 场景级 Chart Builder / BI 子页面抽检见 `scene-bi-chart-interaction-review-checklist.md` CHART-06～10。
5. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。
6. 检索路径见 `agent-retrieval-guide.md` BI 图表深度交互抽检行。

## CHART-01 — 数据点悬停与 Tooltip

**对照 reference**：`chart-theme.md`、`bi-chart-interaction-gates.png`、`RuntimeChartsGallery`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 悬停触发 | 折线/面积/柱状数据点 hover 显示 tooltip | CHART-01 · INTER-01 |
| 2 | 标记放大 | line/area 悬停时 marker 放大或高亮 | CHART-01 · VIS-02 |
| 3 | 中文标签 | tooltip 标题/数值使用中文或行业固定术语 | CHART-01 · COPY-02 |
| 4 | data-state | `data-audit="bi-chart-hover-state"` 悬停后 `data-state=active` | CHART-01 · COV-05 |
| 5 | example runtime | `.apexcharts-tooltip` 可见 + runtime 门禁全过 | CHART-01 · PREVIEW-* |

**交互动作**：打开 Chart Builder → 悬停折线数据点 → 确认 tooltip 与 `hoverLabel` → 对照 runtime `pointHover: true`。

## CHART-02 — 图例系列切换

**对照 golden**：`bi-chart-state-gates.png`、`bi-chart-interaction-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 可点击 | 图例项可点击隐藏/显示对应系列 | CHART-02 · INTER-02 |
| 2 | 视觉反馈 | 隐藏系列后图表重绘；图例项变淡或划线 | CHART-02 · VIS-03 |
| 3 | 多系列 | 至少 2 个系列可独立切换 | CHART-02 · COV-02 |
| 4 | data-state | `data-audit="bi-chart-legend-toggle-state"` 跟随切换 | CHART-02 · COV-05 |
| 5 | example runtime | 点击 `.apexcharts-legend-series` 后 runtime 全过 | CHART-02 · PREVIEW-* |

**交互动作**：点击图例「当前值」→ 确认系列隐藏 → `data-state=series-hidden` → 再点击恢复。

## CHART-03 — 刷选 / 缩放范围

**对照 reference**：`bi-filter-linkage.md`、`bi-chart-interaction-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 刷选手势 | 折线/面积图支持拖拽选择 x 轴范围 | CHART-03 · INTER-03 |
| 2 | 选区可见 | 选区有半透明高亮；不遮挡 tooltip | CHART-03 · VIS-04 |
| 3 | 范围回写 | 选区范围写入 `data-state` 或面包屑 | CHART-03 · LOGIC-03 |
| 4 | 清除路径 | 可清除选区或重置全量 | CHART-03 · INTER-04 |
| 5 | example runtime | `data-audit="bi-chart-brush-state"` `data-state=selected` | CHART-03 · PREVIEW-* |

**交互动作**：在折线图上拖拽选区 → 确认 `brushRange` 中文范围 → 对照 runtime `brushSelected: true`。

## CHART-04 — 下钻 / 明细事件

**对照 reference**：`bi-drill-down.md`、`drill-breadcrumb.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 点击下钻 | 柱状/饼图点击触发 dataPointSelection 或等效事件 | CHART-04 · PAT-04 |
| 2 | 路径可见 | 面包屑或路径标签显示当前下钻层级 | CHART-04 · LOGIC-04 |
| 3 | 返回路径 | 提供返回上级或重置 | CHART-04 · INTER-05 |
| 4 | 中文路径 | 下钻路径标签使用中文 | CHART-04 · COPY-02 |
| 5 | example runtime | `data-audit="bi-chart-drill-state"` `data-state=drilled` | CHART-04 · PREVIEW-* |

**交互动作**：点击柱状条 → 确认路径变为「X月 · 明细」→ 点击返回上级。

## CHART-05 — Runtime 图表矩阵交互门禁

**对照 golden**：`verifyBiChartInteractionGates`、`runtime-charts` gallery

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 统一门禁 | `bi-chart-interaction-gates` + `verifyBiChartInteractionGates` runtime 全过 | CHART-05 · VAL-* |
| 2 | 截图证据 | `bi-chart-interaction-gates.png` 含悬停/刷选/下钻态 | CHART-05 · INTER-01 |
| 3 | 10 类图表 | `chartCanvases >= 10` 且 interaction gates 与 state gates 串联 | CHART-05 · COV-05 |
| 4 | 不互相遮挡 | interaction gates 与 state gates 同页可访问 | CHART-05 · REV-05 |
| 5 | audit 静态 | `audit` 含 `verifyBiChartInteractionGates` marker | CHART-05 · PREVIEW-* |

**交互动作**：跑 `npm run verify:runtime` → 确认 `biChartInteractionStates` → 对照双门禁截图。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | CHART-01～05 |
| 场景/BI 级 | `scene-bi-chart-interaction-review-checklist.md` | CHART-06～10 |

## 交叉引用

- `scene-bi-chart-interaction-review-checklist.md` — CHART-06～10
- `interaction-motion-review-checklist.md` — INTER-01～05
- `decision-matrix.md` — G89 BI 图表深度交互选型表
- `upgrade-troubleshooting.md` — CHART-01～10 症状路由
- `agent-retrieval-guide.md` — BI 图表深度交互检索路径
- `quality-rubric.md` — 交互与动效质量维度
