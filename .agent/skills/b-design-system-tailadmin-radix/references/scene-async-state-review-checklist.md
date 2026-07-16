# 场景异步状态与韧性评审清单

> DOCS-025 / G74 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级异步状态与韧性抽检**，覆盖 BI 大屏刷新与 cross-filter、DevOps 流水线阶段与日志流、Gateway 探测与配额、PaaS 危险操作与恢复及 MS 场景异步束，并与 `async-state-review-checklist.md`（ASYNC-01～05）、`state-index.md`、`prd/F02-data-state.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景异步抽检 | 对应 ASYNC 块 + `quality-rubric.md` 逻辑完备 |
| 大规模 Agent 生成后 MS 场景抽检 | ASYNC-01～05（控件/页面级）+ ASYNC-06～10（场景级）各抽 1 页 |
| BI 大屏筛选后 KPI/图表静默无反馈 | 先跑 ASYNC-06，再查 `layout-patterns/bi-filter-linkage.md` |
| CI/CD 阶段切换与日志流不同步 | ASYNC-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway 端点 probe 无分步 loading | ASYNC-08 + MS-09 `EndpointProbeTable` |
| PaaS 恢复/伸缩确认无提交 loading | ASYNC-09 + `templates/paas/ops-danger-flow.tsx` |
| MS 场景组合缺 observable 异步路径 | ASYNC-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `async-state-review-checklist.md` ASYNC-01～05（页面级 loading/empty/error、表格、表单、局部失败、重组件降级）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
4. 场景级状态迁移（筛选联动、阶段切换、probe 分步、危险操作提交）须有 **可观察 loading→success/error 路径**，禁止 silent no-op。
5. 用户可见 loading/empty/error/retry 文案默认中文；技术缩写（API、CI/CD、K8s、P95）可保留。

## ASYNC-06 — BI / Data Screen 刷新与 cross-filter 异步

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`templates/bi/cross-filter-dashboard.tsx`、`templates/bi/filter-bar.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 筛选→KPI | FilterBar chip 变更后 KPI 有 Skeleton 或 loading 指示，再刷新内容 | ASYNC-06 · MS-11 |
| 2 | cross-filter | 图表/表格联动有 loading 或高亮过渡，非整页硬切 | ASYNC-02 · INTER-06 |
| 3 | 空/错态 | 筛选无结果有中文空态 + 清除 CTA；数据失败有重试 | ASYNC-01 · COPY-02 |
| 4 | 图表 lazy | ApexCharts runtime 有占位；失败有降级文案，非白屏 | ASYNC-05 · SSR-02 |
| 5 | 自动刷新 | 定时刷新有 loading 指示；手动暂停/恢复可观察 | ASYNC-05 · MS-11 |

**交互动作**：FilterBar 添加 chip → 观察 KPI/图表 loading→刷新 → 模拟 empty/error → 点击重试 → 对照 `bi-chart-state-gates.png`。

## ASYNC-07 — DevOps 流水线阶段与日志流异步

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段切换 | PipelineStageBar 切换阶段时日志/制品区有 loading→内容 | ASYNC-07 · MS-10 |
| 2 | 日志流 | LogStream 尾部新行加载有 Spinner 或淡入；error 有重试 | ASYNC-05 · INTER-07 |
| 3 | 制品/审批 | ArtifactTable 翻页/筛选有表级 loading；审批 pending→approved 可辨 | ASYNC-02 · LOGIC-09 |
| 4 | Rollback | Rollback Dialog 提交有 checking/loading；失败有中文错误 + 重试 | ASYNC-03 · LOGIC-02 |
| 5 | 局部失败 | 单面板（日志/制品）失败不拖垮全页；其余区块仍可读 | ASYNC-04 · MS-10 |

**交互动作**：PipelineStageBar 切换阶段 → 观察 LogStream loading → 触发 Rollback → 模拟单面板 error → 点重试。

## ASYNC-08 — Gateway 端点探测与配额异步

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Probe 分步 | EndpointProbe 每步 loading→success/failed 可观察；非整表硬切 | ASYNC-08 · LOGIC-04 |
| 2 | 配额刷新 | BalanceQuota 用量更新有 loading 或数字过渡；超限态可辨 | ASYNC-08 · MS-09 |
| 3 | License 同步 | License 状态刷新有 loading；吊销/过期有中文说明 | ASYNC-04 · LOGIC-09 |
| 4 | 同步健康 | SyncHealth healthy/degraded 切换有 loading 或状态过渡 | ASYNC-08 · INTER-08 |
| 5 | 探测 Dialog | 探测结果提交/复制有 loading；失败有重试路径 | ASYNC-03 · VAL-01 |

**交互动作**：EndpointProbeTable 触发 probe → 观察分步 loading→结果 → 模拟配额超限 disabled → 对照 `ecommerce-crud-live-gates.png` 同类 live gates 模式。

## ASYNC-09 — PaaS 危险操作与恢复流程异步

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 恢复/伸缩 | 危险 Dialog 确认后有 checking/loading；成功/失败态可辨 | ASYNC-09 · MS-12 |
| 2 | ResourceTable | 列表筛选/翻页有 loading；空态与筛选无结果区分 | ASYNC-02 · INTER-09 |
| 3 | ConfigDiff | diff 加载有 Skeleton；展开失败有 inline 错误 | ASYNC-04 · MS-12 |
| 4 | Backup 恢复 | 恢复确认→loading→结果有 Spinner + 中文文案过渡 | ASYNC-03 · LOGIC-02 |
| 5 | Capacity 卡片 | 用量/Replica 刷新有局部 loading；partial 不拖垮 2×2 栅格 | ASYNC-04 · ASYNC-05 |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 确认 loading → 模拟失败重试 → 观察 Capacity 局部 loading。

## ASYNC-10 — MS 场景异步韧性束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：probe 分步 loading + 配额刷新 + License 状态迁移 | SOR-05 · ASYNC-08 |
| 2 | MS-10 | CI/CD：阶段切换日志 loading + Rollback 提交态 + 局部 retry | SOR-02 · ASYNC-07 |
| 3 | MS-11 | BI：筛选→KPI/chart 联动 loading + empty/error + chart lazy | SOR-01 · ASYNC-06 |
| 4 | MS-12 | PaaS：恢复 Dialog loading + ResourceTable 翻页态 + Capacity partial | SOR-03 · ASYNC-09 |
| 5 | MS-13 | 治理：PermissionMatrix 提交 loading + Wizard 步骤 async + AuditLog 刷新 | SOR-04 · ASYNC-03 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景异步状态（G74）** 选型表 → 确认 ASYNC-01～10 在场景内组合满足。

## 五类场景异步状态速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | 筛选后 KPI 硬切、chart 白屏、无 empty/error | `bi-filter-linkage.md` | ASYNC-06 · VAL-03 |
| DevOps | 阶段切换日志不同步、Rollback 无双提交防护 | `devops-template.md` | ASYNC-07 · VAL-02 |
| Gateway | probe 整表硬切、配额刷新无反馈 | `gateway-template.md` | ASYNC-08 · VAL-01 |
| PaaS | 危险操作无 checking、恢复无 loading | `paas-template.md` | ASYNC-09 · LOGIC-02 |
| MS 束 | 领域页缺 observable loading→success 路径 | `business-validation-checklist.md` | ASYNC-10 · DRIFT-03 |

## 完整异步状态评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `async-state-review-checklist.md` | ASYNC-01～05 |
| 场景级 | 本文件 | ASYNC-06～10 |

完整异步状态与韧性评审 = **ASYNC-01～10**；PR 前至少抽检 ASYNC-01 + ASYNC-06 + 1 个 MS ASYNC-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
# 业务仓库：模拟慢网/失败 API
pnpm exec playwright test --grep scene-async-state
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级静默失败、probe 无分步 loading 或危险操作无双提交防护。
- MS 场景组合缺少 observable 异步路径（如 BI cross-filter 无 loading、流水线阶段切换日志不同步）。
- 检索路径超过 3 跳才找到本清单或对应 ASYNC 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 ASYNC-06（BI 场景）～ ASYNC-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 状态矩阵与 Token | `state-index.md` |
| DataTable 契约 | `prd/F02-data-state.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 场景交互与动效 | `scene-interaction-review-checklist.md` |
| 场景视觉 Token | `scene-visual-token-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 重组件降级 | `extension-audit.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` ASYNC-* / VAL-* / RUN-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
