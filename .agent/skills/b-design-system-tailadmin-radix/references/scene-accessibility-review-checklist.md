# 场景可访问性评审清单

> DOCS-026 / G75 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级可访问性抽检**，覆盖 BI 大屏筛选与图表键盘可达、DevOps 流水线阶段与日志读屏、Gateway 探测 Dialog 与表格行操作、PaaS 危险操作与 ConfigDiff 语义及 MS 场景可访问性束，并与 `accessibility-review-checklist.md`（A11Y-01～05）、`engineering-guards.md`、`state-index.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景 a11y 抽检 | 对应 A11Y 块 + `quality-rubric.md` 约束遵守 |
| 大规模 Agent 生成后 MS 场景抽检 | A11Y-01～05（控件/页面级）+ A11Y-06～10（场景级）各抽 1 页 |
| BI 筛选 chip 无法键盘清除或图表区无降级可读 | 先跑 A11Y-06，再查 `layout-patterns/bi-filter-linkage.md` |
| CI/CD 阶段条键盘不可达或 LogStream 无 aria-live | A11Y-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway 端点探测 Dialog 无标题或行操作无名称 | A11Y-08 + MS-09 `EndpointProbeTable` |
| PaaS 地图 iframe 无 title 或危险 Dialog 焦点不回 | A11Y-09 + `templates/paas/ops-danger-flow.tsx` |
| MS 场景组合 RBAC 仅用 Switch 无矩阵语义 | A11Y-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `accessibility-review-checklist.md` A11Y-01～05（键盘、标签、浮层、图标命名、对比度与动态）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
4. 场景级主路径必须能用键盘完成一次核心任务；浮层打开后焦点在浮层内且 Esc/关闭可回焦。
5. 用户可见标签、按钮、错误文案默认中文；技术缩写（API、CI/CD、K8s、P95）可保留。

## A11Y-06 — BI / Data Screen 筛选与图表可访问性

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`templates/bi/cross-filter-dashboard.tsx`、`templates/bi/filter-bar.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | FilterBar 键盘 | chip 添加/清除可用键盘触发；清除按钮有可读名称 | A11Y-06 · MS-11 |
| 2 | 图表降级 | Chart lazy 失败有中文降级文案 + `aria-live` 或区域标题，非白屏 | A11Y-05 · ASYNC-05 |
| 3 | KPI 读屏 | KPI 数值与趋势有可见标签或 `aria-labelledby`；数字 tabular-nums 不裁切 | A11Y-02 · VIS-06 |
| 4 | cross-filter | 筛选联动后焦点不丢失；tooltip/legend 切换不困在图表子树 | A11Y-01 · INTER-06 |
| 5 | Dark 对比 | 筛选 chip 选中态与图表轴/网格在 dark 下可读 | A11Y-05 · VIS-02 |

**交互动作**：键盘 Tab 到 FilterBar → 添加/清除 chip → 观察 KPI/图表区焦点与读屏标签 → 切换 light/dark → 对照 `bi-chart-state-gates.png`。

## A11Y-07 — DevOps 流水线阶段与日志可访问性

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段条键盘 | PipelineStageBar 各阶段可用键盘激活；active 态有 focus-visible | A11Y-07 · MS-10 |
| 2 | LogStream 动态 | 日志尾部新行有 `aria-live="polite"` 或区域标题；loading 可读 | A11Y-05 · ASYNC-07 |
| 3 | Rollback Dialog | 确认 Dialog 有 `DialogTitle`；提交 checking 有 `aria-busy` 或状态文案 | A11Y-03 · LOGIC-02 |
| 4 | 制品行操作 | ArtifactTable 行内 icon-only 操作有中文 `aria-label` | A11Y-04 · MS-10 |
| 5 | Danger Zone | 危险区块操作按钮有可读名称；disabled 态可辨 | A11Y-02 · VIS-07 |

**交互动作**：键盘切换 PipelineStageBar 阶段 → 观察 LogStream loading 反馈 → 键盘打开 Rollback Dialog → Tab 循环 → Esc 关闭回焦。

## A11Y-08 — Gateway 端点探测与配额可访问性

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Probe Dialog | 端点探测 Dialog 有标题 + 关闭按钮可键盘聚焦 | A11Y-08 · MS-09 |
| 2 | 分步结果 | Probe 分步 loading→success/failed 有 badge 文本或 `aria-label` | A11Y-08 · LOGIC-04 |
| 3 | 表格行操作 | EndpointProbeTable 行操作 icon 有「探测」「复制」等中文名称 | A11Y-04 · MS-09 |
| 4 | 配额超限 | BalanceQuota 超限时主操作 disabled + 可读说明 | A11Y-02 · ASYNC-08 |
| 5 | License 状态 | 有效/过期/吊销 badge 有文本；不仅靠颜色区分 | A11Y-05 · VIS-08 |

**交互动作**：键盘打开探测 Dialog → 触发 probe → 检查分步结果读屏 → 模拟配额超限 disabled → 对照 `gateway-patterns` golden。

## A11Y-09 — PaaS 危险操作与 ConfigDiff 可访问性

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 地图 iframe | Maps/Vector 嵌入有 `title` 或 `aria-label` 描述地理语义 | A11Y-09 · MS-12 |
| 2 | 危险 Dialog | 恢复/伸缩 Dialog 有标题；destructive 按钮有可读名称 | A11Y-03 · INTER-09 |
| 3 | ConfigDiff | diff 展开区块有标题；变更行不仅靠背景色区分 | A11Y-02 · VIS-09 |
| 4 | ResourceTable | 行选中态有 `aria-selected` 或可见高亮 + 行操作标签 | A11Y-04 · INTER-09 |
| 5 | Wizard 步骤 | 多步恢复流程每步有 Label；步骤指示可读 | A11Y-02 · MS-13 |

**交互动作**：ResourceTable 键盘选中行 → 打开恢复 Dialog → Tab 到确认按钮 → 检查 ConfigDiff 展开标题 → 对照 `complex-form-drawer-guard.png` 焦点模式。

## A11Y-10 — MS 场景可访问性束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：探测 Dialog 标题 + 表格行操作 aria-label + 配额超限说明 | SOR-05 · A11Y-08 |
| 2 | MS-10 | CI/CD：阶段条键盘可达 + LogStream aria-live + Rollback Dialog 标题 | SOR-02 · A11Y-07 |
| 3 | MS-11 | BI：FilterBar chip 键盘清除 + 图表降级可读 + KPI 标签 | SOR-01 · A11Y-06 |
| 4 | MS-12 | PaaS：地图 title + 危险 Dialog 焦点陷阱 + ResourceTable 行操作 | SOR-03 · A11Y-09 |
| 5 | MS-13 | 治理：PermissionMatrix 非纯 Switch + Wizard Label + AuditLog 表格键盘 | SOR-04 · A11Y-02 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景可访问性（G75）** 选型表 → 确认 A11Y-01～10 在场景内组合满足。

## 五类场景可访问性速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | chip 无法键盘清除、图表白屏无降级、KPI 无标签 | `bi-filter-linkage.md` | A11Y-06 · VAL-03 |
| DevOps | 阶段条不可键盘激活、日志无 live 区域、Rollback 无标题 | `devops-template.md` | A11Y-07 · VAL-02 |
| Gateway | 探测 Dialog 无标题、行操作无名称 | `gateway-template.md` | A11Y-08 · VAL-01 |
| PaaS | 地图无 title、危险 Dialog 焦点不回 | `paas-template.md` | A11Y-09 · LOGIC-02 |
| MS 束 | 领域页 RBAC 仅 Switch、Wizard 无 Label | `business-validation-checklist.md` | A11Y-10 · DRIFT-03 |

## 完整可访问性评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `accessibility-review-checklist.md` | A11Y-01～05 |
| 场景级 | 本文件 | A11Y-06～10 |

完整可访问性评审 = **A11Y-01～10**；PR 前至少抽检 A11Y-01 + A11Y-06 + 1 个 MS A11Y-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
# 业务仓库：键盘遍历与读屏抽检
pnpm exec playwright test --grep scene-accessibility
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级无标签图标按钮、无标题 Dialog 或键盘不可达主路径。
- MS 场景组合存在可访问性反模式（如 RBAC 仅用 Switch 无矩阵语义、地图 iframe 无 title）。
- 检索路径超过 3 跳才找到本清单或对应 A11Y 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 A11Y-06（BI 场景）～ A11Y-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 工程守卫与 Radix 规则 | `engineering-guards.md` |
| 交互状态与焦点 | `state-index.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 场景交互与动效 | `scene-interaction-review-checklist.md` |
| 场景视觉 Token | `scene-visual-token-review-checklist.md` |
| 场景异步状态 | `scene-async-state-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| SSR / 微前端 Portal | `ssr-microfrontend-adoption-checklist.md#ssr-04` |
| 症状与回滚 | `upgrade-troubleshooting.md` A11Y-* / VIS-* / DRIFT-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
