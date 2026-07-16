# 场景 UiElements 键盘 / Hover / Focus 评审清单

> DOCS-037 / G86 产物。对 Agent 生成或人工改写的 **Specimen Lab 22 源页面与 MS 场景组合** 执行**可复现场景级键盘、hover、focus 与失败态抽检**，覆盖 Modals/Dropdowns、Tabs/Breadcrumb、布尔控件、empty/error/loading 失败态与 Specimen 束，并与 `ui-elements-keyboard-hover-focus-review-checklist.md`（KBF-01～05）、`scene-interaction-review-checklist.md`（INTER-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 Specimen Lab 键盘/hover/focus 抽检 | 对应 KBF 块 + `quality-rubric.md` |
| 大规模 Agent 生成后 22 源页面抽检 | KBF-01～05 + KBF-06～10 各抽 1 页 |
| Modals/Dropdowns 源页面无 Esc/焦点回退 | KBF-06 + `ui-elements-live-state-gates.png` |
| Tabs/Breadcrumb/Pagination 无法键盘切换 | KBF-07 + `state-index.md#导航状态` |
| Switch/Checkbox/Radio 源页面 hover/focus 错位 | KBF-08 + `interaction-motion-review-checklist.md#inter-03` |
| Specimen 仅 happy path 无 empty/error/loading | KBF-09 + `scene-async-state-review-checklist.md` |
| Specimen Lab 22 页矩阵缺统一键盘束 | KBF-10 + `verify:runtime` `uiElementSourceChecks` |

## 通用前置

1. 先完成 `ui-elements-keyboard-hover-focus-review-checklist.md` KBF-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/ui-elements-*.png` 与 `ui-elements-keyboard-hover-focus-gates.png`。
3. 抽检至少 **3 个 overlay 类源页面 + 2 个 navigation 类源页面 + 1 个 feedback 类源页面**。
4. 视口 **desktop 1440×1000** 与 **mobile 390×844** 各 1 次窄屏焦点/触控检查。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景 UiElements 键盘/hover/focus（G86）** 选型表。

## KBF-06 — Modals / Dropdowns / Popover 源页面键盘

**对照 golden**：`ui-modals`、`ui-dropdowns`、`ui-elements-live-state-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Dialog 键盘 | 打开后初始焦点合理；Tab 循环；Esc 可关 | KBF-06 · KBF-03 · FAIL-05 |
| 2 | Dropdown 键盘 | ArrowDown 打开并导航；Enter 选中；Esc 关闭 | KBF-06 · KBF-02 |
| 3 | Popover 层级 | 打开态不永久遮挡后续 specimen；有合理 z-index | KBF-06 · REV-05 |
| 4 | Tooltip 指针 | Tooltip 不拦截键盘焦点；hover/focus 均可触发（如适用） | KBF-06 · INTER-02 |
| 5 | example runtime | Specimen Lab overlay 类源页面 + `ui-elements-keyboard-hover-focus-gates.png` | KBF-06 · PREVIEW-* |

**交互动作**：打开 ui-modals specimen → 键盘打开 Dialog → Esc 关闭 → 打开 Dropdown → ArrowDown 导航 → 对照 runtime 截图。

## KBF-07 — Tabs / Breadcrumb / Pagination 导航键盘

**对照 golden**：`ui-tabs`、`ui-breadcrumb`、`ui-pagination`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Tabs roving | ArrowLeft/Right 切换 tab；active 指示器跟随 | KBF-07 · KBF-02 |
| 2 | Breadcrumb | 当前页不可聚焦或 aria-current；链接可 Tab 到达 | KBF-07 · A11Y-01 |
| 3 | Pagination | 上一页/下一页可键盘激活；disabled 页码不可误触 | KBF-07 · LOGIC-04 |
| 4 | 窄屏 | mobile 下 tabs 可横滚或折行；焦点不丢失 | KBF-07 · RESP-03 |
| 5 | example runtime | `verifyUiElementSourceSpecimens` 覆盖 tabs/breadcrumb 源页截图 | KBF-07 · PREVIEW-* |

**交互动作**：打开 ui-tabs specimen → ArrowRight 切换 → 打开 ui-breadcrumb → Tab 遍历链接 → mobile 390px 复查。

## KBF-08 — 布尔控件与 Slider 源页面 hover/focus

**对照 golden**：`ui-alerts` 邻近布尔区、`form-controls-matrix`、`ui-elements-keyboard-hover-focus-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Switch/Checkbox | Space/Enter 切换；focus 环可见；圆点不错位 | KBF-08 · INTER-03 |
| 2 | Radio group | Arrow 在组内移动；选中态与 label 对齐 | KBF-08 · INTER-03 |
| 3 | Segmented | 选中滑块跟随；键盘切换有过渡 | KBF-08 · KBF-02 |
| 4 | hover 冲突 | checked + hover 态可辨；disabled 无 hover | KBF-08 · KBF-04 |
| 5 | example runtime | `uiElementLiveStates.segmentedActive` + 门禁区布尔控件截图 | KBF-08 · PREVIEW-* |

**交互动作**：Specimen Lab 打开含布尔控件的源页 → 键盘切换 Switch/Radio → hover disabled 项 → 对照 `ui-elements-keyboard-hover-focus-gates.png`。

## KBF-09 — Empty / Error / Loading 失败态与焦点

**对照 golden**：`ui-notifications`、`ui-progress`、`scene-async-state-review-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | empty 可读 | 空列表/空通知有中文说明 + 可选 CTA；非空白闪烁 | KBF-09 · ASYNC-02 · COPY-02 |
| 2 | error 可读 | 错误态有中文文案 + 重试/关闭路径；`aria-live` 或内联错误 | KBF-09 · ASYNC-01 |
| 3 | loading | Skeleton/Spinner 保留结构；loading 按钮 disabled | KBF-09 · INTER-04 |
| 4 | 焦点不陷阱 | 错误横幅不永久抢走焦点；Dialog 关闭后焦点合理 | KBF-09 · KBF-03 |
| 5 | example runtime | 门禁 `data-audit="ui-kbf-error"` + BI/Ecommerce live gates data-state 切换 | KBF-09 · PREVIEW-* |

**交互动作**：切换 error/empty/loading data-state → 检查中文文案与焦点路径 → 对照 `bi-chart-state-gates.png` / `ecommerce-crud-live-gates.png`。

## KBF-10 — Specimen Lab 22 源页面键盘/hover/focus 束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`uiElementSpecimens.ts`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 源页矩阵 | 22 个 UiElements 源页 `verifyUiElementSourceSpecimens` 全通过 | KBF-10 · COV-05 |
| 2 | 打开态截图 | overlay 类源页有 open 态或 live gates 证据 | KBF-10 · FAIL-10 |
| 3 | 键盘束 | KBF-01～05 在 `ui-elements-keyboard-hover-focus-gates` 可复现 | KBF-10 · VAL-* |
| 4 | hover/focus 截图 | `ui-elements-keyboard-hover-focus-gates.png` 含 hover + focus-visible | KBF-10 · INTER-01 |
| 5 | MS 组合 | Dashboard/BI/Ecommerce 页面族 tabs 键盘可达主画布 | KBF-10 · A11Y-10 |

**交互动作**：跑 `verify:runtime` → 确认 `uiElementSourceChecks=22` + `uiElementKeyboardHoverFocusStates` → 抽 3 个源页人工键盘复核 → 写回 decision-matrix 反例（如有）。

## 五类 Specimen 键盘/hover/focus 速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| Overlay | Dialog 无 Esc、Dropdown 无方向键 | `ui-modals` / live gates | KBF-06 · FAIL-05 |
| Navigation | Tabs 无 roving、分页不可键盘达 | `ui-tabs` / `ui-breadcrumb` | KBF-07 · A11Y-01 |
| Boolean | Switch 圆点错位、disabled 仍 hover | `form-controls-matrix` | KBF-08 · INTER-03 |
| Failure | empty/error 英文或无 CTA | `scene-async-state-review-checklist.md` | KBF-09 · COPY-02 |
| 矩阵束 | 22 页缺截图或不可键盘抽检 | `verify:runtime` | KBF-10 · FAIL-10 |

## 完整场景 UiElements 键盘/hover/focus 评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | `ui-elements-keyboard-hover-focus-review-checklist.md` | KBF-01～05 |
| 场景/Specimen 级 | 本文件 | KBF-06～10 |

完整评审 = **KBF-01～10**；PR 前至少抽检 KBF-01 + KBF-06 + KBF-10。

## 验证命令汇总

```bash
npm run audit -w examples/b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
```

## 交叉引用

- `ui-elements-keyboard-hover-focus-review-checklist.md` — KBF-01～05
- `scene-interaction-review-checklist.md` — INTER-06～10 场景动效
- `scene-accessibility-review-checklist.md` — A11Y-06～10 场景可访问性
- `decision-matrix.md` — G86 选型表
- `upgrade-troubleshooting.md` — KBF-06～10 症状
- `agent-retrieval-guide.md` — Specimen Lab 路由
- `examples/b-design-system-tailadmin-radix/README.md` — runtime 验收入口
