# 场景逻辑完备评审清单

> DOCS-035 / G84 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级产品逻辑完备抽检**，覆盖 BI 筛选联动与下钻因果链、DevOps 流水线阶段依赖与回滚闭环、Gateway 探测与配额审批、PaaS 资源筛选与危险操作审批及 MS 场景逻辑束，并与 `logic-completeness-review-checklist.md`（LOGIC-06～10）、`form-validation-logic-review-checklist.md`（LOGIC-01～05）、`layout-patterns/crud-flow.md`、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景逻辑抽检 | 对应 LOGIC 块 + `quality-rubric.md` 逻辑完备 |
| 大规模 Agent 生成后 MS 场景抽检 | LOGIC-01～05（表单）+ LOGIC-06～10（场景级）各抽 1 页 |
| BI 筛选 chips 无 KPI/图表因果反馈 | 先跑 LOGIC-06，再查 `layout-patterns/bi-filter-linkage.md` |
| CI/CD 阶段可跳步或 Rollback 无确认闭环 | LOGIC-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway probe 无分步结果或配额超限仍可提交 | LOGIC-08 + MS-09 `EndpointProbeTable` |
| PaaS 恢复/伸缩无审批或 ResourceTable 筛选与地图不一致 | LOGIC-09 + `templates/paas/ops-danger-flow.tsx` |
| MS 场景组合缺 probe/联动/审计业务闭环 | LOGIC-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `form-validation-logic-review-checklist.md` LOGIC-01～05（表单校验、危险操作、权限、向导、CRUD）。
2. 再完成 `logic-completeness-review-checklist.md` LOGIC-06～10（用户流程、筛选因果、主从上下文、审批配额、MS 束）的页面级抽检。
3. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
4. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
5. 筛选/查询/阶段/probe 变更必须可观察地影响结果区（表格/KPI/图表/日志），禁止 silent no-op。

## LOGIC-06 — BI / Data Screen 筛选联动与下钻因果

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`layout-patterns/bi-drill-down.md`、`templates/bi/cross-filter-dashboard.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 筛选→KPI | FilterBar chip 变更后 KPI 数值或趋势可观察更新；清除 chip 恢复 | LOGIC-06 · MS-11 |
| 2 | cross-filter | 图表点击/筛选 chips 联动表格或相邻图表；非单图 onClick 冒充 | LOGIC-07 · GEN-06 |
| 3 | 下钻面包屑 | DrillBreadcrumb 可返回上级；返回不丢全局筛选 | LOGIC-06 · PAT-02 |
| 4 | 空/错态因果 | 筛选无结果有中文空态 + 清除 CTA；失败有重试且保留筛选上下文 | LOGIC-07 · ASYNC-06 |
| 5 | example runtime | `bi-chart-state-gates.png` 可复现 legend/tooltip 与 data-state 因果链 | LOGIC-06 · PREVIEW-* |

**交互动作**：FilterBar 添加 chip → 观察 KPI/图表更新 → 触发下钻 → 面包屑返回 → 清除 chip → 对照 `bi-chart-state-gates.png`。

## LOGIC-07 — DevOps 流水线阶段依赖与回滚闭环

**对照 golden**：`cicd-run-detail`、`workflow-ticket-reply.png`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段依赖 | PipelineStageBar 未完成阶段不可跳步；active 阶段与日志/制品区同步 | LOGIC-07 · MS-10 |
| 2 | 日志/制品联动 | 阶段切换后 LogStream 与 ArtifactTable 内容因果更新 | LOGIC-08 · ASYNC-07 |
| 3 | Rollback 闭环 | Rollback Dialog 确认→checking→结果；取消不丢阶段上下文 | LOGIC-02 · LOGIC-09 |
| 4 | 审批流可见 | ApprovalTimeline pending/approved/rejected 可辨；超限不可提交 | LOGIC-09 · VAL-02 |
| 5 | example runtime | `workflow-ticket-reply.png` 可复现阶段切换与危险操作取消路径 | LOGIC-07 · PREVIEW-* |

**交互动作**：PipelineStageBar 切换阶段 → 观察日志/制品联动 → 触发 Rollback（取消）→ 检查审批流状态 → 对照 `workflow-ticket-reply.png`。

## LOGIC-08 — Gateway 探测与配额审批逻辑

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Probe 分步 | EndpointProbe 每步 loading→success/failed 可观察；结果可复制 | LOGIC-04 · ASYNC-08 |
| 2 | 配额因果 | BalanceQuota 超限 disabled 提交；用量变更影响 KPI 摘要 | LOGIC-09 · MS-09 |
| 3 | License 吊销 | License 吊销/过期有确认 Dialog + 结果态；非 silent 状态切换 | LOGIC-02 · LOGIC-09 |
| 4 | Hub 子面板 | ControlPlaneHub Tab 切换保留 probe/配额上下文；返回不丢筛选 | LOGIC-08 · PAT-03 |
| 5 | example runtime | Gateway golden `gateway-patterns` 可复现探测与配额摘要因果链 | LOGIC-08 · PREVIEW-* |

**交互动作**：EndpointProbeTable 触发 probe → 观察分步结果 → 模拟配额超限 → 切换 Hub Tab → 对照 `gateway-patterns` golden。

## LOGIC-09 — PaaS 资源筛选与危险操作审批

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 筛选→地图/表 | ResourceTable 筛选与 Maps/表格选中状态一致；清除恢复全量 | LOGIC-07 · MS-12 |
| 2 | ConfigDiff 因果 | ConfigDiff before/after 与选中资源对应；风险提示与变更字段对齐 | LOGIC-09 · PAT-02 |
| 3 | 恢复/伸缩审批 | 危险 Dialog 确认→checking→结果；取消不丢表格筛选 | LOGIC-02 · ASYNC-09 |
| 4 | Backup 恢复闭环 | 恢复确认→loading→结果；失败有重试且保留选中行 | LOGIC-09 · VAL-04 |
| 5 | example runtime | `paas-restore-dialog-open` / `paas-scale-dialog-open` 可复现审批与取消路径 | LOGIC-09 · PREVIEW-* |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 确认后取消 → 展开 ConfigDiff → 对照 `paas-restore-dialog-open` golden。

## LOGIC-10 — MS 场景业务逻辑束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：端点 probe 分步结果 + License 吊销确认 + 配额摘要因果链 | SOR-05 · VAL-01 |
| 2 | MS-10 | CI/CD：阶段依赖不可跳步 + Rollback 确认 + 日志流与制品表联动 | SOR-02 · VAL-02 |
| 3 | MS-11 | BI：筛选 chips→图表 cross-filter + 下钻面包屑可返回 | SOR-01 · VAL-03 |
| 4 | MS-12 | PaaS：ResourceTable 筛选→地图/表格一致 + 恢复/伸缩审批闭环 | SOR-03 · VAL-04 |
| 5 | MS-13 | 治理：PermissionMatrix 保存→审计刷新 + Auth Wizard probe 结果态 | SOR-04 · VAL-05 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景逻辑完备（G84）** 选型表 → 确认 LOGIC-01～10 在场景内组合满足。

## 五类场景逻辑速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | 筛选 silent no-op、下钻返回丢筛选、cross-filter 断裂 | `bi-filter-linkage.md` | LOGIC-06 · VAL-03 |
| DevOps | 阶段可跳步、Rollback 无确认、日志与阶段不同步 | `devops-template.md` | LOGIC-07 · VAL-02 |
| Gateway | probe 无分步、配额超限仍可提交、Hub Tab 丢上下文 | `gateway-template.md` | LOGIC-08 · VAL-01 |
| PaaS | 筛选与地图不一致、危险操作无审批、ConfigDiff 不对齐 | `paas-template.md` | LOGIC-09 · LOGIC-02 |
| MS 束 | 领域页缺 probe/审批/联动/审计闭环 | `business-validation-checklist.md` | LOGIC-10 · VAL-* |

## 完整逻辑完备评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 表单校验、危险操作、权限、向导、CRUD | `form-validation-logic-review-checklist.md` | LOGIC-01～05 |
| 用户流程、筛选因果、主从上下文、审批配额 | `logic-completeness-review-checklist.md` | LOGIC-06～10（页面级） |
| 场景级 | 本文件 | LOGIC-06～10（领域场景） |

完整逻辑完备评审 = **LOGIC-01～10**；PR 前至少抽检 LOGIC-01 + LOGIC-06（场景级）+ 1 个 MS LOGIC-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
# 业务仓库：导航/筛选/主从/审批逻辑抽检
rg -n "FilterBar|PipelineStageBar|EndpointProbe|ResourceTable|PermissionMatrix" src/
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级筛选 silent no-op、阶段可跳步、probe 无分步结果或危险操作无审批闭环。
- MS 场景组合缺少可观察因果链（如 BI cross-filter 无反馈、流水线阶段与日志不同步）。
- 检索路径超过 3 跳才找到本清单或对应 LOGIC 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 LOGIC-06（BI 场景）～ LOGIC-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 表单校验与 CRUD | `form-validation-logic-review-checklist.md` |
| 页面级产品逻辑 | `logic-completeness-review-checklist.md` |
| CRUD 与列表流 | `layout-patterns/crud-flow.md` |
| 主从与 Hub 布局 | `layout-patterns/master-detail-ops.md` |
| BI 筛选联动 | `layout-patterns/bi-filter-linkage.md` |
| 状态与异步 | `scene-async-state-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` LOGIC-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
