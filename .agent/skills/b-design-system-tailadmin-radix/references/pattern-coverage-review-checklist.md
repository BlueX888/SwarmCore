# 模式覆盖评审清单

> DOCS-020 / G69 产物。对 Agent 生成或人工改写的业务页面执行**可复现模式覆盖抽检**，覆盖 output modes、页面/布局模式、状态模式、路由检索与 MS 场景页面组合，并与 `pattern-index.md`、`route-index.md`、`state-index.md`、`decision-matrix.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前模式覆盖抽检 | 对应 PAT 块 + `quality-rubric.md` 模式覆盖 |
| 从 0 搭建新应用或新页面 | PAT-01 + PAT-02 + `output-modes/from-zero.md` |
| 迁移/重构已有 UI | PAT-01 + PAT-03 + `output-modes/migration.md` |
| 缺组件开发后验收 | PAT-01 + `output-modes/missing-component.md` |
| 页面模式选错或只有孤立组件 | PAT-02 + PAT-03 + `pattern-index.md` |
| 状态模式不完整（仅 happy path） | PAT-04 + `state-index.md` |
| MS-09～13 场景缺完整页面组合 | PAT-05 + `domain-scenarios.md` |

## 通用前置

1. 页面级任务**必须先读** `route-index.md` → `pattern-index.md` → 对应 `layout-patterns/` 文件。
2. 抽检至少 **1 个通用页面模式（dashboard/table-list/form-flow）+ 1 个 MS-09～13 场景组合页**。
3. 禁止只有孤立组件、无页面级 layout pattern 或 output mode 指引的「半成品页面」。
4. 状态模式必须覆盖 loading、empty、error 中适用项；权限/只读/危险操作不得省略。
5. preview 场景页必须体现完整页面组合，不能只有占位 Card 或假数据堆叠。

## PAT-01 — Output modes 与生命周期模式

**对照 reference**：`output-modes/from-zero.md`、`output-modes/migration.md`、`output-modes/missing-component.md`、`ui-drift-review-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 从 0 构建 | 新应用/页面按 from-zero 读取顺序：Token → 壳层 → pattern → 组件 | from-zero.md |
| 2 | 迁移模式 | migration 含 preserve/adapt/replace/deprecate 判断 + playbook 路由 | migration-playbook.md |
| 3 | 缺组件协议 | missing-component 同步 component-index、detail、preview、when/when-not | missing-component.md |
| 4 | 评审模式 | UI 漂移评审走 REV-01～05 + golden screens 对照 | ui-drift-review-checklist.md |
| 5 | 演化闭环 | 发现模式缺口写回 PRD/plan/state，而非只修局部页面 | sop.md |

**交互动作**：打开 `output-modes/from-zero.md` → 对照一个新页面任务 → 确认读取顺序 ≤3 跳且指向 pattern-index。

## PAT-02 — 页面模式与路由索引

**对照 reference**：`route-index.md`、`pattern-index.md`、`layout-patterns/dashboard.md`、`table-list.md`、`form-flow.md`、`detail-page.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 路由对照 | 新页面在 `route-index.md` 有相似路径或明确新增登记 | route-index.md |
| 2 | 核心页面 | dashboard、table-list、form-flow、detail、settings/auth 有 layout pattern | pattern-index.md |
| 3 | 决策树 | 页面选型走 pattern-index 决策树，非随机 Card 堆叠 | decision-matrix.md |
| 4 | AppLayout | 后台页在 AppLayout 内：PageHeader + 主内容 grid/stack | dashboard.md |
| 5 | 领域入口 | SaaS/企业/政府/PaaS/DevOps 先读 `domain-scenarios.md` 再选 pattern | domain-scenarios.md |

**交互动作**：抽 1 个 table-list 页 + 1 个 dashboard 页 → 对照 route-index 与 layout-patterns 文件路径存在。

## PAT-03 — 布局组合与高级页面模式

**对照 reference**：`layout-patterns/form-composition.md`、`hub-tabs.md`、`master-detail-ops.md`、`three-column-workspace.md`、`activation-wizard.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 表单组合 | 简单/复杂/Drawer/Dialog 短表单/描述列表有 form-composition 指引 | form-composition.md |
| 2 | Hub Tabs | 设置/配额/用量类页用 HubTabsLayout + `?tab=` 路由 | hub-tabs.md |
| 3 | Master-Detail | 列表+详情用 master-detail-ops；mobile 详情入 Drawer | master-detail-ops.md |
| 4 | 三栏工作区 | 仓库/资源树+编辑器用 three-column-workspace | three-column-workspace.md |
| 5 | 向导模式 | 部署/接入/激活用 activation-wizard 或 auth-provider-wizard | activation-wizard.md |

**交互动作**：Hub Tabs 设置页 + Master-Detail 运维页 → 确认 layout pattern 文件与 preview scenario frame 一致。

## PAT-04 — 状态模式与数据流

**对照 reference**：`state-index.md`、`component-styles/content-state-contract.md`、`async-state-review-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 加载态 | QueryShell/DataTableCard 有 Skeleton；按钮提交有 loading | ASYNC-01 |
| 2 | 空态/错误 | empty、error、retry、partial 与真 empty 区分；中文 CTA | ASYNC-02 · COPY-02 |
| 3 | 权限/只读 | RBAC 页用 PermissionMatrix + disabled tooltip；非 Switch 列表 | LOGIC-03 |
| 4 | 脏表单 | Drawer/Dialog 表单 dirty 关闭有确认；wizard 分步局部校验 | LOGIC-04 · LOGIC-05 |
| 5 | 批量操作 | 表格 bulk action、筛选无结果、翻页不丢选中态 | DATA-001 · ASYNC-02 |

**交互动作**：DataTable 加载→空态→错误 retry + FormDialog dirty 关闭 → 对照 state-index 状态矩阵。

## PAT-05 — MS 场景页面模式与领域组合

**对照 reference**：`scenario-override-recipes.md`、`domain-scenarios.md`、`business-validation-checklist.md`、`decision-matrix.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关/控制平面：`ControlPlaneHub` + gateway layout；preview gateway-patterns | SOR-05 · VAL-01 |
| 2 | MS-10 | CI/CD：`cicd-release` + PipelineStageBar/LogStream；preview devops-patterns | SOR-02 · VAL-02 |
| 3 | MS-11 | BI 联动：`bi-filter-linkage` + CrossFilterDashboard；preview bi-filter-linkage | SOR-01 · VAL-03 |
| 4 | MS-12 | PaaS 资源：`paas-resource` + ResourceTable/Maps；preview paas-patterns | SOR-03 · VAL-04 |
| 5 | MS-13 | 治理安全：Auth Wizard + PermissionMatrix + AuditLogTable；preview security-governance | SOR-04 · VAL-05 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **模式覆盖（G69）** 列 → 确认 layout pattern + 领域模板组合完整。

## 五类模式覆盖速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 缺 output mode | 任务类型不明，Agent 随机扫描 templates/ | `output-modes/` | PAT-01 |
| 页面模式错选 | dashboard 任务用了 table-list 或孤立 Card | `pattern-index.md` | PAT-02 |
| 布局组合缺失 | 设置页无 Hub Tabs、列表详情同屏挤压 | `form-composition.md` | PAT-03 |
| 状态模式不足 | 只有 happy path，无 loading/empty/error | `state-index.md` | PAT-04 |
| 场景页不完整 | MS 页缺领域 layout 或 preview 仅占位 | `domain-scenarios.md` | PAT-05 |

## 完整模式覆盖评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | 本文件 | PAT-01～05 |
| 场景级 | `scene-pattern-coverage-review-checklist.md` | PAT-06～10 |

完整模式覆盖评审 = **PAT-01～10**；PR 前至少抽检 PAT-01 + PAT-06 + 1 个 MS PAT-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_decision_matrix_from_preview.py b-design-system-tailadmin-radix
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的页面模式错选、layout pattern 缺失或 MS 场景只有孤立组件。
- route-index / pattern-index 缺相似路径登记，导致 Agent 无法 ≤3 跳定位模式文件。
- 状态模式（loading/empty/error/permission/dirty）在同类页面表现不一致。

症状 ID 对照：`upgrade-troubleshooting.md` 中 PAT-01（output modes）～ PAT-05（MS 场景）、PAT-06～10（场景级）；与 SEL-*、REV-*、VAL-* 交叉引用。

## 交叉引用

| 主题 | 文件 |
|---|---|
| 模式索引 | `pattern-index.md` |
| 路由索引 | `route-index.md` |
| 状态矩阵 | `state-index.md` |
| 领域场景 | `domain-scenarios.md` |
| 选型矩阵 | `decision-matrix.md` |
| 场景食谱 | `scenario-override-recipes.md` |
| 业务冒烟 | `business-validation-checklist.md` |
| 组件覆盖率 | `component-coverage-review-checklist.md` |
| 场景页面模式 | `scene-pattern-coverage-review-checklist.md` |
| 升级症状 | `upgrade-troubleshooting.md` |
| Golden 对照 | `docs/spec/.../shards/golden-screens.md` |
