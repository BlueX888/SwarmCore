# 场景 Complex Form Visual Regression 评审清单

> DOCS-042 / G91 产物。对 Agent 生成或人工改写的 **5 条复杂表单流程矩阵** 执行**可复现场景级视觉回归抽检**，覆盖 Tabs Product Create、Accordion Billing、Drawer Row Edit、Dialog Danger Confirm、Step Wizard Activation 与 live overlay 截图，并与 `complex-form-visual-regression-review-checklist.md`（CFVR-01～05）、`scene-logic-completeness-review-checklist.md`（LOGIC-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前复杂表单流程抽检 | 对应 CFVR 块 + `quality-rubric.md` |
| 5 条 complex form flow tab 矩阵 | CFVR-06 + `complexFormFlowCount = 5` |
| Drawer 行编辑 live overlay | CFVR-07 + `complex-form-drawer-guard.png` |
| Dialog 危险确认 live overlay | CFVR-08 + `complex-form-dialog-guard.png` |
| 向导开通四步布局 | CFVR-09 + `step-wizard-activation` flow |
| 复杂表单视觉回归束缺门禁 | CFVR-10 + `verify:runtime` `complexFormVisualRegressionStates` |

## 通用前置

1. 先完成 `complex-form-visual-regression-review-checklist.md` CFVR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/complex-form-*.png`。
3. 抽检至少 **Drawer Row Edit + Dialog Danger Confirm + 1 个 page 级流程**。
4. 视口 **desktop 1440×1000** 与 **mobile 390×844** 各 1 次 overlay framing 检查。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景复杂表单视觉回归（G91）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 复杂表单视觉回归抽检行。

## CFVR-06 — 5 条 Flow Tab 矩阵

**对照 golden**：`complexFormFlows = 5`、`complex-form-flows`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | flow 数量 | 5 条复杂表单流程 tab 均可打开 | CFVR-06 · COV-06 |
| 2 | container 标签 | page/drawer/dialog/wizard 容器类型与 flow 一致 | CFVR-06 · PAT-06 |
| 3 | 预览可见 | 切换后 `.complex-form-preview` 画布可见 | CFVR-06 · REV-06 |
| 4 | 模板 chip | 每条 flow 展示 templates/patterns/states | CFVR-06 · GEN-06 |
| 5 | example runtime | `complexFormFlowCount = 5` runtime 全过 | CFVR-06 · VAL-* |

**交互动作**：打开「表单组合」→ 切换 5 条 flow tab → 确认 specimen 与 contract 卡片同步。

## CFVR-07 — Drawer Row Edit Live Overlay

**对照 golden**：`complex-form-drawer-guard.png`、`complex-form-live-drawer`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | overlay 打开 | Drawer 真实 open state，列表上下文保留 | CFVR-07 · INTER-07 |
| 2 | 焦点循环 | Tab 在 overlay 内循环，Shift+Tab 不逃逸 | CFVR-07 · A11Y-03 |
| 3 | dirty guard | Escape 触发 dirty close guard 可放弃关闭 | CFVR-07 · LOGIC-07 |
| 4 | 截图归档 | `complex-form-drawer-guard.png` fullPage 可复现 | CFVR-07 · PREVIEW-* |
| 5 | example runtime | `complexFormLiveOverlays >= 1` drawer 全过 | CFVR-07 · VAL-* |

**交互动作**：打开 Drawer Row Edit → 打开 live drawer → Escape → 放弃关闭 → 对照 guard 截图。

## CFVR-08 — Dialog Danger Confirm Live Overlay

**对照 golden**：`complex-form-dialog-guard.png`、`complex-form-live-dialog`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | overlay 打开 | Dialog 真实 open state，危险文案完整 | CFVR-08 · COPY-08 |
| 2 | submitting | 提交进入 checking/loading 态 | CFVR-08 · ASYNC-08 |
| 3 | close guard | dirty close guard 与取消路径可复现 | CFVR-08 · LOGIC-08 |
| 4 | 截图归档 | `complex-form-dialog-guard.png` fullPage 可复现 | CFVR-08 · PREVIEW-* |
| 5 | example runtime | `complexFormLiveOverlays = 2` dialog 全过 | CFVR-08 · VAL-* |

**交互动作**：打开 Dialog Danger Confirm → 打开 live dialog → 提交 → 对照 guard 截图。

## CFVR-09 — Step Wizard Activation 布局

**对照 golden**：`step-wizard-activation` flow、`cfvr-wizard` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 四步结构 | 身份源/字段映射/策略/测试发布四步可见 | CFVR-09 · PAT-09 |
| 2 | 步骤切换 | 每步校验与回退可交互 | CFVR-09 · LOGIC-09 |
| 3 | async test | 连通性测试显示 checking/success/error | CFVR-09 · ASYNC-09 |
| 4 | 不挤压 | 步骤指示器在 desktop/mobile 不重叠 | CFVR-09 · RESP-09 |
| 5 | example runtime | wizard gate balanced 态 runtime 全过 | CFVR-09 · PREVIEW-* |

**交互动作**：打开 Step Wizard Activation → 检查四步指示器 → 对照 wizard 门禁截图。

## CFVR-10 — 复杂表单视觉回归束

**对照 golden**：`complex-form-visual-regression-gates.png`、`verifyComplexFormVisualRegressionGates`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 统一门禁 | `complex-form-visual-regression-gates` + runtime 验证全过 | CFVR-10 · VAL-* |
| 2 | 五项交互 | sticky/drawer/dialog/wizard/validation 5 门禁可切换 | CFVR-10 · INTER-10 |
| 3 | 截图证据 | `complex-form-visual-regression-gates.png` 含五门禁态 | CFVR-10 · REV-10 |
| 4 | audit 静态 | `audit` 含 `verifyComplexFormVisualRegressionGates` marker | CFVR-10 · COV-10 |
| 5 | 流程串联 | visual regression gates 与 `complexFormFlows = 5` 同轮验证 | CFVR-10 · PREVIEW-* |

**交互动作**：跑 `npm run verify:runtime` → 确认 `complexFormVisualRegressionStates` → 对照五门禁截图。

## 交叉引用

- `complex-form-visual-regression-review-checklist.md` — CFVR-01～05
- `scene-logic-completeness-review-checklist.md` — LOGIC-06～10
- `form-composition.md` — 容器选型与流程规则
- `business-validation-checklist.md` — VAL-* 复杂表单冒烟
- `decision-matrix.md` — G91 复杂表单视觉回归选型表
- `upgrade-troubleshooting.md` — CFVR-01～10 症状路由
- `agent-retrieval-guide.md` — 复杂表单视觉回归检索路径
- `quality-rubric.md` — 逻辑完备维度
- `verifyComplexFormVisualRegressionGates` — runtime 验证函数
- `complex-form-visual-regression-gates.png` — runtime 截图证据
