# Agent 失败模式评审清单

> DOCS-036 / G85 产物。对 Agent 生成或人工改写的**控件/页面**执行**可复现 Agent 常见失败抽检**，覆盖主内容宽度、卡片嵌套、移动端表格、dark 边界、手写浮层五类高频失败，并与 `agent-failure-patterns.md`（FAIL-01～10）、`ui-drift-review-checklist.md`、`quality-rubric.md` 截图红线及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 Agent 失败自检 | 对应 FAIL 块 + `quality-rubric.md` 截图红线 |
| 大规模 Agent 生成后抽检 | FAIL-01～05 各抽 1 页 |
| 首屏大面积空白或 KPI 挤在窄列 | 先跑 FAIL-01，再查 `ui-drift-review-checklist.md#rev-01` |
| 多层 Card 嵌套像营销页 | FAIL-02 + `layout-patterns/*.md` 页面壳层 |
| mobile 表格列裁切或操作不可点 | FAIL-03 + `responsive-review-checklist.md#resp-04` |
| dark 边框/分隔线与背景融合 | FAIL-04 + `visual-token-review-checklist.md#vis-02` |
| 手写 div 弹层无 focus trap | FAIL-05 + `accessibility-review-checklist.md#a11y-03` |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
2. 截图视口 **desktop 1440×1000** 与 **mobile 390×844**，**light + dark** 各 1 张；交互组件补打开态截图。
3. 用户可见文案默认中文（技术缩写除外，见 `quality-rubric.md`）。
4. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。
5. 场景级失败（Token 硬编码、英文 mock、浮层遮挡、状态矩阵缺失、不可交互）见 `scene-agent-failure-review-checklist.md` FAIL-06～10。

## FAIL-01 — 主内容列过窄 / 首屏大面积空白

**对照 golden**：`overview-period`、`tablet-overview`、`dashboard-ai-family.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 内容宽度 | 主内容区按 `max-w-(--breakpoint-2xl)` 展开，无首屏右侧大面积空白 | FAIL-01 · REV-01 · DRIFT-01 |
| 2 | KPI 栅格 | desktop 4 列 / tablet 2×2；数字与趋势标签不被裁切 | FAIL-01 · RESP-02 |
| 3 | 壳层 framing | 侧栏展开 290px / 折叠 90px，内容左边界不压入侧栏 | FAIL-01 · RESP-01 |
| 4 | 响应式展开 | 栅格、卡片、表格按容器宽度响应式展开 | FAIL-01 · DRIFT-05 |
| 5 | example runtime | `verify:runtime` 主内容区 bounding box 通过；`dashboard-ai-family.png` 可复现 | FAIL-01 · PREVIEW-* |

**交互动作**：切换 light/dark → 折叠/展开侧栏 → 检查首屏 KPI 区宽度利用率 → 对照 `dashboard-ai-family.png`。

## FAIL-02 — 卡片套卡片 / 营销页感

**对照 golden**：`form-controls-matrix`、`cicd-run-detail`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 页面壳层 | 使用 AppLayout + 单一层级页面标题区；非多层 Card 套 hero | FAIL-02 · DRIFT-02 |
| 2 | 表单容器 | 表单字段在 FormSection/Card 一层内；非 Card 内再套多层 Card | FAIL-02 · PAT-01 |
| 3 | 列表页密度 | DataTableCard 自带 toolbar；非额外包一层装饰 Card | FAIL-02 · COV-03 |
| 4 | 场景页组合 | MS-09～13 领域页用 layout pattern 组合，非散落 mock Card 拼凑 | FAIL-02 · GEN-08 |
| 5 | example runtime | DevOps/Gateway 场景 framing 与 golden 一致，无 hero 级标题堆叠 | FAIL-02 · PREVIEW-* |

**交互动作**：打开 CicdRunDetail 或 Gateway Hub → 检查页面层级 ≤2 层 Card → 对照 `cicd-run-detail` golden。

## FAIL-03 — 表格移动端不可读

**对照 golden**：`data-table-dense`、`paas-resource-table`、`ecommerce-crud-live-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 横向滚动 | 表格容器 `overflow-x-auto`；mobile 列不被永久裁切 | FAIL-03 · RESP-04 |
| 2 | sticky 操作列 | 行操作列 sticky 或 Dropdown 可触达；按钮不重叠 | FAIL-03 · DRIFT-05 |
| 3 | 数字对齐 | KPI/金额列 tabular-nums 或右对齐；mobile 不溢出 | FAIL-03 · VIS-03 |
| 4 | 空/错态 | loading/empty/error 有占位；mobile 同样可读 | FAIL-03 · ASYNC-02 |
| 5 | example runtime | `ecommerce-crud-live-gates.png` 可复现 edit drawer / delete confirm 路径 | FAIL-03 · PREVIEW-* |

**交互动作**：mobile 390px 视口打开 ResourceTable 或 Ecommerce CRUD → 横向滚动 → 打开行操作 Dropdown → 对照 `ecommerce-crud-live-gates.png`。

## FAIL-04 — dark 边界丢失 / 对比度不足

**对照 golden**：`overview-period` dark、`bi-chart-state-gates.png` dark

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 边框语义 | 面板/表格/输入框使用 `dark:border-gray-800` 等语义 Token | FAIL-04 · VIS-02 · CON-01 |
| 2 | 分隔线 | 侧栏/顶栏/内容区分隔线在 dark 下可辨 | FAIL-04 · DRIFT-01 |
| 3 | 控件对比 | Switch/Checkbox/Radio 轨道与圆点在 dark 下可辨认 | FAIL-04 · A11Y-05 |
| 4 | 图表色板 | Chart 使用 `chartPaletteCssVars`；dark 下图例/tooltip 可读 | FAIL-04 · MER-02 |
| 5 | example runtime | light/dark 各 1 张截图对比度通过；`bi-chart-state-gates.png` dark 可复现 | FAIL-04 · PREVIEW-* |

**交互动作**：切换 ThemeToggle → 检查表格边框、输入框 focus ring、Chart tooltip → 对照 dark golden。

## FAIL-05 — 手写 Modal / 无 focus trap

**对照 golden**：`form-dialog-short`、`complex-form-dialog-guard.png`、`ui-elements-live-state-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Radix 浮层 | Dialog/Drawer/Dropdown 来自 shadcn/Radix；禁止 div+fixed 自写 | FAIL-05 · CON-02 · A11Y-03 |
| 2 | 标题与关闭 | Dialog 有 DialogTitle；Esc 可关闭；关闭后焦点回触发器 | FAIL-05 · A11Y-03 |
| 3 | focus trap | Tab 在 overlay 内循环；初始焦点落在关闭或主操作 | FAIL-05 · A11Y-03 |
| 4 | dirty guard | 表单 Dialog 有 dirty close guard；取消不丢列表上下文 | FAIL-05 · LOGIC-02 |
| 5 | example runtime | `complex-form-dialog-guard.png` / `ui-elements-live-state-gates.png` 可复现打开/关闭路径 | FAIL-05 · PREVIEW-* |

**交互动作**：打开 FormDialog → Shift+Tab 检查焦点循环 → Esc 触发 dirty guard → 对照 `complex-form-dialog-guard.png`。

## 完整 Agent 失败评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | 本文件 | FAIL-01～05 |
| 场景级 | `scene-agent-failure-review-checklist.md` | FAIL-06～10 |

完整 Agent 失败评审 = **FAIL-01～10**；PR 前至少抽检 FAIL-01 + FAIL-06（场景级）+ 1 个 MS FAIL-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
rg -n "#[0-9a-fA-F]{6}" src/ --glob '!**/chart-theme.ts'
pnpm exec tsc --noEmit
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的 Agent 失败模式（非一次性笔误）。
- 新业务场景与 example runtime golden 差异根因为 Skill 规则缺口。
- 检索路径超过 3 跳才找到本清单或对应 FAIL 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 FAIL-01（主内容宽度）～ FAIL-05（手写浮层）。

## 检索入口

| 意图 | 读 |
|---|---|
| 失败模式索引 | `agent-failure-patterns.md` |
| 场景级失败 | `scene-agent-failure-review-checklist.md` |
| UI 漂移对照 | `ui-drift-review-checklist.md` |
| 评审规程与封顶规则 | `quality-rubric.md` |
| 组件/页面正选 | `decision-matrix.md` |
| Golden 对照 | `docs/spec/.../shards/golden-screens.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` FAIL-* / DRIFT-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
