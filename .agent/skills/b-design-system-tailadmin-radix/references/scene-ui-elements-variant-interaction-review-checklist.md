# 场景 UiElements Variant / Interaction 评审清单

> DOCS-039 / G88 产物。对 Agent 生成或人工改写的 **Specimen Lab 22 源页面与 MS 场景组合** 执行**可复现场景级变体数量与交互态抽检**，覆盖按钮/徽章、卡片/列表、浮层、媒体轮播与 22 源页变体束，并与 `ui-elements-variant-interaction-review-checklist.md`（VAR-01～05）、`scene-component-coverage-review-checklist.md`（COV-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 Specimen Lab 变体/交互抽检 | 对应 VAR 块 + `quality-rubric.md` |
| 大规模 Agent 生成后 22 源页面抽检 | VAR-01～05 + VAR-06～10 各抽 1 页 |
| Buttons/Badges 仅 primary 单变体 | VAR-06 + `ui-elements-variant-interaction-gates.png` |
| Cards/Lists 缺 hover/inline action | VAR-07 + `ui-elements-*.png` |
| Modals/Dropdowns 无打开态 | VAR-08 + `ui-elements-live-state-gates.png` |
| Carousel/Videos 无真实媒体区 | VAR-09 + Adapter runtime pack |
| 22 源页缺统一变体束 | VAR-10 + `verify:runtime` `uiElementVariantInteractionStates` |

## 通用前置

1. 先完成 `ui-elements-variant-interaction-review-checklist.md` VAR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/ui-elements-*.png` 与 `ui-elements-variant-interaction-gates.png`。
3. 抽检至少 **2 个 action 类源页面 + 2 个 display 类源页面 + 1 个 overlay 类源页面**。
4. 视口 **desktop 1440×1000** 与 **mobile 390×844** 各 1 次变体可读性检查。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景 UiElements 变体/交互（G88）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` Specimen Lab 变体/交互态抽检行。

## VAR-06 — Buttons / Badges / ButtonsGroup 变体矩阵

**对照 golden**：`ui-buttons`、`ui-badges`、`ui-buttons-group`、`ui-elements-variant-interaction-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 按钮变体 | primary/outline/ghost/danger 至少 3 种可见 | VAR-06 · COV-06 |
| 2 | 徽章变体 | solid/soft/outline + 语义色可切换 | VAR-06 · VIS-06 |
| 3 | 按钮组 | segmented active 态 + icon command 可见 | VAR-06 · INTER-06 |
| 4 | loading/disabled | 按钮 loading 与 disabled 变体可辨 | VAR-06 · ASYNC-06 |
| 5 | example runtime | 门禁 `ui-var-count` + `ui-var-semantic` runtime 全过 | VAR-06 · PREVIEW-* |

**交互动作**：打开 ui-buttons specimen → 检查 3+ 变体 → 切换 ui-badges 语义色 → 对照 runtime 截图。

## VAR-07 — Cards / Lists / Avatars 展示变体

**对照 golden**：`ui-cards`、`ui-lists`、`ui-avatars`、`ui-elements-*.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 卡片变体 | plain/header/metric/media 至少 2 种布局 | VAR-07 · PAT-06 |
| 2 | 列表变体 | ordered/icon/metric 或 dense/comfortable 可辨 | VAR-07 · COV-07 |
| 3 | 头像变体 | sm/md/lg + image/fallback/online 状态 | VAR-07 · VIS-07 |
| 4 | hover 线索 | 卡片 hover lift 或列表行 hover 可见 | VAR-07 · INTER-07 |
| 5 | example runtime | 22 源页 element screenshot 含展示类变体 | VAR-07 · PREVIEW-* |

**交互动作**：打开 ui-cards → 检查 metric/media 变体 → ui-avatars 检查 online/offline → 对照 element screenshot。

## VAR-08 — Modals / Dropdowns / Tooltips 浮层交互

**对照 golden**：`ui-modals`、`ui-dropdowns`、`ui-tooltips`、`ui-elements-live-state-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Dialog 打开态 | 居中/确认 Dialog 有 open 截图 | VAR-08 · INTER-08 |
| 2 | Drawer/Sheet | 侧滑/底部 sheet 有 open 态（如适用） | VAR-08 · PAT-08 |
| 3 | Dropdown | 菜单 open 态不遮挡后续 specimen | VAR-08 · REV-08 |
| 4 | Tooltip | hover 或 focus 触发可见；不永久遮挡 | VAR-08 · A11Y-08 |
| 5 | example runtime | 门禁 `ui-var-overlay` + live gates dropdown/dialog open | VAR-08 · PREVIEW-* |

**交互动作**：打开 ui-modals → 触发 Dialog open → live gates dropdown open → 对照 `ui-elements-live-state-gates.png`。

## VAR-09 — Carousel / Videos / Images 媒体交互

**对照 golden**：`ui-carousel`、`ui-videos`、`Adapter runtime pack`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 媒体区可见 | 轮播/视频/图片有真实可见画布非占位灰块 | VAR-09 · COV-09 |
| 2 | 轮播交互 | next/prev 或 indicator 可切换 slide | VAR-09 · INTER-09 |
| 3 | 变体数量 | 至少 2 种 carousel 导航/指示器变体 | VAR-09 · PAT-09 |
| 4 | 比例美学 | 媒体区 framing 正常；无异常裁切 | VAR-09 · RESP-09 |
| 5 | example runtime | Adapter runtime Swiper slide 切换 + element screenshot | VAR-09 · PREVIEW-* |

**交互动作**：Adapter runtime pack 点击 carousel next → 检查 active slide 变化 → ui-videos specimen 检查媒体区。

## VAR-10 — 22 源页变体束与 runtime 门禁

**对照 golden**：`verifyUiElementSourceSpecimens`、`uiElementSpecimens.ts`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 统一门禁 | `ui-elements-variant-interaction-gates` + `verifyUiElementVariantInteractionGates` runtime 全过 | VAR-10 · VAL-* |
| 2 | 截图证据 | `ui-elements-variant-interaction-gates.png` 含变体切换与 overlay open 态 | VAR-10 · INTER-01 |
| 3 | catalog 对齐 | 22 页 `variants.length>=2` 且 `interactions.length>=1` | VAR-10 · COV-10 |
| 4 | 门禁串联 | KBF + EEL + VAR 三门禁同页可访问不互相遮挡 | VAR-10 · REV-05 |
| 5 | audit 静态 | `audit:pages` `uiElementSpecimenCount=22` + `verifyUiElementVariantInteractionGates` marker | VAR-10 · PREVIEW-* |

**交互动作**：跑 `npm run verify:runtime` → 确认 `uiElementVariantInteractionStates` → 对照三门禁截图。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | `ui-elements-variant-interaction-review-checklist.md` | VAR-01～05 |
| 场景/Specimen 级 | 本文件 | VAR-06～10 |

## 交叉引用

- `ui-elements-variant-interaction-review-checklist.md` — VAR-01～05
- `scene-component-coverage-review-checklist.md` — COV-06～10
- `decision-matrix.md` — G88 场景 UiElements 变体/交互选型表
- `upgrade-troubleshooting.md` — VAR-06～10 症状路由
- `business-validation-checklist.md` — VAL-* 业务验收
- `agent-retrieval-guide.md` — Specimen Lab 变体/交互态检索路径
