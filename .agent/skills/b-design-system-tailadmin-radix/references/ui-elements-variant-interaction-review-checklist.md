# UiElements Variant / Interaction 评审清单

> DOCS-039 / G88 产物。对 Agent 生成或人工改写的 **UiElements 控件与数据展示** 执行**可复现变体数量与交互态抽检**，覆盖变体下限、语义切换、打开/选中态、overlay 打开态与 loading/disabled 交互矩阵，并与 `interaction-motion-review-checklist.md`（INTER-01～05）、`component-coverage-review-checklist.md`（COV-02）、`state-index.md` 及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 UiElements 变体/交互抽检 | 对应 VAR 块 + `quality-rubric.md` 组件覆盖率 |
| 大规模 Agent 生成后抽检 | VAR-01～05 各抽 1 个控件族 |
| 源页面仅 1 个变体或 happy path | 先跑 VAR-01，再查 `prd/scenarios/S00-tailadmin-pages.md` |
| 按钮/徽章语义变体不可切换 | VAR-02 + `decision-matrix.md` G88 选型表 |
| Segmented/Tabs 无 active 态 | VAR-03 + `ui-elements-keyboard-hover-focus-review-checklist.md#kbf-02` |
| Dialog/Drawer 无打开态截图 | VAR-04 + `scene-interaction-review-checklist.md` |
| 22 源页 variants 字段与 example 不一致 | VAR-05 + `uiElementSpecimens` catalog |

## 通用前置

1. 先完成 `interaction-motion-review-checklist.md` INTER-01～02（控件级 hover/open/active）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/ui-elements-variant-interaction-gates.png`。
3. 抽检视口 **desktop 1440×1000**，**light + dark** 各至少 1 次变体切换与打开态截图。
4. 场景级 UiElements 22 源页面矩阵抽检见 `scene-ui-elements-variant-interaction-review-checklist.md` VAR-06～10。
5. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。
6. 检索路径见 `agent-retrieval-guide.md` Specimen Lab 变体/交互态抽检行。

## VAR-01 — 变体数量下限

**对照 reference**：`prd/scenarios/S00-tailadmin-pages.md`、`component-coverage-review-checklist.md#cov-02`、`ui-elements-variant-interaction-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 关键模板 | Button/Badge/Card 等关键模板至少 **3** 个可见变体 | VAR-01 · COV-02 |
| 2 | 一般模板 | 其余模板至少 **2** 个可见变体 | VAR-01 · COV-02 |
| 3 | 非占位 | 变体为真实样式差异；非重复文案 | VAR-01 · GEN-02 |
| 4 | 中文标签 | 变体切换按钮/标签使用中文或行业固定术语 | VAR-01 · COPY-02 |
| 5 | example runtime | `data-audit="ui-var-count"` `data-variant-count>=3` 且可点击切换 | VAR-01 · PREVIEW-* |

**交互动作**：打开变体门禁 → 逐个点击 3 个按钮变体 → 确认 `data-state` 跟随变化 → 对照 `ui-elements-variant-interaction-gates.png`。

## VAR-02 — 语义 / 尺寸变体切换

**对照 golden**：`ui-badges`、`ui-buttons`、`ui-elements-variant-interaction-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 语义色 | success/warning/error/info 语义变体可辨且对比足够 | VAR-02 · VIS-02 |
| 2 | 尺寸阶梯 | sm/md/lg 至少 2 档可见（如适用） | VAR-02 · VIS-03 |
| 3 | 状态联动 | 变体切换不丢 hover/focus 环 | VAR-02 · KBF-01 |
| 4 | dark 一致 | light/dark 下语义变体仍可读 | VAR-02 · FAIL-04 |
| 5 | example runtime | `data-audit="ui-var-semantic"` 可切换 success/warning/error | VAR-02 · PREVIEW-* |

**交互动作**：切换徽章语义色 → 检查边框/背景变化 → dark 模式再切换 1 次 → 对照 runtime `semanticVariant`。

## VAR-03 — Active / Selected / Segmented 交互态

**对照 reference**：`ui-buttons-group`、`ui-tabs`、`ui-elements-live-state-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | active 可见 | segmented/tabs 有明确 active 背景或下划线 | VAR-03 · INTER-02 |
| 2 | 可点击切换 | 点击或方向键可改变 active 项 | VAR-03 · KBF-02 |
| 3 | data-state | active 索引写入 `data-state` 供 runtime 门禁 | VAR-03 · COV-05 |
| 4 | 不跳布局 | 切换 active 不引起容器高度跳动 | VAR-03 · VIS-03 |
| 5 | example runtime | `data-audit="ui-var-segment"` 点击后 `data-state` 更新 | VAR-03 · PREVIEW-* |

**交互动作**：点击「周」分段 → 确认 active 样式 → 对照 runtime `segmentActiveIndex: 1`。

## VAR-04 — Overlay 打开态矩阵

**对照 golden**：`ui-modals`、`ui-dropdowns`、`ui-elements-live-state-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 打开态 | Dialog/Drawer/Dropdown 有真实 open 态 DOM | VAR-04 · INTER-01 |
| 2 | 关闭路径 | 有关闭按钮或 Esc 可回到 closed | VAR-04 · KBF-04 |
| 3 | 截图证据 | 打开态截图不遮挡后续门禁到无法阅读 | VAR-04 · REV-05 |
| 4 | 层级 | overlay z-index 高于页面内容 | VAR-04 · DRIFT-03 |
| 5 | example runtime | `data-audit="ui-var-overlay"` open → closed 可验证 | VAR-04 · PREVIEW-* |

**交互动作**：点击「打开 Drawer」→ 确认 `data-state=open` → 点击关闭 → 对照 runtime `overlayOpen: false`。

## VAR-05 — 源 catalog 变体矩阵对齐

**对照 reference**：`uiElementSpecimens.ts`、`verifyUiElementSourceSpecimens`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | variants 字段 | 每个 specimen `variants.length >= 2` | VAR-05 · COV-05 |
| 2 | interactions 字段 | 每个 specimen `interactions.length >= 1` | VAR-05 · INTER-01 |
| 3 | 预览一致 | UiElementPreview 展示 catalog 声明的变体 | VAR-05 · GEN-03 |
| 4 | 模板 chip | templates chip 与 `component-index.md` 路径一致 | VAR-05 · TYPE-02 |
| 5 | example runtime | 22 源页 `verifyUiElementSourceSpecimens` 全过 + 变体门禁截图 | VAR-05 · PREVIEW-* |

**交互动作**：Specimen Lab 逐个打开 22 源页 → 核对 variants 列表与预览 → 对照 `ui-elements-*.png` element screenshots。

## 完整 UiElements 变体/交互评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | VAR-01～05 |
| 场景/Specimen 级 | `scene-ui-elements-variant-interaction-review-checklist.md` | VAR-06～10 |

完整 UiElements 变体/交互评审 = **VAR-01～10**；PR 前至少抽检 VAR-01 + VAR-03 + 1 个 VAR-06～10 Specimen 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
```

## 交叉引用

- `interaction-motion-review-checklist.md` — INTER-01～05 控件级交互
- `component-coverage-review-checklist.md` — COV-02 变体覆盖
- `scene-ui-elements-variant-interaction-review-checklist.md` — VAR-06～10 场景级
- `decision-matrix.md` — G88 UiElements 变体/交互选型表
- `upgrade-troubleshooting.md` — VAR-01～10 症状路由
- `agent-retrieval-guide.md` — Specimen Lab 变体/交互态检索路径
