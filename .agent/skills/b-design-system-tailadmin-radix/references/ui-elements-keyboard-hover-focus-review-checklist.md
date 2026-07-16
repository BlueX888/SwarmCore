# UiElements 键盘 / Hover / Focus 评审清单

> DOCS-037 / G86 产物。对 Agent 生成或人工改写的 **UiElements 控件与浮层** 执行**可复现键盘、hover、focus-visible 与失败态抽检**，覆盖 focus 环、方向键导航、Esc 关闭、hover 反馈、禁用/错误焦点行为，并与 `interaction-motion-review-checklist.md`（INTER-01～05）、`accessibility-review-checklist.md`（A11Y-01～05）、`state-index.md` 及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 UiElements 键盘/hover/focus 抽检 | 对应 KBF 块 + `quality-rubric.md` 交互与动效质量 |
| 大规模 Agent 生成后抽检 | KBF-01～05 各抽 1 个控件族 |
| 按钮/输入 focus 环不可见或鼠标点击也出粗环 | 先跑 KBF-01，再查 `interaction-motion.md` |
| 菜单/分段/标签无法用方向键切换 | KBF-02 + `state-index.md#交互状态` |
| Popover/菜单 Esc 无法关闭或焦点丢失 | KBF-03 + `accessibility-review-checklist.md#a11y-03` |
| hover 无反馈或 disabled 仍有 hover 高亮 | KBF-04 + `interaction-motion-review-checklist.md#inter-01` |
| 错误输入无 `aria-invalid` 或禁用控件仍可 Tab 聚焦 | KBF-05 + `form-validation-logic-review-checklist.md` |

## 通用前置

1. 先完成 `interaction-motion-review-checklist.md` INTER-01～02（控件级 hover/focus/浮层）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/ui-elements-keyboard-hover-focus-gates.png`。
3. 抽检视口 **desktop 1440×1000**，**light + dark** 各至少 1 次键盘 Tab 与 hover 检查。
4. 场景级 UiElements 22 源页面矩阵抽检见 `scene-ui-elements-keyboard-hover-focus-review-checklist.md` KBF-06～10。
5. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。

## KBF-01 — Focus-visible 环与 Tab 顺序

**对照 reference**：`interaction-motion.md`、`state-index.md#交互状态`、`ui-elements-keyboard-hover-focus-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Button focus | 键盘 Tab 时 primary/outline/ghost 有 `focus-visible:ring-*`；鼠标点击不强制粗环 | KBF-01 · INTER-01 · A11Y-01 |
| 2 | Input focus | 文本输入 focus 环可见；label 与输入关联 `htmlFor`/`id` | KBF-01 · A11Y-02 |
| 3 | Tab 顺序 | 主任务区 Tab 顺序符合视觉阅读顺序；不跳入隐藏侧栏 | KBF-01 · A11Y-01 |
| 4 | dark 对比 | light/dark 下 focus 环与背景对比足够 | KBF-01 · FAIL-04 |
| 5 | example runtime | `verify:runtime` 聚焦按钮后 `document.activeElement` 正确；截图可复现 | KBF-01 · PREVIEW-* |

**交互动作**：键盘 Tab 遍历门禁区主按钮 → 检查 focus-visible 环 → 切换 light/dark 各 1 次 → 对照 `ui-elements-keyboard-hover-focus-gates.png`。

## KBF-02 — 方向键导航（菜单 / 分段 / 标签）

**对照 golden**：`ui-elements-live-state-gates.png`、`form-controls-matrix`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 垂直菜单 | ArrowDown/ArrowUp 在菜单项间移动；active 项有可见高亮 | KBF-02 · INTER-01 |
| 2 | 水平标签 | ArrowLeft/ArrowRight 或 Tab 在 tablist 内切换；active tab 可辨 | KBF-02 · INTER-03 |
| 3 | 分段控件 | 分段按钮可用方向键或 Tab+Enter 切换；选中态有过渡 | KBF-02 · INTER-03 |
| 4 | roving tabindex | 复合控件使用 roving tabindex 或 Radix 内置键盘行为 | KBF-02 · A11Y-03 |
| 5 | example runtime | `data-audit="ui-kbf-menu"` activeIndex 随方向键变化 | KBF-02 · PREVIEW-* |

**交互动作**：聚焦菜单 → ArrowDown 两次 → 确认 active 项变化 → 标签页 ArrowRight 切换 → 对照 runtime `menuActiveIndex`/`tabActiveIndex`。

## KBF-03 — Esc 关闭与焦点回退

**对照 golden**：`ui-elements-live-state-gates.png`、`complex-form-dialog-guard.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Esc 关闭 | 迷你 Popover/菜单按 Esc 关闭；`data-state` 回到 closed | KBF-03 · INTER-02 · A11Y-03 |
| 2 | 焦点回退 | 关闭后焦点回到触发器或合理邻近控件 | KBF-03 · A11Y-03 |
| 3 | 不穿透 | Esc 不同时关闭多层浮层导致上下文丢失（有 guard 时先确认） | KBF-03 · LOGIC-02 |
| 4 | 滚动锁定 | 浮层打开时背景不滚动；关闭后恢复 | KBF-03 · INTER-02 |
| 5 | example runtime | `verify:runtime` Esc 后 popover `data-state=closed` | KBF-03 · PREVIEW-* |

**交互动作**：打开迷你 Popover → Esc → 确认关闭且焦点可继续 Tab → 对照 runtime `popoverOpen: false`。

## KBF-04 — Hover 反馈与指针态

**对照 reference**：`interaction-motion.md`、`ui-elements-keyboard-hover-focus-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 按钮 hover | primary/outline 有背景或边框变化；非瞬时跳色 | KBF-04 · INTER-01 |
| 2 | 菜单项 hover | 菜单/列表项 hover 有浅底；与 active/selected 不冲突 | KBF-04 · INTER-01 |
| 3 | 卡片 hover | 可点击卡片 hover 有阴影或边框变化（如适用） | KBF-04 · INTER-05 |
| 4 | disabled 无 hover | `disabled` 控件无 hover 高亮；`cursor-not-allowed` | KBF-04 · A11Y-05 |
| 5 | example runtime | `data-audit="ui-kbf-hover"` `data-state=hovered` 可由 Playwright hover 触发 | KBF-04 · PREVIEW-* |

**交互动作**：鼠标 hover 门禁卡片 → 确认 `data-state` 变化 → hover disabled 按钮确认无高亮 → 截图 hover 态。

## KBF-05 — 禁用 / 错误 / 只读焦点行为

**对照 reference**：`form-validation-logic-review-checklist.md`、`state-index.md#表单状态`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | disabled 跳过 | disabled 按钮/输入不可操作；Tab 顺序合理（可跳过或保持可见禁用态） | KBF-05 · A11Y-05 |
| 2 | error 焦点 | 错误输入有 `aria-invalid` + 可见错误文案；focus 环仍可见 | KBF-05 · A11Y-02 · LOGIC-01 |
| 3 | readonly | readonly 可选中复制；不冒充可编辑 | KBF-05 · LOGIC-01 |
| 4 | loading | loading 按钮 disabled + Spinner；不可双提交 | KBF-05 · ASYNC-03 · INTER-04 |
| 5 | example runtime | `data-audit="ui-kbf-error"` `data-state=error` 且 input 带 `aria-invalid` | KBF-05 · PREVIEW-* |

**交互动作**：Tab 到错误输入 → 检查 `aria-invalid` 与错误文案 → 点击 disabled 按钮确认无状态变化 → 对照 runtime `errorState: true`。

## 完整 UiElements 键盘/hover/focus 评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | KBF-01～05 |
| 场景/Specimen 级 | `scene-ui-elements-keyboard-hover-focus-review-checklist.md` | KBF-06～10 |

完整 UiElements 键盘/hover/focus 评审 = **KBF-01～10**；PR 前至少抽检 KBF-01 + KBF-02 + 1 个 KBF-06～10 Specimen 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
# 业务仓库：Playwright 键盘/hover/focus 截图
```

## 交叉引用

- `interaction-motion-review-checklist.md` — INTER-01～05 控件级交互
- `accessibility-review-checklist.md` — A11Y-01～05 可访问性
- `scene-ui-elements-keyboard-hover-focus-review-checklist.md` — KBF-06～10 场景级
- `decision-matrix.md` — G86 UiElements 键盘/hover/focus 选型表
- `upgrade-troubleshooting.md` — KBF-01～10 症状路由
- `agent-retrieval-guide.md` — 任务路由
- `quality-rubric.md` — 交互与动效质量维度
