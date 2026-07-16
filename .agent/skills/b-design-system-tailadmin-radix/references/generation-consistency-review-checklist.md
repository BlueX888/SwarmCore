# 生成一致性评审清单

> DOCS-018 / G67 产物。对 Agent 生成或人工改写的业务页面执行**可复现生成一致性抽检**，覆盖组件/页面选型、Token 与密度、状态矩阵、检索路由与 MS 场景组合，并与 `decision-matrix.md`、`agent-retrieval-guide.md`、`token-index.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前生成一致性抽检 | 对应 GEN 块 + `quality-rubric.md` 生成一致性 |
| 大规模 Agent 生成后 MS 场景抽检 | GEN-01～05 各抽 1 页 + GEN-06～10 各抽 1 页 |
| 同类页面组件选择不一致 | 先跑 GEN-01，再查 `decision-matrix.md` |
| Token/间距/密度漂移 | GEN-02 + `visual-token-review-checklist.md` |
| 状态控件表现不一致 | GEN-03 + `state-index.md` |
| Agent 检索路径过长或错路由 | GEN-04 + `agent-retrieval-guide.md` |
| MS 场景组合与模板契约不一致 | GEN-05 + `business-validation-checklist.md` |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
2. 抽检至少 **1 个原子组件页 + 1 个 MS-09～13 场景组合页**。
3. 组件/页面不确定时**必须先读** `decision-matrix.md`，禁止无矩阵依据的随机组合。
4. 图标语义不确定时**必须先读** `icon-system.md`；禁止无理由 lucide 替换 TailAdmin SVG。
5. 同类任务检索路径应 **≤3 跳**；超过 3 跳须写回 `agent-retrieval-guide.md`。

## GEN-01 — 组件与页面选型一致性

**对照 reference**：`decision-matrix.md`、`component-index.md`、`pattern-index.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 矩阵正选 | 表单/表格/浮层/场景页与 decision-matrix 正选一致；无 SEL-* 误选 | SEL-* · DRIFT-03 |
| 2 | when-not | 新增组件有「什么时候用 / 不什么时候用」；错选已写回矩阵 | decision-matrix |
| 3 | 浮层基座 | Dialog/Dropdown/Popover 走 Radix/shadcn；非手写 div 浮层 | DRIFT-02 |
| 4 | 领域模板 | DevOps/网关/PaaS/BI/治理页使用对应 `templates/*/` 组合，非散落 Card 拼凑 | MS-09～13 |
| 5 | 图标选型 | 语义图标先查 `icon-system.md`；尺寸 `size-4`/`size-5`/`size-6` 一致 | A11Y-04 |

**交互动作**：打开 MS-10 CicdRunDetail 与 MS-13 PermissionMatrix → 对照 decision-matrix **生成一致性（G67）** 列 → 确认无 Kanban/Switch 列表误选。

## GEN-02 — Token 与视觉密度一致性

**对照 reference**：`token-index.md`、`visual-language.md`、`visual-token-review-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 语义色 | 主操作/状态/边框使用 `brand-*`/`success-*`/`error-*`；无页面内 hex 默认色 | VIS-01 |
| 2 | 间距密度 | 面板 `p-5`/`p-6`、表格 `py-4`、KPI 栅格与 golden 一致 | VIS-03 |
| 3 | 圆角阴影 | 面板 `rounded-xl`、Dialog `rounded-3xl`、浮层 `z-99999` 层级统一 | VIS-04 |
| 4 | dark 对比 | light/dark 同一页面结构下 Token 映射一致；边框层级不丢失 | VIS-02 |
| 5 | 数字排版 | KPI/表格数字 `tabular-nums` + `font-semibold`；Chart 走 `chartPaletteCssVars` | VIS-05 |

**交互动作**：Overview KPI 与 MS-11 CrossFilterDashboard → 切换 light/dark → 对比 `golden-screens.md` 密度与色板。

## GEN-03 — 状态矩阵与交互模式一致性

**对照 reference**：`state-index.md`、`interaction-motion.md`、`interaction-motion-review-checklist.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 布尔控件 | Switch/Checkbox/Radio 同一产品内尺寸、标签对齐、checked/disabled/error 一致 | INTER-03 |
| 2 | 加载态 | 按钮 loading、表级 Skeleton、页面 QueryShell 模式与 `state-index.md` 一致 | ASYNC-01 · INTER-04 |
| 3 | 空/错态 | empty/error/retry 文案与布局与 `prd/F02-data-state.md` 一致 | COPY-02 · ASYNC-02 |
| 4 | 浮层过渡 | Dialog/Dropdown/Drawer 开关过渡 150–200ms；Esc 可关闭 | INTER-02 |
| 5 | hover/focus | 主按钮/菜单项 hover 与 `focus-visible:ring-*` 在全站一致 | INTER-01 · A11Y-01 |

**交互动作**：Form Controls 矩阵与 DataTable 筛选栏 → 切换 loading/disabled/error → 对比同类页面状态表现。

## GEN-04 — Agent 检索与生成路由一致性

**对照 reference**：`agent-retrieval-guide.md`、`run_token_hit_tests.py`（T01–T20）

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 任务路由 | 同类任务（表单/BI/DevOps/迁移）走 agent-retrieval 路由表 ≤3 跳 | RUN-04 |
| 2 | 先矩阵后模板 | 不确定组件时先 `decision-matrix.md` 再 `component-index.md` | SEL-* |
| 3 | Token 命中 | T01–T20 检索路径 100% 命中；无歧义路由 | token-metrics |
| 4 | 误路由纠正 | 常见误路由表覆盖 BI/Kanban/RBAC/网关等；有新误路由写回 | agent-retrieval-guide |
| 5 | 升级症状 | 升级后先 `upgrade-troubleshooting.md` 症状 ID，再 playbook/SOR | RUN-01～04 |

**交互动作**：模拟 3 个任务（BI 联动、CI/CD 详情、RBAC 矩阵）→ 按路由表计数跳数 ≤3 → 跑 `run_token_hit_tests.py`。

## GEN-05 — MS 场景组合生成一致性

**对照 reference**：`business-validation-checklist.md`、`scenario-override-recipes.md`、`decision-matrix.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | `ControlPlaneHub` 子面板受控 props；非散落 mock Card | SEL-05 · VAL-01 |
| 2 | MS-10 | `PipelineStageBar` + `LogStreamPanel` + `ArtifactTable` 组合；非纯 Kanban | SEL-02 · VAL-02 |
| 3 | MS-11 | `FilterBar` chips + `CrossFilterDashboard` 联动；非单图 onClick | SEL-01 · VAL-03 |
| 4 | MS-12 | `ResourceTable` + 可选 Maps 同一地理语义；非扁平表硬塞地图 | SEL-03 · VAL-04 |
| 5 | MS-13 | `PermissionMatrix` + `AuditLogTable` + Auth Wizard；非 Switch 列表 | SEL-04 · VAL-05 |

**交互动作**：按 MS 表各抽 1 个组合页 → 对照 decision-matrix **生成一致性（G67）** 列 → 完成受控 props 切换与组合交互。

## 五类生成一致性速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 选型漂移 | Kanban 冒充 CI/CD、Switch 冒充 RBAC | `decision-matrix.md` | GEN-01 · SEL-* |
| Token/密度漂移 | 硬编码色、KPI 栅格过疏/过挤 | `token-index.md` | GEN-02 · VIS-* |
| 状态不一致 | 同类 loading/empty 表现不同 | `state-index.md` | GEN-03 · ASYNC-* |
| 检索过长 | Agent 扫描整个 templates/ 目录 | `agent-retrieval-guide.md` | GEN-04 · RUN-04 |
| MS 组合漂移 | 场景页与模板契约/受控 props 不一致 | `business-validation-checklist.md` | GEN-05 · VAL-* |
| 场景组合漂移 | BI/DevOps/Gateway/PaaS 领域页模板组合不一致 | `scene-generation-consistency-review-checklist.md` | GEN-06～10 · SEL-* |

## 完整生成一致性评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | 本文件 | GEN-01～05 |
| 场景级 | `scene-generation-consistency-review-checklist.md` | GEN-06～10 |

完整生成一致性评审 = **GEN-01～10**；PR 前至少抽检 GEN-01 + GEN-06 + 1 个 MS GEN-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/run_token_hit_tests.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_decision_matrix_from_preview.py b-design-system-tailadmin-radix
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的组件错选、页面错选或同类页面 Token/状态表现不一致。
- MS 场景组合缺少受控 props 或模板引用，导致 Agent 每次生成结果不同。
- 检索路径超过 3 跳才找到本清单或 `decision-matrix.md` 对应块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 GEN-01（选型）～ GEN-05（MS 组合）、GEN-06～10（场景级）；与 SEL-*、DRIFT-03、RUN-04 交叉引用。

## 交叉引用

| 主题 | 文件 |
|---|---|
| 选型矩阵 | `decision-matrix.md` |
| 检索路由 | `agent-retrieval-guide.md` |
| 生成一致性规则 | `quality-rubric.md` |
| UI 漂移对照 | `ui-drift-review-checklist.md` |
| 视觉 Token | `visual-token-review-checklist.md` |
| 业务冒烟 | `business-validation-checklist.md` |
| 升级症状 | `upgrade-troubleshooting.md` |
| 场景生成一致性 | `scene-generation-consistency-review-checklist.md` |
| Golden 对照 | `docs/spec/.../shards/golden-screens.md` |
