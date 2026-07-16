# 逻辑完备评审清单

> DOCS-022 / G71 产物。对 Agent 生成或人工改写的业务页面执行**可复现产品逻辑完备抽检**，覆盖用户流程导航、筛选因果链、主从上下文、审批配额规则与 MS 场景业务逻辑束，并与 `form-validation-logic-review-checklist.md`（LOGIC-01～05）、`layout-patterns/crud-flow.md`、`pattern-coverage-review-checklist.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前产品逻辑抽检 | 对应 LOGIC 块 + `quality-rubric.md` 逻辑完备 |
| 大规模 Agent 生成后抽检 | LOGIC-01～05（表单）+ LOGIC-06～10（产品逻辑）各抽 1 页 |
| 列表筛选无结果或筛选丢失 | 先跑 LOGIC-07，再查 `async-state-review-checklist.md#async-02` |
| 详情返回丢筛选/分页 | LOGIC-08 + `layout-patterns/master-detail-ops.md` |
| 审批/配额/限制无反馈 | LOGIC-09 + `decision-matrix.md#治理安全` |
| MS 场景业务路径不完整 | LOGIC-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `form-validation-logic-review-checklist.md` LOGIC-01～05（表单校验、危险操作、权限、向导、CRUD）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
3. 抽检至少 **1 个列表/主从页 + 1 个 MS-09～13 场景组合页**。
4. 筛选/查询变更必须可观察地影响结果区（表格/KPI/图表），禁止 silent no-op。
5. 返回/面包屑/Tab 切换须保留可解释的业务上下文（筛选、选中行、分页）。

## LOGIC-06 — 用户流程与导航闭环

**对照 reference**：`layout-patterns/crud-flow.md`、`references/route-index.md`、`pattern-coverage-review-checklist.md#pat-02`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 列表→详情→返回 | 行点击/编辑进入详情；返回保留列表筛选与分页 | LOGIC-06 · PAT-02 |
| 2 | 面包屑/标题 | 详情/编辑页有面包屑或上下文标题（中文领域名） | COPY-03 · PAT-02 |
| 3 | 新建入口 | 列表页有明确「新建」主操作；成功后回到列表或详情 | LOGIC-05 · `crud-flow.md` |
| 4 | 深链/刷新 | URL 含 id/tab 参数时刷新不 404；状态可从 URL 恢复（可选） | PAT-04 · ASYNC-02 |
| 5 | 空路由兜底 | 未知路由有 404 或重定向；侧栏 active 与当前路由一致 | PAT-01 · GEN-01 |

**交互动作**：列表页筛选 → 进入详情 → 浏览器返回 → 确认筛选与页码仍在。

## LOGIC-07 — 筛选查询与结果因果链

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`templates/bi/filter-bar.tsx`、`state-index.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 筛选→结果 | 筛选 chips/搜索/日期变更后表格或 KPI 有 loading→刷新反馈 | LOGIC-07 · ASYNC-02 |
| 2 | 清除筛选 | 「清除全部」恢复默认结果；chip 可单独移除 | MS-11 · `filter-bar.tsx` |
| 3 | 无结果态 | 筛选无匹配时有中文空态 + 清除筛选 CTA | ASYNC-01 · COPY-02 |
| 4 | 跨组件联动 | BI/仪表盘筛选驱动多图/KPI 同步（cross-filter 因果可见） | MS-11 · LOGIC-05 |
| 5 | 防抖/防重 | 搜索输入 debounce；连续提交筛选不堆叠重复请求 | ASYNC-03 |

**交互动作**：FilterBar 添加 chip → 观察图表/表格变化 → 清除 chip → 结果恢复。

## LOGIC-08 — Master-Detail 与上下文保留

**对照 reference**：`layout-patterns/master-detail-ops.md`、`layout-patterns/hub-tabs.md`、`async-state-review-checklist.md#async-02`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 选中态 | 列表选中行高亮；切换选中时详情区 loading→内容 | LOGIC-08 · PAT-03 |
| 2 | 详情 Tab | 详情内多 Tab（概览/日志/配置）切换不丢列表选中 | PAT-03 · MS-10 |
| 3 | 分页保留 | 翻页后返回上一页或详情关闭，列表页码/排序保留 | ASYNC-02 |
| 4 | 并行编辑 | Master-Detail 编辑中切换选中行需 dirty 确认或自动保存策略 | LOGIC-05 · `form-dialog.tsx` |
| 5 | 移动降级 | `< lg` 详情入 Drawer/全屏；关闭 Drawer 回到列表上下文 | RESP-04 · MS-12 |

**交互动作**：Master-Detail 选中行 → 详情 Tab 切换 → 列表翻页 → 再选中其他行 → 检查上下文提示。

## LOGIC-09 — 审批配额与业务限制规则

**对照 reference**：`templates/devops/approval-timeline.tsx`、`templates/gateway/balance-quota-summary.tsx`、`decision-matrix.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 配额可见 | 余额/配额/用量 KPI 或摘要区可读；超限有中文说明 | MS-09 · VAL-01 |
| 2 | 审批流 | 发布/变更/危险操作有审批时间线或 pending 态 | MS-10 · `approval-timeline.tsx` |
| 3 | 限制门禁 | 超配额/无 License 时主操作 disabled + 原因说明 | LOGIC-03 · MS-09 |
| 4 | 状态迁移 | queued→running→success/failed 有明确视觉与文案 | ASYNC-04 · MS-10 |
| 5 | 业务规则 | 领域规则（如备份保留期、伸缩上下限）在表单 helper 或确认 Dialog 说明 | LOGIC-02 · MS-12 |

**交互动作**：Gateway 配额摘要 → 模拟超限 disabled → CI/CD 审批时间线查看 pending/approved 态。

## LOGIC-10 — MS 场景业务逻辑束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：端点 probe 分步结果 + License 吊销确认 + 配额摘要因果链 | SOR-05 · VAL-01 |
| 2 | MS-10 | CI/CD：阶段依赖不可跳步 + Rollback 确认 + 日志流与制品表联动 | SOR-02 · VAL-02 |
| 3 | MS-11 | BI：筛选 chips→图表 cross-filter + 下钻面包屑可返回 | SOR-01 · VAL-03 |
| 4 | MS-12 | PaaS：ResourceTable 筛选→地图/表格一致 + 恢复/伸缩审批闭环 | SOR-03 · VAL-04 |
| 5 | MS-13 | 治理：PermissionMatrix 保存→审计刷新 + Auth Wizard probe 结果态 | SOR-04 · VAL-05 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **逻辑完备（G65/G71）** 列 → 确认 LOGIC-01～10 在场景内组合满足。

## 五类产品逻辑速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 导航闭环 | 返回丢筛选、无新建入口、面包屑缺失 | `crud-flow.md` | LOGIC-06 · PAT-02 |
| 筛选因果 | 筛选无反馈、清除无效、联动断裂 | `bi-filter-linkage.md` | LOGIC-07 · ASYNC-02 |
| 主从上下文 | 切换选中丢 Tab、翻页丢详情 | `master-detail-ops.md` | LOGIC-08 · PAT-03 |
| 审批配额 | 超限仍可提交、审批流不可见 | `approval-timeline.tsx` | LOGIC-09 · VAL-* |
| MS 场景 | 领域页缺 probe/审批/联动/审计闭环 | `decision-matrix.md` MS 表 | LOGIC-10 · VAL-* |

## 与表单逻辑清单的关系

| 范围 | 清单 | 块 ID |
|---|---|---|
| 表单校验、危险操作、权限、向导、CRUD | `form-validation-logic-review-checklist.md` | LOGIC-01～05 |
| 用户流程、筛选因果、主从上下文、审批配额、MS 束 | 本文件 | LOGIC-06～10 |
| 领域场景级 BI/DevOps/Gateway/PaaS/MS 逻辑束 | `scene-logic-completeness-review-checklist.md` | LOGIC-06～10 |

完整逻辑完备评审 = **LOGIC-01～10**；PR 前至少抽检 LOGIC-01 + LOGIC-06 + 1 个 MS LOGIC-10 场景。MS 领域场景页另按 `scene-logic-completeness-review-checklist.md` 抽检。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库：导航/筛选/主从逻辑抽检
rg -n "breadcrumb|FilterBar|MasterDetail|ApprovalTimeline|BalanceQuota" src/
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的筛选 silent no-op、返回丢上下文、审批流不可见或 MS 场景缺业务闭环。
- `crud-flow.md` / `master-detail-ops.md` 未覆盖的新产品逻辑模式。
- 检索路径超过 3 跳才找到本清单或 LOGIC-06～10 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 LOGIC-06（导航）～ LOGIC-10（MS 场景）；与 PAT-*、ASYNC-*、VAL-* 交叉引用。

## 检索入口

| 意图 | 读 |
|---|---|
| 表单校验与 CRUD | `form-validation-logic-review-checklist.md` |
| CRUD 与列表流 | `layout-patterns/crud-flow.md` |
| 主从与 Hub 布局 | `layout-patterns/master-detail-ops.md` |
| BI 筛选联动 | `layout-patterns/bi-filter-linkage.md` |
| 状态与异步 | `async-state-review-checklist.md` |
| 模式覆盖 | `pattern-coverage-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` LOGIC-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
