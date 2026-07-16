# Complex Form Visual Regression 评审清单

> DOCS-042 / G91 产物。对 Agent 生成或人工改写的 **复杂表单布局** 执行**可复现视觉回归抽检**，覆盖 sticky 操作栏、Drawer/Dialog 浮层 framing、向导步骤指示器与校验错误溢出，并与 `form-validation-logic-review-checklist.md`（LOGIC-01～05）、`logic-completeness-review-checklist.md`（LOGIC-06～10）、`interaction-motion-review-checklist.md`（INTER-01～05）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前复杂表单视觉抽检 | 对应 CFVR 块 + `quality-rubric.md` 逻辑完备 |
| FormPageShell / FormDrawer / FormDialog 抽检 | CFVR-01～05 各抽 1 项 |
| Drawer 行编辑 framing 错位 | CFVR-02 + `complex-form-drawer-guard.png` |
| Dialog 危险确认偏移或裁切 | CFVR-03 + `complex-form-dialog-guard.png` |
| 向导步骤指示器挤压 | CFVR-04 + `form-composition.md` |
| 校验错误与操作栏重叠 | CFVR-05 + `form-validation-logic-review-checklist.md` |

## 通用前置

1. 先完成 `form-validation-logic-review-checklist.md` LOGIC-01～02（必填与错误展示）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/complex-form-visual-regression-gates.png` 与 `complex-form-drawer-guard.png`、`complex-form-dialog-guard.png`。
3. 抽检视口 **desktop 1440×1000** 与 **mobile 390×844** 各至少 1 次。
4. 场景级 5 条复杂表单流程抽检见 `scene-complex-form-visual-regression-review-checklist.md` CFVR-06～10。
5. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。
6. 检索路径见 `agent-retrieval-guide.md` 复杂表单视觉回归抽检行。

## CFVR-01 — Sticky 操作栏对齐

**对照 reference**：`complex-form-visual-regression-gates.png`、`form-composition.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 贴底对齐 | 长表单底部操作栏贴容器底，不漂浮遮挡字段 | CFVR-01 · LOGIC-02 |
| 2 | 按钮组完整 | 取消/草稿/提交按钮完整可见，不被裁切 | CFVR-01 · REV-04 |
| 3 | 滚动行为 | 表单滚动时操作栏保持 sticky，不脱离主容器 | CFVR-01 · INTER-02 |
| 4 | data-state | `data-audit="cfvr-sticky"` `data-state=aligned` | CFVR-01 · COV-05 |
| 5 | example runtime | `verifyComplexFormVisualRegressionGates` sticky gate 全过 | CFVR-01 · PREVIEW-* |

**交互动作**：打开「表单组合」→ 切换 sticky 门禁「模拟漂浮」→ 确认 `data-state=floating` → 点击「恢复贴底」。

## CFVR-02 — Drawer 浮层 Framing

**对照 golden**：`complex-form-drawer-guard.png`、`cfvr-drawer` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 右边界对齐 | Drawer 贴右边界滑入，列表上下文仍可见 | CFVR-02 · PAT-03 |
| 2 | 不越界 | Drawer 面板不超出视口或压入侧栏 | CFVR-02 · RESP-02 |
| 3 | 初始焦点 | 打开后焦点落在关闭按钮或首个字段 | CFVR-02 · A11Y-03 |
| 4 | data-state | `data-audit="cfvr-drawer"` `data-state=in-canvas` | CFVR-02 · COV-05 |
| 5 | example runtime | drawer gate 切换 off-canvas 可复现并恢复 | CFVR-02 · PREVIEW-* |

**交互动作**：点击 drawer 门禁「模拟越界」→ `data-state=off-canvas` → 点击「恢复对齐」。

## CFVR-03 — Dialog 居中与 Guard

**对照 golden**：`complex-form-dialog-guard.png`、`cfvr-dialog` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 居中 | Dialog 在视口水平垂直居中，不偏移裁切 | CFVR-03 · REV-02 |
| 2 | guard 可读 | dirty close guard 与危险确认文案完整可见 | CFVR-03 · COPY-03 |
| 3 | 按钮可达 | 确认/取消按钮不被 backdrop 遮挡 | CFVR-03 · A11Y-03 |
| 4 | data-state | `data-audit="cfvr-dialog"` `data-state=centered` | CFVR-03 · COV-05 |
| 5 | example runtime | dialog gate 切换 off-center 可复现并恢复 | CFVR-03 · PREVIEW-* |

**交互动作**：点击 dialog 门禁「模拟偏移」→ `data-state=off-center` → 点击「恢复居中」。

## CFVR-04 — 向导步骤指示器

**对照 reference**：`form-composition.md`、`cfvr-wizard` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 步骤间距 | 4 步向导标签间距均衡，当前步高亮清晰 | CFVR-04 · VIS-03 |
| 2 | 不重叠 | 步骤文字不挤压重叠，mobile 可换行 | CFVR-04 · RESP-03 |
| 3 | 进度语义 | 已完成/当前/待办步骤视觉层级可辨认 | CFVR-04 · LOGIC-04 |
| 4 | data-state | `data-audit="cfvr-wizard"` `data-state=balanced` | CFVR-04 · COV-05 |
| 5 | example runtime | wizard gate 切换 cramped 可复现并恢复 | CFVR-04 · PREVIEW-* |

**交互动作**：点击向导门禁「模拟挤压」→ `data-state=cramped` → 点击「恢复均衡」。

## CFVR-05 — 校验错误溢出

**对照 reference**：`form-validation-logic-review-checklist.md`、`cfvr-validation` gate

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 错误完整 | 校验错误提示完整可见，不被裁切 | CFVR-05 · LOGIC-01 |
| 2 | 不重叠 | 错误提示不与 sticky 操作栏或字段重叠 | CFVR-05 · REV-04 |
| 3 | 中文可读 | 错误文案使用中文，技术术语保留 API/CI 等 | CFVR-05 · COPY-01 |
| 4 | data-state | `data-audit="cfvr-validation"` `data-state=pass` | CFVR-05 · COV-05 |
| 5 | example runtime | validation gate 模拟 fail 后可恢复 pass | CFVR-05 · PREVIEW-* |

**交互动作**：点击校验门禁「模拟溢出」→ `data-state=fail` → 点击「恢复通过」。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | CFVR-01～05 |
| 场景/流程级 | `scene-complex-form-visual-regression-review-checklist.md` | CFVR-06～10 |

## 交叉引用

- `scene-complex-form-visual-regression-review-checklist.md` — CFVR-06～10
- `form-validation-logic-review-checklist.md` — LOGIC-01～05
- `logic-completeness-review-checklist.md` — LOGIC-06～10
- `decision-matrix.md` — G91 复杂表单视觉回归选型表
- `upgrade-troubleshooting.md` — CFVR-01～10 症状路由
- `agent-retrieval-guide.md` — 复杂表单视觉回归检索路径
- `quality-rubric.md` — 逻辑完备维度
- `complex-form-visual-regression-gates.png` — runtime 截图证据
