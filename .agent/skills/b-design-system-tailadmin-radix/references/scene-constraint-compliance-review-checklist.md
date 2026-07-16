# 场景约束遵守评审清单

> DOCS-028 / G77 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级约束遵守抽检**，覆盖 BI 大屏筛选与图表 Token/动态导入、DevOps 流水线 client 边界与中文阶段、Gateway 探测受控 props 与配额 Token、PaaS 危险操作 Maps client-only 与 ConfigDiff 语义及 MS 场景约束束，并与 `constraint-compliance-review-checklist.md`（CON-01～05）、`engineering-guards.md`、`token-index.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景约束抽检 | 对应 CON 块 + `quality-rubric.md` 约束遵守 |
| 大规模 Agent 生成后 MS 场景抽检 | CON-01～05（控件/页面级）+ CON-06～10（场景级）各抽 1 页 |
| BI 筛选 chips 硬编码色或 Chart 非 dynamic import | 先跑 CON-06，再查 `layout-patterns/bi-filter-linkage.md` |
| CI/CD 阶段条手写 div 弹层或英文阶段文案 | CON-07 + `templates/devops/pipeline-stage-bar.tsx` |
| Gateway 探测表裸色值或 ControlPlaneHub 非受控 props | CON-08 + MS-09 `EndpointProbeTable` |
| PaaS Maps SSR 直渲或 ResourceTable 英文 mock | CON-09 + `templates/paas/resource-table.tsx` |
| MS 场景组合 Token+API+文案工程边界违规 | CON-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `constraint-compliance-review-checklist.md` CON-01～05（语义 Token、框架 API、导入规则、Skill 红线、MS 工程边界）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 与 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` 选取同类型截图证据。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
4. 页面内 `#hex`、`rgb()`、`style={{ color }}` 默认视为 CON-01/CON-06 失败；浮层非 Radix 实现视为 CON-02/CON-07 失败。
5. 用户可读 mock/placeholder/helper 默认中文；无 `locale`/i18n 入口的英文默认文案视为 CON-04/CON-08 失败。

## CON-06 — BI / Data Screen 筛选与图表约束遵守

**对照 reference**：`layout-patterns/bi-filter-linkage.md`、`templates/bi/cross-filter-dashboard.tsx`、`templates/bi/filter-bar.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | FilterBar Token | chip 选中/默认态使用 `brand-*` / `gray-*` 语义 Token，无裸 `blue-500` | CON-06 · MS-11 |
| 2 | Chart 边界 | Chart/ApexCharts `dynamic import` 或 client-only；`chartPaletteCssVars` 对齐 | CON-03 · ASYNC-05 |
| 3 | KPI 语义色 | 趋势 up/down 使用 `success-*` / `error-*`；数字 tabular-nums | CON-01 · VIS-06 |
| 4 | cross-filter 文案 | 筛选 chips、空态、错误态默认中文；技术缩写可保留 | CON-04 · COPY-03 |
| 5 | Dark 约束 | 筛选 chip 与图表轴/网格在 `html.dark` 下层级可读 | CON-01 · VIS-02 |

**交互动作**：抽 BI 筛选页 → 检查 className 无裸色值 → 确认 Chart lazy 边界 → 切换 light/dark → 对照 `bi-chart-state-gates.png`。

## CON-07 — DevOps 流水线阶段与日志约束遵守

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段条 Radix | PipelineStageBar 浮层/菜单使用 Radix/shadcn；禁止手写 portal | CON-02 · MS-10 |
| 2 | LogStream client | LogStreamPanel 等重组件 client-only 或 dynamic import | CON-03 · SSR-02 |
| 3 | 阶段中文 | 阶段名、状态 badge、空态/错误默认中文 | CON-04 · COPY-04 |
| 4 | Rollback Dialog | 确认 Dialog 受控 `open`；destructive 使用语义 `error-*` Token | CON-02 · LOGIC-02 |
| 5 | Danger Zone | 危险区块按钮使用 `cva` variants；无内联条件 class 堆叠 | CON-02 · VIS-07 |

**交互动作**：打开 Rollback Dialog → 检查 Radix 实现与 `cn()` 合并 → 抽查阶段/日志中文 mock → 对照 `workflow-ticket-reply.png`。

## CON-08 — Gateway 端点探测与配额约束遵守

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 受控 props | `ControlPlaneHub` / `EndpointProbeTable` 使用受控 props，非 Skill 内部 mock 穿透 | CON-08 · MS-09 |
| 2 | Probe Token | 探测结果 badge 使用语义 Token；状态不仅靠颜色区分 | CON-01 · A11Y-08 |
| 3 | 表格导入 | 模板从 `@/components/ui/*` 导入；无深层相对路径穿透 | CON-03 · ADOPT-03 |
| 4 | 配额文案 | BalanceQuota 超限/正常说明默认中文 | CON-04 · ASYNC-08 |
| 5 | License 状态 | 有效/过期/吊销使用 Badge variants；导出与 `api-contracts.md` 一致 | CON-03 · TYPE-01 |

**交互动作**：抽查 Gateway 页 import 行 → 模拟配额超限 → 检查探测 Dialog Radix 实现 → 对照 `gateway-patterns` golden。

## CON-09 — PaaS 危险操作与 ConfigDiff 约束遵守

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Maps client-only | Maps/Vector 嵌入 dynamic import 或 client-only 声明 | CON-03 · MS-12 |
| 2 | 危险 Dialog | 恢复/伸缩 Dialog Radix 受控；确认按钮语义 Token | CON-02 · INTER-09 |
| 3 | ConfigDiff | diff 高亮使用语义背景 Token；变更行不仅靠 `#hex` | CON-01 · VIS-09 |
| 4 | ResourceTable 密度 | 表格密度符合 TailAdmin 约定；mock 列头/空态中文 | CON-04 · COPY-04 |
| 5 | theme helper | Maps/Chart override 走 `mergeMapLibreOptions` / `getBaseChartOptions` deep merge | CON-03 · MER-02 |

**交互动作**：抽查 PaaS 页 Maps import → 打开恢复 Dialog → 展开 ConfigDiff 检查 Token → 对照 `paas-restore-dialog-open` golden。

## CON-10 — MS 场景约束束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：受控 props + 探测表 Token + 配额中文 mock + Radix Dialog | SOR-05 · CON-08 |
| 2 | MS-10 | CI/CD：client 边界 + 阶段中文 + Pipeline Radix + LogStream 密度 | SOR-02 · CON-07 |
| 3 | MS-11 | BI：Chart dynamic + `chartPaletteCssVars` + 筛选 chips 中文 | SOR-01 · CON-06 |
| 4 | MS-12 | PaaS：Maps client-only + ResourceTable 密度 + 危险 Dialog 中文 | SOR-03 · CON-09 |
| 5 | MS-13 | 治理：PermissionMatrix 非 Switch 列表 + Wizard 中文 + 审计表异步态合规 | SOR-04 · CON-04 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景约束遵守（G77）** 选型表 → 确认 CON-01～10 在场景内组合满足。

## 五类场景约束遵守速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | 筛选硬编码色、Chart SSR 直渲、KPI 裸色值 | `bi-filter-linkage.md` | CON-06 · VAL-03 |
| DevOps | 手写 div 弹层、英文阶段文案、LogStream SSR | `devops-template.md` | CON-07 · VAL-02 |
| Gateway | 探测表裸色值、非受控 props、英文 mock | `gateway-template.md` | CON-08 · VAL-01 |
| PaaS | Maps SSR 直渲、ConfigDiff `#hex`、英文列头 | `paas-template.md` | CON-09 · MS-12 |
| MS 束 | 领域页 Token+API+文案组合违规 | `business-validation-checklist.md` | CON-10 · DRIFT-02 |

## 完整约束遵守评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `constraint-compliance-review-checklist.md` | CON-01～05 |
| 场景级 | 本文件 | CON-06～10 |

完整约束遵守评审 = **CON-01～10**；PR 前至少抽检 CON-01 + CON-06 + 1 个 MS CON-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix
npm run verify:runtime -w examples/b-design-system-tailadmin-radix
# 业务仓库：Token/导入/文案抽检
pnpm exec playwright test --grep scene-constraint
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的场景级裸色值、非 Radix 浮层、SSR 直渲 Chart/Maps 或英文默认 mock。
- MS 场景组合在工程边界（受控 props、client-only、中文 mock、theme helper）上反复失败。
- `engineering-guards.md` 未覆盖的新场景级约束模式。

症状 ID 对照：`upgrade-troubleshooting.md` 中 CON-06（BI 场景）～ CON-10（MS 束）。

## 检索入口

| 意图 | 读 |
|---|---|
| 工程守卫 | `engineering-guards.md` |
| Token 索引 | `token-index.md` |
| 控件/页面级约束 | `constraint-compliance-review-checklist.md` |
| 组件/页面正选 | `decision-matrix.md` |
| 场景可访问性 | `scene-accessibility-review-checklist.md` |
| 场景响应式 | `scene-responsive-review-checklist.md` |
| 场景视觉 Token | `scene-visual-token-review-checklist.md` |
| 中文文案 | `chinese-copy-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| SSR / 微前端嵌入 | `ssr-microfrontend-adoption-checklist.md#ssr-02` |
| 症状与回滚 | `upgrade-troubleshooting.md` CON-* / VIS-* / COPY-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
| Example runtime 证据 | `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/` |
