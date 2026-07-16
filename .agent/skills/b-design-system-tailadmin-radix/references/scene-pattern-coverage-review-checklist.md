# 场景模式覆盖评审清单

> DOCS-032 / G81 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级模式覆盖抽检**，覆盖 BI 大屏筛选与图表布局、DevOps 流水线阶段与日志页面组合、Gateway 控制平面 Hub、PaaS 资源与危险操作布局及 MS 场景页面模式束，并与 `pattern-coverage-review-checklist.md`（PAT-01～05）、`pattern-index.md`、`route-index.md`、`state-index.md`、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景模式覆盖抽检 | 对应 PAT 块 + `quality-rubric.md` 模式覆盖规则 |
| 大规模 Agent 生成后 MS 场景抽检 | PAT-01～05（控件/页面级）+ PAT-06～10（场景级）各抽 1 页 |
| BI 页散落 Card 拼凑或缺 layout pattern | 先跑 PAT-06，再查 `layout-patterns/bi-filter-linkage.md` |
| CI/CD 页误用 Kanban 或缺 DevOps 页面模式 | PAT-07 + `layout-patterns/master-detail-ops.md` |
| Gateway 子面板无 Hub 布局或缺控制平面 pattern | PAT-08 + MS-09 `ControlPlaneHub` |
| PaaS 列表缺 ResourceTable 页面模式或危险流程布局 | PAT-09 + `layout-patterns/detail-page.md` |
| MS 场景组合缺完整页面 layout 或 preview 占位 | PAT-10 + `domain-scenarios.md` |

## 通用前置

1. 先完成 `pattern-coverage-review-checklist.md` PAT-01～05（output modes、页面/布局模式、状态模式、路由检索、MS 组合）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
4. 禁止只有孤立组件、无页面级 layout pattern 或 output mode 指引的「半成品场景页」。
5. 场景页必须体现完整页面组合（PageHeader + 主内容 grid/stack + 适用状态模式），不能只有占位 Card 或假数据堆叠。

## PAT-06 — BI / Data Screen 场景页面模式覆盖

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`layout-patterns/bi-drill-down.md`、`layout-patterns/data-screen-canvas.md`、`pattern-index.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 筛选联动布局 | `FilterBar` + `CrossFilterDashboard`/`DrillDownDashboard` 走 `bi-filter-linkage` / `bi-drill-down` layout pattern | PAT-06 · PAT-02 |
| 2 | 仪表盘栅格 | KPI + Chart 区使用 `dashboard-grid` 或 BI dashboard layout；非孤立 Card 堆叠 | PAT-02 · dashboard.md |
| 3 | 大屏画布 | Data Screen 使用 `data-screen-canvas` 或多区块布局模式；非空容器假柱状条 | PAT-05 · BI-005 |
| 4 | 状态模式 | loading/empty/error 与 `state-index.md` 一致；筛选无结果有 empty CTA | PAT-04 · ASYNC-06 |
| 5 | example runtime | BI 场景有 example section + 打开态截图；`bi-chart-state-gates.png` 可复现 | PAT-05 · PREVIEW-* |

**交互动作**：打开 BI 筛选页 → 对照 `pattern-index.md` 决策树 → 切换筛选 chip 观察 KPI/图表联动布局 → 对照 `bi-chart-state-gates.png`。

## PAT-07 — DevOps 流水线阶段与日志场景页面模式覆盖

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`、`layout-patterns/master-detail-ops.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 领域正选布局 | `CicdRunDetail` 或 PipelineStageBar + LogStream + ArtifactTable 组合页模式；非 Kanban 冒充 CI/CD | PAT-07 · PAT-05 |
| 2 | Master-Detail | 运行列表→详情用 master-detail-ops；mobile 详情入 Drawer | PAT-03 · master-detail-ops.md |
| 3 | 阶段条布局 | 阶段条、日志流、制品表在同一页面模式内；间距密度与 golden 一致 | PAT-02 · MS-10 |
| 4 | 状态模式 | 阶段 active/成功/失败/等待审批态与 `state-index.md` 一致 | PAT-04 · INTER-07 |
| 5 | preview/golden | DevOps preview frame 注册 `golden-screens.md`；`workflow-ticket-reply.png` 可复现 | PAT-05 · PREVIEW-001 |

**交互动作**：打开 CicdRunDetail → 对照 MS-10 正选页面模式 → 切换阶段/日志态 → 对照 `workflow-ticket-reply.png`。

## PAT-08 — Gateway 控制平面 Hub 场景页面模式覆盖

**对照 golden**：`gateway-patterns`、`control-plane-hub`、`references/gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Hub 布局模式 | `ControlPlaneHub` 子面板在同一 Hub Tabs / 控制平面 layout 内；非散落 Card 拼凑 | PAT-08 · hub-tabs.md |
| 2 | 探测/配额区块 | `EndpointProbeTable`、`BalanceQuotaSummary` 在统一 PageHeader + grid 内 | PAT-02 · gateway-template.md |
| 3 | 部署/License 区块 | `DeploymentModeMatrix`、`LicenseIssuePanel` 有 layout pattern 登记 | PAT-03 · SOR-05 |
| 4 | Dialog 短表单 | 探测/License Dialog 走 form-dialog 短表单模式；非每页自建浮层布局 | PAT-03 · form-composition.md |
| 5 | 检索路由 | Gateway 任务 ≤3 跳：`domain-scenarios` → `gateway-template` → layout pattern | PAT-01 · RUN-04 |

**交互动作**：抽查 Gateway 页 3 个子面板 → 确认 Hub 布局与 `gateway-patterns` golden 一致 → 打开探测 Dialog。

## PAT-09 — PaaS 资源与危险操作场景页面模式覆盖

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 列表+详情布局 | `ResourceTable` + 可选 Maps 在同一 table-list / detail-page 模式内 | PAT-09 · PAT-02 |
| 2 | ConfigDiff 布局 | `ConfigDiff` / `DescriptionDiff` 在详情页或 Master-Detail 右栏；非每页自建 diff 区块 | PAT-03 · detail-page.md |
| 3 | 危险流程布局 | 恢复/伸缩 Dialog 与 `ops-danger-flow` 页面模式一致；destructive 区有 DangerZone 模式 | PAT-03 · form-composition.md |
| 4 | 容量/备份区块 | `CapacityCard`、`BackupTable` 在统一 KPI + 表格栅格内 | PAT-02 · MS-12 |
| 5 | example runtime | PaaS 场景有打开态截图；`paas-restore-dialog-open` / `paas-scale-dialog-open` 可复现 | PAT-05 · PREVIEW-* |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 展开 ConfigDiff → 对照 `paas-restore-dialog-open` golden。

## PAT-10 — MS 场景页面模式束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`、`domain-scenarios.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：`ControlPlaneHub` Hub 布局 + gateway layout；preview gateway-patterns | SOR-05 · PAT-08 |
| 2 | MS-10 | CI/CD：`cicd-release` + PipelineStageBar/LogStream 页面组合；preview devops-patterns | SOR-02 · PAT-07 |
| 3 | MS-11 | BI 联动：`bi-filter-linkage` + CrossFilterDashboard 完整页面；preview bi-filter-linkage | SOR-01 · PAT-06 |
| 4 | MS-12 | PaaS 资源：`paas-resource` + ResourceTable/Maps 页面组合；preview paas-patterns | SOR-03 · PAT-09 |
| 5 | MS-13 | 治理安全：Auth Wizard + PermissionMatrix + AuditLogTable 完整场景页；preview security-governance | SOR-04 · PAT-05 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景模式覆盖（G81）** 选型表 → 确认 PAT-01～10 在场景内页面模式组合满足。

## 五类场景模式覆盖速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | 缺 layout pattern、Chart 区孤立 Card、大屏占位画布 | `bi-filter-linkage.md` | PAT-06 · PAT-02 |
| DevOps | Kanban 冒充 CI/CD、缺 master-detail 或 pipeline 页面模式 | `master-detail-ops.md` | PAT-07 · PAT-05 |
| Gateway | 散落 mock Card、缺 Hub/控制平面 layout | `gateway-template.md` | PAT-08 · PAT-03 |
| PaaS | 扁平表硬塞地图、ConfigDiff 无详情页模式 | `detail-page.md` | PAT-09 · PAT-02 |
| MS 束 | 领域页缺完整 layout 或 preview 仅占位 | `domain-scenarios.md` | PAT-10 · VAL-* |

## 完整模式覆盖评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `pattern-coverage-review-checklist.md` | PAT-01～05 |
| 场景级 | 本文件 | PAT-06～10 |

完整模式覆盖评审 = **PAT-01～10**；PR 前至少抽检 PAT-01 + PAT-06 + 1 个 MS PAT-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_decision_matrix_from_preview.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级页面模式错选、layout pattern 缺失或 MS 场景只有孤立组件。
- route-index / pattern-index 缺相似路径登记，导致 Agent 无法 ≤3 跳定位场景 layout 文件。
- 状态模式（loading/empty/error/permission/dirty）在同类 MS 场景页面表现不一致。

症状 ID 对照：`upgrade-troubleshooting.md` 中 PAT-06（BI 场景）～ PAT-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 模式覆盖规则与封顶 | `quality-rubric.md` |
| 控件/页面级覆盖 | `pattern-coverage-review-checklist.md` |
| 模式索引 | `pattern-index.md` |
| 路由索引 | `route-index.md` |
| 状态矩阵 | `state-index.md` |
| 领域场景 | `domain-scenarios.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 场景食谱 | `scenario-override-recipes.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| Golden 对照 | `docs/spec/.../shards/golden-screens.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` PAT-* / VAL-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
