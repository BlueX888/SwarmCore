# 场景类型完整与 API 契约评审清单

> DOCS-033 / G82 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级 TypeScript 类型与公开 API 契约抽检**，覆盖 BI 筛选与图表组合受控类型、DevOps 流水线阶段与日志流式 props、Gateway 控制平面 Hub 子面板契约、PaaS 资源与危险操作类型边界及 MS 场景类型束，并与 `type-api-contract-review-checklist.md`（TYPE-01～05）、`api-contracts.md`、`extension-audit.md`、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景类型契约抽检 | 对应 TYPE 块 + `quality-rubric.md` 类型完整规则 |
| 大规模 Agent 生成后 MS 场景抽检 | TYPE-01～05（控件/页面级）+ TYPE-06～10（场景级）各抽 1 页 |
| BI 页 Chart override 编译报错或 chips 类型断裂 | 先跑 TYPE-06，再查 `api-override-recipes.md` |
| CI/CD 页 stages 受控类型与 LogStream 流式 props 不匹配 | TYPE-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway 子面板 props 与 `api-contracts.md` 不一致 | TYPE-08 + MS-09 `ControlPlaneHub` |
| PaaS ResourceTable row type 或 Maps override 类型丢失 | TYPE-09 + `templates/paas/resource-table.tsx` |
| MS 场景组合缺类型化受控 props 或 `tsc` 报错 | TYPE-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `type-api-contract-review-checklist.md` TYPE-01～05（props 导出、theme helper 签名、复杂受控契约、additive 变更、MS 组合类型）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
4. 业务代码必须能通过 `tsc --noEmit`；禁止 `any` 或 `@ts-ignore` 掩盖场景级 props 漂移。
5. 场景页子面板必须使用文档列出的受控 props 类型；硬编码 mock 且无类型出口不得计为场景完整类型覆盖。

## TYPE-06 — BI / Data Screen 场景类型契约覆盖

**对照 reference**：`api-contracts.md`、`api-override-recipes.md`、`layout-patterns/bi-filter-linkage.md`、`extension-audit.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 筛选 chips 受控类型 | `FilterBar` chips `value`/`onChange` 与维度模型类型一致；非 `string[]` 裸数组混用 | TYPE-06 · TYPE-03 |
| 2 | Chart override 签名 | `getBaseChartOptions(overrides?)` 在 BI 场景传入 `series`/`colors` 深嵌套不丢类型 | TYPE-02 · MER-02 |
| 3 | 联动仪表盘 props | `CrossFilterDashboard`/`DrillDownDashboard` filter state 与 chart props 类型联动闭合 | TYPE-03 · TYPE-05 |
| 4 | 大屏/指标面板 | KPI/指标面板 props 有显式 interface；`metric-definition-panel` 与数据模型对齐 | TYPE-01 · api-contracts |
| 5 | example runtime | BI 场景 `tsc --noEmit` 通过；`bi-chart-state-gates.png` 对应 runtime 状态类型可推断 | TYPE-05 · PREVIEW-* |

**交互动作**：打开 BI 筛选页 → 传入 `getBaseChartOptions({ series: [...] })` → 切换 FilterBar chips → `tsc --noEmit` → 对照 `bi-chart-state-gates.png`。

## TYPE-07 — DevOps 流水线阶段与日志场景类型契约覆盖

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`、`api-contracts.md`、`extension-audit.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段条受控类型 | `PipelineStageBar` `stages: StageData[]` + `activeStageId`/`onStageChange` 成对且类型完整 | TYPE-07 · TYPE-03 |
| 2 | 日志流式 props | `LogStreamPanel` `lines`/`onLoadMore`/`status` 与流式数据模型类型闭合 | TYPE-03 · MS-10 |
| 3 | 制品/审批 props | `ArtifactTable` row type + `ApprovalTimeline` step id 类型与 `api-contracts.md` 一致 | TYPE-01 · TYPE-05 |
| 4 | 页面组合类型 | `CicdRunDetail` 子面板 props 受控；组合页 `tsc --noEmit` 无 props 缺失 | TYPE-05 · SEL-02 |
| 5 | 危险/回滚契约 | `RollbackDialog`/`DangerZone` 回调签名与 destructive flow 数据模型一致 | TYPE-03 · LOGIC-02 |

**交互动作**：打开 CicdRunDetail → 切换 `stages` 受控 prop → 触发 LogStream loading → `tsc --noEmit` → 对照 `workflow-ticket-reply.png`。

## TYPE-08 — Gateway 端点探测与配额场景类型契约覆盖

**对照 golden**：`gateway-patterns`、`control-plane-hub`、`references/gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Hub 子面板受控 props | `ControlPlaneHub` 各子面板 props 与 `api-contracts.md` Gateway 表一致；禁止内部 mock 无类型出口 | TYPE-08 · TYPE-03 |
| 2 | 探测回调签名 | `EndpointProbeTable` `onProbe(endpointId)` 返回类型与 probe 结果模型一致 | TYPE-03 · MS-09 |
| 3 | 配额/License props | `BalanceQuotaSummary`、`LicenseIssuePanel` 数值/状态 props 有显式联合类型 | TYPE-01 · SOR-05 |
| 4 | 部署矩阵类型 | `DeploymentModeMatrix` row/column id 为 `string`；`onSelect` 返回完整模式快照 | TYPE-03 · api-contracts |
| 5 | example runtime | Gateway 场景组合页 `tsc --noEmit` 通过；探测 Dialog 打开态 props 可推断 | TYPE-05 · PREVIEW-* |

**交互动作**：抽查 Gateway 页 3 个子面板 → 触发 `onProbe` → 打开探测 Dialog → `tsc --noEmit` → 对照 `gateway-patterns` golden。

## TYPE-09 — PaaS 资源与危险操作场景类型契约覆盖

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 资源表 row type | `ResourceTable` `rows: ResourceRow[]` + 筛选/排序回调参数类型与 `api-contracts.md` 一致 | TYPE-09 · TYPE-03 |
| 2 | Maps override 类型 | `mergeMapLibreOptions`/`mergeLeafletOptions` `center`/`zoom` override 类型不丢失 | TYPE-02 · MER-01 |
| 3 | ConfigDiff props | `ConfigDiff`/`DescriptionDiff` before/after 字段类型与详情页数据模型对齐 | TYPE-01 · TYPE-05 |
| 4 | 危险流程回调 | 恢复/伸缩 Dialog `onConfirm`/`onCancel` 与 `ops-danger-flow` 风险模型类型一致 | TYPE-03 · LOGIC-02 |
| 5 | example runtime | PaaS 场景 `tsc --noEmit` 通过；`paas-restore-dialog-open` 打开态 props 可推断 | TYPE-05 · PREVIEW-* |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 展开 ConfigDiff → `tsc --noEmit` → 对照 `paas-restore-dialog-open` golden。

## TYPE-10 — MS 场景类型契约束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：`ControlPlaneHub` 子面板受控 props + `onProbe` 类型与 `gateway-template.md` 一致 | SOR-05 · TYPE-08 |
| 2 | MS-10 | CI/CD：`PipelineStageBar` stages + `LogStreamPanel` 流式 props 类型闭合 | SOR-02 · TYPE-07 |
| 3 | MS-11 | BI：`FilterBar` chips + `getBaseChartOptions(overrides?)` + CrossFilter filter 类型联动 | SOR-01 · TYPE-06 |
| 4 | MS-12 | PaaS：`ResourceTable` row type + Maps override + ConfigDiff 类型齐全 | SOR-03 · TYPE-09 |
| 5 | MS-13 | 治理：`PermissionMatrix` `onChange` 快照 + `AuthProviderWizard` 分步 data 类型与保存回调对齐 | SOR-04 · TYPE-05 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景类型完整（G82）** 选型表 → 确认 TYPE-01～10 在场景内类型契约满足 → `audit_compat_contracts.py` exit 0。

## 五类场景类型契约速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | Chart override 编译报错、chips 受控类型断裂 | `api-override-recipes.md` | TYPE-06 · TYPE-02 |
| DevOps | stages 受控 props 与 LogStream 流式类型不匹配 | `api-contracts.md` DevOps 表 | TYPE-07 · TYPE-03 |
| Gateway | Hub 子面板 props 与模板契约不一致 | `gateway-template.md` | TYPE-08 · TYPE-03 |
| PaaS | ResourceTable row type 或 Maps override 类型丢失 | `api-contracts.md` PaaS 表 | TYPE-09 · TYPE-02 |
| MS 束 | 场景页 props 与模板默认不一致、`tsc` 报错 | `business-validation-checklist.md` | TYPE-10 · VAL-* |

## 完整类型契约评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `type-api-contract-review-checklist.md` | TYPE-01～05 |
| 场景级 | 本文件 | TYPE-06～10 |

完整类型契约评审 = **TYPE-01～10**；PR 前至少抽检 TYPE-01 + TYPE-06 + 1 个 MS TYPE-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
pnpm exec tsc --noEmit
rg -n "@ts-ignore|as any" src/
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级 props 重命名、受控契约断裂或 theme helper 签名漂移。
- MS 场景组合缺少类型化受控 props，导致业务只能硬编码 mock 或依赖 `any`。
- 检索路径超过 3 跳才找到本清单或 `api-contracts.md` 对应块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 TYPE-06（BI 场景）～ TYPE-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 类型完整规则与封顶 | `quality-rubric.md` |
| 控件/页面级契约 | `type-api-contract-review-checklist.md` |
| 公开 API 注册表 | `api-contracts.md` |
| 扩展性降级 | `extension-audit.md` |
| Override 食谱 | `api-override-recipes.md` |
| 领域场景 | `domain-scenarios.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 场景食谱 | `scenario-override-recipes.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| Golden 对照 | `docs/spec/.../shards/golden-screens.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` TYPE-* / VAL-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
