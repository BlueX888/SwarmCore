# 场景生成一致性评审清单

> DOCS-030 / G79 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级生成一致性抽检**，覆盖 BI 大屏筛选与图表组合、DevOps 流水线阶段与日志、Gateway 端点探测与配额、PaaS 危险操作与 ConfigDiff 及 MS 场景生成一致性束，并与 `generation-consistency-review-checklist.md`（GEN-01～05）、`decision-matrix.md`、`agent-retrieval-guide.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景生成一致性抽检 | 对应 GEN 块 + `quality-rubric.md` 生成一致性规则 |
| 大规模 Agent 生成后 MS 场景抽检 | GEN-01～05（控件/页面级）+ GEN-06～10（场景级）各抽 1 页 |
| BI 页散落 Card 拼凑或单图冒充联动 | 先跑 GEN-06，再查 `layout-patterns/bi-filter-linkage.md` |
| CI/CD 页误用 Kanban 或 Switch 列表 | GEN-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway 子面板硬编码 mock 或非受控组合 | GEN-08 + MS-09 `ControlPlaneHub` |
| PaaS 列表硬塞地图 Card 或散落拼凑 | GEN-09 + `templates/paas/resource-table.tsx` |
| MS 场景组合与模板契约/受控 props 漂移 | GEN-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `generation-consistency-review-checklist.md` GEN-01～05（选型、Token/密度、状态矩阵、检索路由、MS 组合）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
4. 组件/页面不确定时**必须先读** `decision-matrix.md`，禁止无矩阵依据的随机 Card 拼凑。
5. 同类 MS 场景生成结果应在模板组合、受控 props、Token 密度与状态矩阵上与 golden / example runtime 一致。

## GEN-06 — BI / Data Screen 筛选与图表生成一致性

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`templates/bi/cross-filter-dashboard.tsx`、`templates/bi/filter-bar.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 筛选组合 | `FilterBar` chips + `CrossFilterDashboard` 或 `DrillDownDashboard` 正选；非单图 onClick 冒充联动 | GEN-06 · SEL-01 |
| 2 | 图表模板 | Chart 走 `templates/bi/*` + `chartPaletteCssVars`；同类 BI 页图表类型/密度一致 | GEN-02 · CON-06 |
| 3 | KPI 栅格 | KPI 卡片密度、数字排版与 golden 一致；非页面内随意改栅格 | GEN-02 · VIS-06 |
| 4 | 状态矩阵 | loading/empty/error 与 `state-index.md` 一致；同类 BI 页状态表现统一 | GEN-03 · ASYNC-06 |
| 5 | 大屏画布 | Data Screen 使用 `data-screen-canvas` 或多区块布局模式；非空容器假柱状条 | GEN-06 · PAT-05 |

**交互动作**：打开 BI 筛选页 → 对照 decision-matrix **生成一致性（G67）** 列 → 切换筛选 chip 观察 KPI/图表联动 → 对照 `bi-chart-state-gates.png`。

## GEN-07 — DevOps 流水线阶段与日志生成一致性

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 领域正选 | `PipelineStageBar` + `LogStreamPanel` + `ArtifactTable` 组合；非 Kanban 冒充 CI/CD | GEN-07 · SEL-02 |
| 2 | 阶段密度 | 阶段条、日志流、制品表间距密度与 golden 一致 | GEN-02 · MS-10 |
| 3 | 状态矩阵 | 阶段 active/成功/失败/等待审批态与同类 DevOps 页一致 | GEN-03 · INTER-07 |
| 4 | Rollback 路径 | Rollback Dialog 与 `CicdRunDetail` 受控 props 一致；非每页自建确认框 | GEN-01 · LOGIC-02 |
| 5 | 检索路由 | DevOps 任务 ≤3 跳：`domain-scenarios` → `devops-template` → `templates/devops/*` | GEN-04 · RUN-04 |

**交互动作**：打开 CicdRunDetail → 对照 MS-10 正选模板组合 → 切换阶段/日志态 → 对照 `workflow-ticket-reply.png`。

## GEN-08 — Gateway 端点探测与配额生成一致性

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 受控组合 | `ControlPlaneHub` 子面板受控 props；非散落 mock Card 拼凑 | GEN-08 · SEL-05 |
| 2 | 探测表一致 | `EndpointProbeTable` 列结构、badge 语义与同类 Gateway 页一致 | GEN-01 · CON-08 |
| 3 | 配额面板 | `BalanceQuota` 与配额摘要布局在同类页密度一致 | GEN-02 · MS-09 |
| 4 | Dialog 选型 | 探测/License Dialog 走 Radix/shadcn；非手写 div 浮层 | GEN-01 · CON-02 |
| 5 | 检索路由 | Gateway 任务 ≤3 跳：`gateway-template` → `templates/gateway/*` → SOR-05 | GEN-04 · RUN-04 |

**交互动作**：抽查 Gateway 页 3 个子面板 → 模拟配额超限 → 打开探测 Dialog → 对照 `gateway-patterns` golden。

## GEN-09 — PaaS 资源与危险操作生成一致性

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 列表+地图 | `ResourceTable` + 可选 Maps 同一地理语义；非扁平表硬塞随机地图 Card | GEN-09 · SEL-03 |
| 2 | ConfigDiff | `ConfigDiff` / `DescriptionDiff` 正选；同类 PaaS 页 diff 高亮模式一致 | GEN-02 · CON-09 |
| 3 | 危险流程 | 恢复/伸缩 Dialog 与 `ops-danger-flow` 模板一致；非每页自建 destructive 按钮 | GEN-01 · INTER-09 |
| 4 | 容量卡片 | `CapacityCard` 栅格与用量条密度与 golden 一致 | GEN-02 · MS-12 |
| 5 | theme helper | Maps/Chart override 走 `mergeMapLibreOptions` / `getBaseChartOptions` deep merge | GEN-02 · MER-02 |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 展开 ConfigDiff → 对照 `paas-restore-dialog-open` golden。

## GEN-10 — MS 场景生成一致性束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：`ControlPlaneHub` 受控 props + 探测表 + 配额面板 + Radix Dialog 组合一致 | SOR-05 · GEN-08 |
| 2 | MS-10 | CI/CD：`PipelineStageBar` + `LogStreamPanel` + `ArtifactTable` 组合；非 Kanban | SOR-02 · GEN-07 |
| 3 | MS-11 | BI：`FilterBar` + `CrossFilterDashboard` 联动 + `chartPaletteCssVars` 一致 | SOR-01 · GEN-06 |
| 4 | MS-12 | PaaS：`ResourceTable` + 可选 Maps + 危险 Dialog + ConfigDiff 一致 | SOR-03 · GEN-09 |
| 5 | MS-13 | 治理：`PermissionMatrix` + `AuditLogTable` + Auth Wizard；非 Switch 列表 | SOR-04 · GEN-01 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景生成一致性（G79）** 选型表 → 确认 GEN-01～10 在场景内组合满足。

## 五类场景生成一致性速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | 单图冒充联动、KPI 栅格漂移、假占位画布 | `bi-filter-linkage.md` | GEN-06 · SEL-01 |
| DevOps | Kanban 冒充 CI/CD、阶段/日志密度不一致 | `devops-template.md` | GEN-07 · SEL-02 |
| Gateway | 散落 mock Card、非受控 Hub、探测表结构漂移 | `gateway-template.md` | GEN-08 · SEL-05 |
| PaaS | 扁平表硬塞地图、ConfigDiff 模式不一致 | `paas-template.md` | GEN-09 · SEL-03 |
| MS 束 | 领域页模板组合/受控 props 与 MS 表不一致 | `business-validation-checklist.md` | GEN-10 · VAL-* |

## 完整生成一致性评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `generation-consistency-review-checklist.md` | GEN-01～05 |
| 场景级 | 本文件 | GEN-06～10 |

完整生成一致性评审 = **GEN-01～10**；PR 前至少抽检 GEN-01 + GEN-06 + 1 个 MS GEN-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/run_token_hit_tests.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级组件错选、页面错选或同类 MS 场景 Token/状态/密度表现不一致。
- MS 场景组合缺少受控 props 或模板引用，导致 Agent 每次生成结果不同。
- 检索路径超过 3 跳才找到本清单或对应 GEN 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 GEN-06（BI 场景）～ GEN-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 生成一致性规则与封顶 | `quality-rubric.md` |
| 控件/页面级一致性 | `generation-consistency-review-checklist.md` |
| 组件/页面正选 | `decision-matrix.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 视觉 Token 密度 | `visual-token-review-checklist.md` |
| 状态矩阵 | `state-index.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` GEN-* / SEL-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
