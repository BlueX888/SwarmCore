# 场景组件覆盖率评审清单

> DOCS-031 / G80 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级组件覆盖率抽检**，覆盖 BI 大屏筛选与图表组合模板、DevOps 流水线阶段与日志、Gateway 端点探测与配额、PaaS 危险操作与 ConfigDiff 及 MS 场景组件覆盖率束，并与 `component-coverage-review-checklist.md`（COV-01～05）、`component-index.md`、`extension-audit.md`、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景组件覆盖率抽检 | 对应 COV 块 + `quality-rubric.md` 组件覆盖率规则 |
| 大规模 Agent 生成后 MS 场景抽检 | COV-01～05（控件/页面级）+ COV-06～10（场景级）各抽 1 页 |
| BI 页散落 Card 拼凑或缺 `templates/bi/*` 组合 | 先跑 COV-06，再查 `layout-patterns/bi-filter-linkage.md` |
| CI/CD 页误用 Kanban 或缺 DevOps 领域模板 | COV-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway 子面板仅 CSS mock 无 `templates/gateway/*` | COV-08 + MS-09 `ControlPlaneHub` |
| PaaS 列表缺 ResourceTable/ConfigDiff 可复制模板 | COV-09 + `templates/paas/resource-table.tsx` |
| MS 场景组合缺领域 `templates/*/` 或 preview 缺口 | COV-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `component-coverage-review-checklist.md` COV-01～05（主路径模板、extension-audit、preview/golden、变体矩阵、MS 组合模板）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
4. 14 项复杂组件在场景内使用时必须对照 `extension-audit.md`；`partial` 状态不得计为场景完整覆盖。
5. 场景页所用组件必须在 `component-index.md` 登记可复制 `templates/` 路径；无 preview/example runtime 的主路径模板组件覆盖率最高 92。

## COV-06 — BI / Data Screen 场景组件覆盖

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`templates/bi/cross-filter-dashboard.tsx`、`templates/bi/filter-bar.tsx`、`extension-audit.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 筛选组合模板 | `FilterBar` + `CrossFilterDashboard`/`DrillDownDashboard` 有 `templates/bi/*` 可复制入口 | COV-06 · COV-05 |
| 2 | 图表模板 | Chart 走 `templates/bi/*` + `chartPaletteCssVars`；extension-audit Chart 14/14 无 partial | COV-02 · COV-06 |
| 3 | KPI/指标面板 | `metric-definition-panel` 或 KPI Card 有模板路径；preview 文案指向 `templates/...` | COV-01 · COV-03 |
| 4 | 大屏画布 | Data Screen 使用 `data-screen-canvas` 或多区块布局模板；非空容器假柱状条 | COV-04 · BI-005 |
| 5 | example runtime | BI 场景有 example section + 打开态截图；`bi-chart-state-gates.png` 可复现 | COV-03 · PREVIEW-* |

**交互动作**：打开 BI 筛选页 → 对照 `component-index.md` 抽 3 个 BI 组件 → 确认 `templates/bi/*` 路径存在且 preview/example 文案指向该路径 → 对照 `bi-chart-state-gates.png`。

## COV-07 — DevOps 流水线阶段与日志场景组件覆盖

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`、`component-styles/devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 领域正选模板 | `PipelineStageBar` + `LogStreamPanel` + `ArtifactTable` 有 `templates/devops/*` 可复制入口 | COV-07 · COV-05 |
| 2 | 危险/回滚组件 | `RollbackDialog`、`DangerZone`、`DiffViewer` 有模板且 component-index 登记 when/when-not | COV-01 · COV-02 |
| 3 | 页面组合 | `CicdRunDetail` 或等效组合页引用领域模板；非 Kanban 冒充 CI/CD | COV-05 · SEL-02 |
| 4 | preview/golden | DevOps preview frame 注册 `golden-screens.md`；阶段/日志打开态截图存在 | COV-03 · PREVIEW-001 |
| 5 | 检索路由 | DevOps 任务 ≤3 跳：`domain-scenarios` → `devops-template` → `templates/devops/*` | COV-01 · RUN-04 |

**交互动作**：打开 CicdRunDetail → 抽 3 个 DevOps 组件 → 确认 `templates/devops/*` 路径与 preview 文案一致 → 对照 `workflow-ticket-reply.png`。

## COV-08 — Gateway 端点探测与配额场景组件覆盖

**对照 golden**：`gateway-patterns`、`control-plane-hub`、`references/gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Hub 组合模板 | `ControlPlaneHub` 子面板均有 `templates/gateway/*` 可复制入口 | COV-08 · COV-05 |
| 2 | 探测/配额组件 | `EndpointProbeTable`、`BalanceQuotaSummary`、`ApiKeyRevealPanel` 有模板且索引登记 | COV-01 · COV-02 |
| 3 | 部署/License | `DeploymentModeMatrix`、`LicenseIssuePanel`、`SyncHealthPanel` 有领域模板 | COV-01 · SOR-05 |
| 4 | preview/golden | gateway-patterns frame 注册 golden；探测 Dialog 打开态截图存在 | COV-03 · PREVIEW-* |
| 5 | 非 mock 拼凑 | 场景页引用领域模板组合；非散落 Card 无 `templates/` 路径 | COV-05 · GEN-08 |

**交互动作**：抽查 Gateway 页 3 个子面板 → 确认各子面板 `templates/gateway/*` 路径 → 打开探测 Dialog → 对照 `gateway-patterns` golden。

## COV-09 — PaaS 资源与危险操作场景组件覆盖

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 列表+地图模板 | `ResourceTable` + 可选 Maps 有 `templates/paas/*`；Maps 走 extension-audit + theme lib | COV-02 · COV-09 |
| 2 | ConfigDiff | `ConfigDiff` / `DescriptionDiff` 有模板；同类 PaaS 页 diff 组件路径一致 | COV-01 · COV-06 |
| 3 | 危险流程 | 恢复/伸缩 Dialog 与 `ops-danger-flow` 模板一致；非每页自建 destructive | COV-01 · INTER-09 |
| 4 | 容量/备份 | `CapacityCard`、`BackupTable` 有 `templates/paas/*` 且 preview 文案指向路径 | COV-03 · MS-12 |
| 5 | example runtime | PaaS 场景有打开态截图；`paas-restore-dialog-open` / `paas-scale-dialog-open` 可复现 | COV-03 · PREVIEW-* |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 展开 ConfigDiff → 对照 `component-index.md` 确认 `templates/paas/*` 路径 → 对照 `paas-restore-dialog-open` golden。

## COV-10 — MS 场景组件覆盖率束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：`ControlPlaneHub` + 探测表 + 配额面板 + License 均有 `templates/gateway/*` | SOR-05 · COV-08 |
| 2 | MS-10 | CI/CD：`PipelineStageBar` + `LogStreamPanel` + `ArtifactTable` 组合模板齐全 | SOR-02 · COV-07 |
| 3 | MS-11 | BI：`FilterBar` + `CrossFilterDashboard` + Chart theme 模板路径一致 | SOR-01 · COV-06 |
| 4 | MS-12 | PaaS：`ResourceTable` + 可选 Maps + 危险 Dialog + ConfigDiff 模板齐全 | SOR-03 · COV-09 |
| 5 | MS-13 | 治理：`PermissionMatrix` + `AuditLogTable` + Auth Wizard `templates/governance/*` | SOR-04 · COV-01 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景组件覆盖率（G80）** 选型表 → 确认 COV-01～10 在场景内组合满足。

## 五类场景组件覆盖速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | 缺 `templates/bi/*`、Chart 仅 CSS mock、大屏占位画布 | `bi-filter-linkage.md` | COV-06 · COV-02 |
| DevOps | Kanban 冒充 CI/CD、缺 `templates/devops/*` 组合 | `devops-template.md` | COV-07 · COV-05 |
| Gateway | 散落 mock Card、缺 `templates/gateway/*` 子面板 | `gateway-template.md` | COV-08 · COV-01 |
| PaaS | 扁平表硬塞地图、ConfigDiff 无模板路径 | `paas-template.md` | COV-09 · COV-02 |
| MS 束 | 领域页缺 `templates/*/` 组合或 preview 缺口 | `business-validation-checklist.md` | COV-10 · VAL-* |

## 完整组件覆盖率评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `component-coverage-review-checklist.md` | COV-01～05 |
| 场景级 | 本文件 | COV-06～10 |

完整组件覆盖率评审 = **COV-01～10**；PR 前至少抽检 COV-01 + COV-06 + 1 个 MS COV-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级主路径组件缺模板、extension-audit partial 未清零或 preview/example runtime 缺口。
- MS 场景组合缺少领域 `templates/*/` 目录模板，导致 Agent 每次用散落 Card 拼凑。
- 检索路径超过 3 跳才找到本清单或对应 COV 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 COV-06（BI 场景）～ COV-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 组件覆盖率规则与封顶 | `quality-rubric.md` |
| 控件/页面级覆盖 | `component-coverage-review-checklist.md` |
| 组件索引 | `component-index.md` |
| 扩展性审计 | `extension-audit.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 场景食谱 | `scenario-override-recipes.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| Golden 对照 | `docs/spec/.../shards/golden-screens.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` COV-* / PREVIEW-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
