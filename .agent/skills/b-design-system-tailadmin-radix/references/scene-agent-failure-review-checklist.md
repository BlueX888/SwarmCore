# 场景 Agent 失败模式评审清单

> DOCS-036 / G85 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级 Agent 失败抽检**，覆盖 Token 硬编码、英文 mock、浮层遮挡、状态矩阵缺失、不可交互验收五类场景高频失败，并与 `agent-failure-patterns-review-checklist.md`（FAIL-01～05）、`agent-failure-patterns.md`、`quality-rubric.md` 截图红线、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景 Agent 失败抽检 | 对应 FAIL 块 + `quality-rubric.md` 截图红线 |
| 大规模 Agent 生成后 MS 场景抽检 | FAIL-01～05（页面级）+ FAIL-06～10（场景级）各抽 1 页 |
| BI 场景散落 hex 或 Chart 裸色 | 先跑 FAIL-06，再查 `scene-constraint-compliance-review-checklist.md#con-06` |
| CI/CD/Gateway mock 英文混杂 | FAIL-07 + `scene-chinese-copy-review-checklist.md#copy-07` |
| PaaS 恢复 Dialog 遮挡表格关键列 | FAIL-08 + `scene-ui-drift-review-checklist.md#rev-09` |
| MS 场景仅 happy path 无 empty/error | FAIL-09 + `scene-async-state-review-checklist.md#async-06` |
| example 只有静态 mock 不可点击 | FAIL-10 + `examples/b-design-system-tailadmin-radix/README.md` |

## 通用前置

1. 先完成 `agent-failure-patterns-review-checklist.md` FAIL-01～05（控件/页面级失败）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**；视口 **desktop 1440×1000**，**light + dark** 各 1 张。
4. 用户可见文案默认中文（技术缩写除外，见 `quality-rubric.md`）。
5. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。

## FAIL-06 — BI / Data Screen Token 硬编码与色板漂移

**对照 golden**：`bi-filter-linkage`、`bi-chart-state-gates.png`、`data-screen-canvas`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 语义 Token | BI 场景 KPI/Chart/FilterBar 无页面内 `#hex`；使用 `brand-*`/`gray-*` | FAIL-06 · CON-06 · VIS-06 |
| 2 | Chart 色板 | 各图表使用 `getBaseChartOptions` + `chartPaletteCssVars` | FAIL-06 · MER-02 |
| 3 | 大屏层次 | Data Screen 有 KPI 带、主图区、明细区；非空容器假柱状条 | FAIL-06 · REV-06 |
| 4 | dark 对比 | light/dark 切换后 Chart tooltip/legend 可读 | FAIL-06 · FAIL-04 |
| 5 | example runtime | `bi-chart-state-gates.png` 可复现 legend/tooltip 与 chart type 切换 | FAIL-06 · PREVIEW-* |

**交互动作**：打开 BI Chart Builder → `rg` 扫描场景页 hex → 切换 chart type donut → 对照 `bi-chart-state-gates.png`。

## FAIL-07 — DevOps / Gateway 英文 mock 与文案混杂

**对照 golden**：`cicd-run-detail`、`gateway-patterns`、`workflow-ticket-reply.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段/日志中文 | PipelineStageBar、LogStream、ArtifactTable 表头/按钮为中文 | FAIL-07 · COPY-07 |
| 2 | 危险操作文案 | Rollback/Approve Dialog 标题、确认、取消为中文 | FAIL-07 · COPY-07 · LOGIC-07 |
| 3 | Gateway mock | EndpointProbe、BalanceQuota、License 面板中文 mock | FAIL-07 · COPY-08 |
| 4 | 技术术语 | API、CI/CD、K8s、P95 等固定术语可保留；非整句英文 placeholder | FAIL-07 · CON-04 |
| 5 | example runtime | `workflow-ticket-reply.png` / `gateway-patterns` 可见文案中文化 | FAIL-07 · PREVIEW-* |

**交互动作**：打开 CicdRunDetail → 检查阶段标签与 Rollback Dialog 文案 → 切换 Gateway Hub 子面板 → 对照 golden 中文 mock。

## FAIL-08 — PaaS / MS 浮层打开态遮挡关键内容

**对照 golden**：`paas-restore-dialog-open`、`paas-scale-dialog-open`、`complex-form-drawer-guard.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Dialog 层级 | 恢复/伸缩 Dialog 打开态不遮挡表格关键列到不可读 | FAIL-08 · REV-09 · INTER-04 |
| 2 | Drawer 层级 | FormDrawer 打开态保留列表上下文；关闭路径可辨 | FAIL-08 · INTER-04 |
| 3 | Dropdown/Popover | 行操作 Dropdown 不永久遮挡后续 KPI/阶段条 | FAIL-08 · DRIFT-05 |
| 4 | z-index 分层 | 浮层 `z-99999` 语义；非 modal 用 Popover | FAIL-08 · VIS-04 |
| 5 | example runtime | `paas-restore-dialog-open` / `complex-form-drawer-guard.png` 可复现打开/关闭 | FAIL-08 · PREVIEW-* |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 检查表格关键列仍可读 → 关闭 → 对照 `paas-restore-dialog-open` golden。

## FAIL-09 — MS 场景 loading/empty/error 状态矩阵缺失

**对照 golden**：`bi-chart-state-gates.png`、`ecommerce-crud-live-gates.png`、`email-chat-live-gates.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | BI data-state | Chart/KPI 有 empty/error/success 可观察切换；非仅 happy path | FAIL-09 · ASYNC-06 |
| 2 | Ecommerce CRUD | create/edit/delete 有 loading/empty/error/ready data-state | FAIL-09 · ASYNC-02 |
| 3 | Email/Chat | inbox multi-select、reply、attachment 有 empty/error/ready | FAIL-09 · ASYNC-02 |
| 4 | 重试路径 | error 态有中文重试 CTA；retry 后保留筛选上下文 | FAIL-09 · ASYNC-01 |
| 5 | example runtime | `ecommerce-crud-live-gates.png` / `email-chat-live-gates.png` 可复现 data-state 切换 | FAIL-09 · PREVIEW-* |

**交互动作**：触发 BI chart data empty → 恢复 success → Ecommerce 触发 loading → 对照 live gates 截图。

## FAIL-10 — MS 场景不可交互 / Agent 失败束抽检

**对照 golden**：`ui-elements-live-state-gates.png`、`bi-chart-state-gates.png`、Specimen Lab 22 页矩阵

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`agent-failure-patterns.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 可点击操作 | Select/MultiSelect/DatePicker/Dialog/Table/Switch 等可真实操作 | FAIL-10 · INTER-05 |
| 2 | 打开态截图 | dropdown/dialog/drawer/popover 有打开态截图且可关闭 | FAIL-10 · REV-06 |
| 3 | UiElements 矩阵 | Specimen Lab 22 个源页面可逐个打开、active source 校验 | FAIL-10 · COV-05 |
| 4 | MS-09～13 束 | 按 MS 表各抽 1 页：FAIL-06～09 在场景内组合满足 | FAIL-10 · VAL-* |
| 5 | example runtime | `npm run verify:runtime` exit 0；live gates 截图可复现 | FAIL-10 · PREVIEW-* |

**交互动作**：Specimen Lab 打开 dropdown + dialog → BI Chart Builder 切换 legend → 按 MS 表抽 1 页对照 decision-matrix **场景 Agent 失败（G85）** 选型表 → 跑 `verify:runtime` → 对照 `ui-elements-live-state-gates.png`。

## 五类场景 Agent 失败速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | hex 硬编码、Chart 裸色、假占位画布 | `bi-filter-linkage` golden | FAIL-06 · CON-06 |
| DevOps/Gateway | 英文阶段/日志/mock、Rollback 不可交互 | `cicd-run-detail` golden | FAIL-07 · COPY-07 |
| PaaS | Dialog 遮挡表格、Maps 压扁 | `paas-patterns` golden | FAIL-08 · REV-09 |
| 状态矩阵 | 仅 happy path、error 无重试 | live gates 截图 | FAIL-09 · ASYNC-06 |
| 不可交互 | 静态 mock、无打开态截图 | Specimen Lab + verify:runtime | FAIL-10 · INTER-05 |

## 完整 Agent 失败评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `agent-failure-patterns-review-checklist.md` | FAIL-01～05 |
| 场景级 | 本文件 | FAIL-06～10 |

完整 Agent 失败评审 = **FAIL-01～10**；PR 前至少抽检 FAIL-01 + FAIL-06 + 1 个 MS FAIL-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
npm run audit -w examples/b-design-system-tailadmin-radix
pnpm exec tsc --noEmit
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级 Token 硬编码、英文 mock、浮层遮挡、状态矩阵缺失或不可交互验收。
- MS 场景组合与 example runtime golden 差异根因为 Skill 规则缺口。
- 检索路径超过 3 跳才找到本清单或对应 FAIL 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 FAIL-06（BI 场景）～ FAIL-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 失败模式索引 | `agent-failure-patterns.md` |
| 控件/页面级失败 | `agent-failure-patterns-review-checklist.md` |
| UI 漂移对照 | `scene-ui-drift-review-checklist.md` |
| 评审规程与封顶规则 | `quality-rubric.md` |
| 组件/页面正选 | `decision-matrix.md` |
| Golden 对照 | `docs/spec/.../shards/golden-screens.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` FAIL-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
