# 场景 UiElements Empty / Error / Loading 评审清单

> DOCS-038 / G87 产物。对 Agent 生成或人工改写的 **Specimen Lab 22 源页面与 MS 场景组合** 执行**可复现场景级 empty/error/loading 失败态抽检**，覆盖通知/进度、表格空态、图表面板、表单异步与 Specimen 束，并与 `ui-elements-empty-error-loading-review-checklist.md`（EEL-01～05）、`scene-async-state-review-checklist.md`（ASYNC-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 Specimen Lab 失败态抽检 | 对应 EEL 块 + `quality-rubric.md` |
| 大规模 Agent 生成后 22 源页面抽检 | EEL-01～05 + EEL-06～10 各抽 1 页 |
| Notifications/Progress 仅 happy path | EEL-06 + `ui-elements-live-state-gates.png` |
| 表格 empty 与筛选无结果混淆 | EEL-07 + `ecommerce-crud-live-gates.png` |
| Chart/BI 面板 error 白屏无重试 | EEL-08 + `bi-chart-state-gates.png` |
| 表单 async validating 无反馈 | EEL-09 + `complex-form-dialog-guard.png` |
| Specimen 22 页缺统一失败态束 | EEL-10 + `verify:runtime` `uiElementEmptyErrorLoadingStates` |

## 通用前置

1. 先完成 `ui-elements-empty-error-loading-review-checklist.md` EEL-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/ui-elements-*.png` 与 `ui-elements-empty-error-loading-gates.png`。
3. 抽检至少 **2 个 feedback 类源页面 + 2 个 data 类源页面 + 1 个 overlay 类源页面**。
4. 视口 **desktop 1440×1000** 与 **mobile 390×844** 各 1 次窄屏失败态可读性检查。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景 UiElements 失败态（G87）** 选型表。

## EEL-06 — Notifications / Progress / Alerts 失败态

**对照 golden**：`ui-notifications`、`ui-progress`、`ui-alerts`、`ui-elements-live-state-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 空通知 | 无通知时有中文说明；非空白区域 | EEL-06 · COPY-02 |
| 2 | 错误通知 | 失败通知有中文原因 + 可选重试/关闭 | EEL-06 · ASYNC-01 |
| 3 | Progress loading | 进度条 loading 保留轨道；complete/error 态可辨 | EEL-06 · INTER-04 |
| 4 | Alert 横幅 | 错误 Alert 可关闭；不永久遮挡后续 specimen | EEL-06 · REV-05 |
| 5 | example runtime | 门禁 `ui-eel-banner` + live gates notification read 态 | EEL-06 · PREVIEW-* |

**交互动作**：打开 ui-notifications specimen → 切换 empty/error → 打开 ui-progress → 检查 complete/loading → 对照 runtime 截图。

## EEL-07 — 表格 / 列表 Empty 与筛选无结果

**对照 golden**：`ui-lists`、`ecommerce-crud-live-gates.png`、`email-chat-live-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 真 empty | 无数据中文「暂无数据」+ 新建 CTA | EEL-07 · ASYNC-02 |
| 2 | 筛选 empty | 「无匹配结果」+ 清除筛选；与真 empty 文案不同 | EEL-07 · LOGIC-04 |
| 3 | loading 表 | 表级 Skeleton 保留列头；非整页空白 | EEL-07 · INTER-04 |
| 4 | error 表 | 表级 error 有重试；不丢筛选条件 | EEL-07 · ASYNC-01 |
| 5 | example runtime | Ecommerce/Email live gates `dataState` empty/error/ready 切换 | EEL-07 · PREVIEW-* |

**交互动作**：Ecommerce CRUD 切换 loading/empty/error/ready → Email/Chat 切换 empty/error → 对照 `ecommerce-crud-live-gates.png`。

## EEL-08 — Chart / BI 面板失败态

**对照 golden**：`bi-chart-state-gates.png`、`RuntimeChartsGallery`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | data empty | 图表无数据有中文说明 + 可选刷新 | EEL-08 · ASYNC-05 |
| 2 | data error | 图表 error 有中文原因 + 重试；非白屏 | EEL-08 · ASYNC-05 |
| 3 | loading | Chart Skeleton 保留面板高度；legend 区不塌陷 | EEL-08 · INTER-06 |
| 4 | tooltip 失败 | tooltip 在 error 态不误导为 0 值 | EEL-08 · LOGIC-03 |
| 5 | example runtime | `biChartStates.dataState` empty/error/success 切换 | EEL-08 · PREVIEW-* |

**交互动作**：Chart Builder 切换 data empty/error/success → 确认面板非白屏 → 对照 `bi-chart-state-gates.png`。

## EEL-09 — 表单异步校验与提交 Loading

**对照 golden**：`complex-form-drawer-guard.png`、`complex-form-dialog-guard.png`、`form-controls-matrix`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | async validating | 异步校验有 Spinner/文案；字段不静默失败 | EEL-09 · ASYNC-03 |
| 2 | submit loading | 提交中按钮 disabled + checking 文案 | EEL-09 · INTER-04 |
| 3 | field error | 字段 error 中文 + `aria-invalid`；提交后仍可见 | EEL-09 · LOGIC-01 |
| 4 | 整表单 error | 顶部横幅或 Alert 汇总错误；可关闭 | EEL-09 · EEL-04 |
| 5 | example runtime | complex form Dialog submitting/checking 态可验证 | EEL-09 · PREVIEW-* |

**交互动作**：打开 FormDialog specimen → 提交进入 checking → 触发字段 error → 对照 `complex-form-dialog-guard.png`。

## EEL-10 — Specimen Lab 22 源页面失败态束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`uiElementSpecimens.ts`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 统一门禁 | `ui-elements-empty-error-loading-gates` + `verifyUiElementEmptyErrorLoadingGates` runtime 全过 | EEL-10 · VAL-* |
| 2 | 截图证据 | `ui-elements-empty-error-loading-gates.png` 含 empty/error/loading 三态 | EEL-10 · INTER-01 |
| 3 | MS live gates | BI/Ecommerce/Email/ComplexForm live gates data-state 矩阵齐全 | EEL-10 · FAIL-09 |
| 4 | 源页矩阵 | 22 源页 `verifyUiElementSourceSpecimens` 仍全通过 | EEL-10 · COV-05 |
| 5 | 选型回写 | 发现英文 failure copy 或缺 CTA 时更新 decision-matrix 反例 | EEL-10 · COPY-02 |

**交互动作**：跑 `verify:runtime` → 确认 `uiElementEmptyErrorLoadingStates` → 抽 3 个源页人工切换失败态 → 写回 decision-matrix 反例（如有）。

## 五类 Specimen 失败态速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| Feedback | 通知/进度仅 happy path | `ui-notifications` / live gates | EEL-06 · COPY-02 |
| Data | 表格 empty 与筛选混淆 | `ecommerce-crud-live-gates.png` | EEL-07 · ASYNC-02 |
| Chart | BI 面板 error 白屏 | `bi-chart-state-gates.png` | EEL-08 · ASYNC-05 |
| Form | 提交无 checking/字段 error 英文 | `complex-form-dialog-guard.png` | EEL-09 · ASYNC-03 |
| 矩阵束 | 22 页缺失败态门禁截图 | `verify:runtime` | EEL-10 · FAIL-09 |

## 完整场景 UiElements 失败态评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | `ui-elements-empty-error-loading-review-checklist.md` | EEL-01～05 |
| 场景/Specimen 级 | 本文件 | EEL-06～10 |

完整评审 = **EEL-01～10**；PR 前至少抽检 EEL-01 + EEL-06 + EEL-10。

## 验证命令汇总

```bash
npm run audit -w examples/b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
```

## 交叉引用

- `ui-elements-empty-error-loading-review-checklist.md` — EEL-01～05
- `scene-async-state-review-checklist.md` — ASYNC-06～10 场景异步
- `scene-chinese-copy-review-checklist.md` — COPY-06～10 场景中文
- `decision-matrix.md` — G87 选型表
- `upgrade-troubleshooting.md` — EEL-06～10 症状
- `agent-retrieval-guide.md` — Specimen Lab 路由
- `examples/b-design-system-tailadmin-radix/README.md` — runtime 验收入口
