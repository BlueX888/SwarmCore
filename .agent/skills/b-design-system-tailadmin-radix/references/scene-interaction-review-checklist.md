# 场景交互与动效评审清单

> DOCS-023 / G72 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级交互与动效抽检**，覆盖 BI 大屏实时反馈、DevOps 流水线阶段、Gateway 探测与配额、PaaS 危险操作与 MS 场景交互束，并与 `interaction-motion-review-checklist.md`（INTER-01～05）、`interaction-motion.md`、`state-index.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景交互抽检 | 对应 INTER 块 + `quality-rubric.md` 交互与动效质量 |
| 大规模 Agent 生成后 MS 场景抽检 | INTER-01～05（控件级）+ INTER-06～10（场景级）各抽 1 页 |
| BI 大屏 KPI/图表刷新无过渡 | 先跑 INTER-06，再查 `layout-patterns/bi-data-screen.md` |
| CI/CD 阶段条/日志流无 active 反馈 | INTER-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway 端点 probe 分步无动效 | INTER-08 + MS-09 `EndpointProbeTable` |
| PaaS 恢复/伸缩确认无过渡 | INTER-09 + `templates/paas/ops-danger-flow.tsx` |
| MS 场景组合缺 observable 交互路径 | INTER-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `interaction-motion-review-checklist.md` INTER-01～05（控件级 hover/focus/浮层/loading/微交互）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
4. 场景级状态迁移（probe 分步、阶段切换、配额告警、审批 pending）须有 **150–300ms 可见过渡**，禁止瞬时硬切。
5. 开启 `prefers-reduced-motion: reduce` 时，场景动画应降级为 opacity/颜色变化，禁止强制 bounce 或无限循环位移。

## INTER-06 — BI / Data Screen 实时与刷新动效

**对照 reference**：`layout-patterns/bi-data-screen.md`、`templates/bi/data-screen-canvas.tsx`、`interaction-motion.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | KPI 刷新 | 指标更新有数字过渡或 Skeleton→内容切换；非空白闪烁 | INTER-06 · ASYNC-01 |
| 2 | 图表联动 | cross-filter 或筛选后 chart highlight/tooltip 跟随有过渡提示 | INTER-05 · MS-11 |
| 3 | 告警/阈值 | 超阈值 KPI 或告警条有颜色/图标 pulse（≤2s 周期）；不遮挡阅读 | INTER-06 · VIS-05 |
| 4 | 大屏画布 | 多区块布局有 stagger 入场或区块 loading 占位；非空容器假柱状条 | INTER-06 · RESP-05 |
| 5 | 自动轮播/刷新 | 定时刷新有 loading 指示；手动暂停/恢复可观察 | ASYNC-05 · MS-11 |

**交互动作**：FilterBar 添加 chip → 观察 KPI/图表联动过渡 → 模拟阈值告警态 → 切换 light/dark 各 1 次。

## INTER-07 — DevOps 流水线阶段与日志流动效

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段条 active | 当前阶段有 active/highlight 过渡；已完成/失败态可辨 | INTER-07 · MS-10 |
| 2 | 阶段切换 | 点击或受控切换阶段时指示器滑动/颜色过渡 ~150ms | INTER-07 · VAL-02 |
| 3 | 日志流 | LogStream 尾部新行有淡入或 auto-scroll；loading 有尾部 Spinner | INTER-04 · MS-10 |
| 4 | 制品/审批 | ArtifactTable 行 hover + ApprovalTimeline pending→approved 有过渡 | INTER-05 · LOGIC-09 |
| 5 | Rollback 确认 | Rollback Dialog 打开 fade+scale；确认后阶段条回退有过渡 | INTER-02 · LOGIC-02 |

**交互动作**：PipelineStageBar 切换阶段 → 观察 LogStream 滚动与 loading → 打开 Rollback Dialog → Esc 关闭。

## INTER-08 — Gateway 端点探测与配额面板动效

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Probe 分步 | 端点探测 loading→success/failed 有逐步结果过渡；非整表硬切 | INTER-08 · LOGIC-04 |
| 2 | 配额摘要 | BalanceQuota 用量条填充有过渡；超限态颜色/图标变化可辨 | INTER-08 · MS-09 |
| 3 | License 状态 | 吊销/过期 badge 有过渡；主操作 disabled 有过渡 opacity | INTER-01 · LOGIC-09 |
| 4 | 同步健康 | SyncHealth 面板状态切换（healthy/degraded）有图标/颜色过渡 | INTER-08 · ASYNC-04 |
| 5 | 探测 Dialog | 打开态 fade+scale；结果复制/关闭路径完整 | INTER-02 · VAL-01 |

**交互动作**：EndpointProbeTable 触发 probe → 观察分步 loading→结果 → 模拟配额超限 disabled → 打开探测 Dialog。

## INTER-09 — PaaS 危险操作与恢复流程动效

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 恢复/伸缩 Dialog | 危险操作 Dialog 打开 fade+scale；确认按钮 destructive hover 可辨 | INTER-02 · LOGIC-02 |
| 2 | ConfigDiff | 变更高亮行有过渡；展开/折叠 diff 区块不撑破布局 | INTER-09 · MS-12 |
| 3 | ResourceTable | 行选中/hover + 地图/表格联动 highlight 有过渡 | INTER-05 · MS-12 |
| 4 | Backup 恢复 | 恢复确认→loading→结果态有 Spinner + 文案过渡 | INTER-04 · ASYNC-03 |
| 5 | 容量卡片 | CapacityCard 用量条/Replica 变化有过渡；partial 区块 loading 不拖垮栅格 | INTER-04 · ASYNC-04 |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 确认 loading → 观察 ConfigDiff 高亮 → 关闭 Dialog。

## INTER-10 — MS 场景交互与动效束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：probe 分步过渡 + 配额条填充 + 探测 Dialog fade+scale | SOR-05 · INTER-08 |
| 2 | MS-10 | CI/CD：阶段 active 过渡 + LogStream 尾部 loading + Rollback Dialog | SOR-02 · INTER-07 |
| 3 | MS-11 | BI：筛选 chip 增删过渡 + chart cross-filter tooltip + KPI 刷新 | SOR-01 · INTER-06 |
| 4 | MS-12 | PaaS：表格行 hover + 恢复/伸缩 Dialog + ConfigDiff 高亮 | SOR-03 · INTER-09 |
| 5 | MS-13 | 治理：矩阵勾选过渡 + Wizard 步骤切换 + AuditLog 搜索 loading | SOR-04 · INTER-03 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景交互与动效（G72）** 选型表 → 确认 INTER-01～10 在场景内组合满足。

## 五类场景交互速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | KPI 硬切、假占位、告警无反馈 | `bi-data-screen.md` | INTER-06 · RESP-05 |
| DevOps | 阶段无 active、日志无滚动反馈 | `devops-template.md` | INTER-07 · VAL-02 |
| Gateway | probe 整表硬切、配额条无过渡 | `gateway-template.md` | INTER-08 · VAL-01 |
| PaaS | 危险 Dialog 无过渡、diff 高亮缺失 | `paas-template.md` | INTER-09 · LOGIC-02 |
| MS 束 | 领域页只有 happy path 无场景动效 | `business-validation-checklist.md` | INTER-10 · DRIFT-02 |

## 完整交互评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | `interaction-motion-review-checklist.md` | INTER-01～05 |
| 场景级 | 本文件 | INTER-06～10 |

完整交互与动效评审 = **INTER-01～10**；PR 前至少抽检 INTER-01 + INTER-06 + 1 个 MS INTER-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库：Playwright 场景交互/打开态截图
pnpm exec playwright test --grep scene-interaction
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的 BI 大屏假占位、流水线阶段无 active、probe 整表硬切或 PaaS 危险 Dialog 无过渡。
- MS 场景组合缺少 observable 场景级交互路径（如 MS-10 阶段切换无过渡、MS-11 筛选无 chart 联动反馈）。
- 检索路径超过 3 跳才找到本清单或 INTER-06～10 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 INTER-06（BI/大屏）～ INTER-10（MS 场景束）；与 VAL-*、LOGIC-*、DRIFT-02 交叉引用。

## 检索入口

| 意图 | 读 |
|---|---|
| 控件级 hover/focus/浮层 | `interaction-motion-review-checklist.md` |
| 时长/缓动/禁止项 | `interaction-motion.md` |
| BI 大屏布局 | `layout-patterns/bi-data-screen.md` |
| DevOps 流水线 | `references/component-styles/devops-template.md` |
| Gateway 控制平面 | `references/component-styles/gateway-template.md` |
| PaaS 资源操作 | `references/component-styles/paas-template.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` INTER-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
