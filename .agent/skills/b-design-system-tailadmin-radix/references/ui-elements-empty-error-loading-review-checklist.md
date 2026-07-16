# UiElements Empty / Error / Loading 评审清单

> DOCS-038 / G87 产物。对 Agent 生成或人工改写的 **UiElements 控件与数据展示** 执行**可复现 empty/error/loading 失败态抽检**，覆盖空列表、内联错误、Skeleton/Spinner、重试路径与 loading 防双提交，并与 `async-state-review-checklist.md`（ASYNC-01～05）、`chinese-copy-review-checklist.md`（COPY-02）、`state-index.md` 及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 UiElements 失败态抽检 | 对应 EEL 块 + `quality-rubric.md` 逻辑完备 |
| 大规模 Agent 生成后抽检 | EEL-01～05 各抽 1 个控件族 |
| 空列表无中文说明或无 CTA | 先跑 EEL-01，再查 `chinese-copy-review-checklist.md#copy-02` |
| 错误态无重试或英文 failure copy | EEL-02 + `async-state-review-checklist.md#async-01` |
| Skeleton 塌陷或 loading 可双提交 | EEL-03 + `interaction-motion-review-checklist.md#inter-04` |
| 错误横幅永久抢焦点 | EEL-04 + `ui-elements-keyboard-hover-focus-review-checklist.md#kbf-03` |
| 表格 empty 与筛选无结果混淆 | EEL-05 + `scene-async-state-review-checklist.md` |

## 通用前置

1. 先完成 `async-state-review-checklist.md` ASYNC-01～02（控件级 empty/error/loading）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/ui-elements-empty-error-loading-gates.png`。
3. 抽检视口 **desktop 1440×1000**，**light + dark** 各至少 1 次 empty/error/loading 切换。
4. 场景级 UiElements 22 源页面矩阵抽检见 `scene-ui-elements-empty-error-loading-review-checklist.md` EEL-06～10。
5. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。

## EEL-01 — Empty 空态可读与 CTA

**对照 reference**：`state-index.md#数据状态`、`chinese-copy-review-checklist.md#copy-02`、`ui-elements-empty-error-loading-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 中文说明 | 空列表/空通知有中文标题 + 辅助说明；非空白闪烁 | EEL-01 · COPY-02 · ASYNC-02 |
| 2 | 可选 CTA | 空态有「新建」「刷新」「清除筛选」等合理操作（如适用） | EEL-01 · LOGIC-02 |
| 3 | 结构保留 | 空态保留容器高度/图标占位；非 0 高度塌陷 | EEL-01 · VIS-02 |
| 4 | dark 对比 | light/dark 下空态图标与文案对比足够 | EEL-01 · FAIL-04 |
| 5 | example runtime | `verify:runtime` 切换 `data-state=empty` 且文案为中文 | EEL-01 · PREVIEW-* |

**交互动作**：点击「切换空态」→ 检查中文标题与 CTA → 切换 light/dark 各 1 次 → 对照 `ui-elements-empty-error-loading-gates.png`。

## EEL-02 — Error 内联错误与重试

**对照 golden**：`ui-elements-keyboard-hover-focus-gates.png`（KBF-05）、`bi-chart-state-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 中文错误 | 错误态有中文原因说明；非 `Error`/`Failed` 裸英文 | EEL-02 · COPY-02 |
| 2 | 重试路径 | 提供「重试」「关闭」或深链；非 `console.error` 静默 | EEL-02 · ASYNC-01 |
| 3 | aria 语义 | 内联错误有 `aria-invalid` 或 `role="alert"`/`aria-live` | EEL-02 · A11Y-02 |
| 4 | 焦点合理 | 错误出现后焦点不永久陷阱；可 Tab 到重试按钮 | EEL-02 · KBF-03 |
| 5 | example runtime | `data-audit="ui-eel-error"` `data-state=error` + 重试可点击 | EEL-02 · PREVIEW-* |

**交互动作**：切换 error 态 → 点击重试 → 确认 `data-state` 回到 ready → 对照 runtime `errorState` + `retryWorked`。

## EEL-03 — Loading Skeleton / Spinner 结构保留

**对照 reference**：`interaction-motion-review-checklist.md#inter-04`、`state-index.md#加载状态`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Skeleton | 列表/卡片 loading 用 Skeleton 保留行高与栅格；非空白闪烁 | EEL-03 · INTER-04 |
| 2 | Spinner 内联 | 按钮 loading 为 disabled + 内联 Spinner；不溢出按钮边界 | EEL-03 · INTER-04 |
| 3 | 防双提交 | loading 提交按钮不可再次点击 | EEL-03 · ASYNC-03 |
| 4 | 结构不跳 | loading→ready 切换时布局不剧烈跳动 | EEL-03 · VIS-03 |
| 5 | example runtime | `data-audit="ui-eel-loading"` `data-state=loading` + 按钮 disabled | EEL-03 · PREVIEW-* |

**交互动作**：切换 loading 态 → 确认 Skeleton 可见 → 点击 loading 按钮确认 disabled → 对照 runtime `loadingState: true`。

## EEL-04 — Error 横幅与可关闭路径

**对照 golden**：`ui-notifications`、`scene-async-state-review-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 横幅可读 | 页面级错误横幅有中文标题 + 原因；对比足够 | EEL-04 · COPY-02 |
| 2 | 可关闭 | 提供关闭或「知道了」；关闭后 `data-state=closed` | EEL-04 · LOGIC-02 |
| 3 | aria-live | 动态错误使用 `role="alert"` 或 `aria-live="polite"` | EEL-04 · A11Y-05 |
| 4 | 不遮挡主任务 | 横幅不永久遮挡表格首行或主 CTA | EEL-04 · REV-05 |
| 5 | example runtime | `data-audit="ui-eel-banner"` 可切换 open/closed | EEL-04 · PREVIEW-* |

**交互动作**：打开错误横幅 → 点击关闭 → 确认 DOM 移除或 `data-state=closed` → 对照截图。

## EEL-05 — Empty 与筛选无结果区分

**对照 reference**：`async-state-review-checklist.md#async-02`、`ecommerce-crud-live-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 真 empty | 无数据时文案为「暂无数据」类；有新建 CTA | EEL-05 · ASYNC-02 |
| 2 | 筛选 empty | 筛选无结果文案为「无匹配结果」；有清除筛选 | EEL-05 · LOGIC-04 |
| 3 | 图标语义 | empty 与 filtered-empty 图标/色调可辨（如适用） | EEL-05 · VIS-04 |
| 4 | 不混淆 loading | loading 态不显示 empty 文案 | EEL-05 · ASYNC-02 |
| 5 | example runtime | `data-audit="ui-eel-table"` 可在 empty/filtered/ready 间切换 | EEL-05 · PREVIEW-* |

**交互动作**：切换 table empty → filtered-empty → ready → 确认文案差异 → 对照 `ecommerce-crud-live-gates.png` data-state 矩阵。

## 完整 UiElements 失败态评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | EEL-01～05 |
| 场景/Specimen 级 | `scene-ui-elements-empty-error-loading-review-checklist.md` | EEL-06～10 |

完整 UiElements 失败态评审 = **EEL-01～10**；PR 前至少抽检 EEL-01 + EEL-02 + 1 个 EEL-06～10 Specimen 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
```

## 交叉引用

- `async-state-review-checklist.md` — ASYNC-01～05 异步状态
- `chinese-copy-review-checklist.md` — COPY-02 空态/错误中文
- `scene-ui-elements-empty-error-loading-review-checklist.md` — EEL-06～10 场景级
- `decision-matrix.md` — G87 UiElements 失败态选型表
- `upgrade-troubleshooting.md` — EEL-01～10 症状路由
- `agent-retrieval-guide.md` — Specimen Lab 失败态路由
- `quality-rubric.md` — 逻辑完备 / 约束遵守评分
