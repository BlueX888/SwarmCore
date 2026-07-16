# 场景视觉 Token 与密度评审清单

> DOCS-024 / G73 产物。对 Agent 生成或人工改写的**领域场景页**执行**可复现场景级视觉 Token 与密度抽检**，覆盖 BI 大屏色板与 KPI 密度、DevOps 流水线视觉层级、Gateway 探测与配额面板、PaaS 危险操作与 diff 高亮及 MS 场景视觉束，并与 `visual-token-review-checklist.md`（VIS-01～05）、`visual-language.md`、`token-index.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景视觉抽检 | 对应 VIS 块 + `quality-rubric.md` 综合美学 |
| 大规模 Agent 生成后 MS 场景抽检 | VIS-01～05（控件/页面级）+ VIS-06～10（场景级）各抽 1 页 |
| BI 大屏假占位或 chart 色板漂移 | 先跑 VIS-06，再查 `layout-patterns/bi-data-screen.md` |
| CI/CD 阶段条/日志面板密度异常 | VIS-07 + `references/component-styles/devops-template.md` |
| Gateway probe 状态色或配额条无语义色 | VIS-08 + MS-09 `EndpointProbeTable` |
| PaaS ConfigDiff 高亮缺失或危险区色不对 | VIS-09 + `templates/paas/ops-danger-flow.tsx` |
| MS 场景组合视觉密度与 golden 明显不一致 | VIS-10 + `business-validation-checklist.md` |

## 通用前置

1. 先完成 `visual-token-review-checklist.md` VIS-01～05（语义色、dark 对比、密度、圆角阴影、排版数字）。
2. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
3. 抽检至少 **1 个 BI/Data Screen 场景 + 1 个 MS-09～13 领域组合页**。
4. 场景级 KPI/状态色/用量条必须使用语义 Token（`brand-*`、`success-*`、`warning-*`、`error-*`），禁止页面内 `#hex` 或默认 Tailwind 色板。
5. desktop 1440px + tablet 1024px 各检查 1 次；**light + dark** 各至少 1 次。

## VIS-06 — BI / Data Screen 色板与信息层次

**对照 reference**：`layout-patterns/bi-data-screen.md`、`templates/bi/data-screen-canvas.tsx`、`templates/bi/cross-filter-dashboard.tsx`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Chart 色板 | series 走 `chartPaletteCssVars` 或 `getBaseChartOptions`；非页面内写死色值 | VIS-06 · MS-11 |
| 2 | KPI 密度 | 大屏 KPI 带 `font-semibold` + tabular-nums；desktop 4 列 / tablet 2×2 | VIS-03 · DRIFT-01 |
| 3 | 信息层次 | Data Screen 有 KPI 带 + 图表 + 明细/告警区块；非空容器或假柱状条 | VIS-05 · RESP-05 |
| 4 | 筛选 chips | FilterBar chip 使用 `brand-500/12` 选中态；清除按钮语义色一致 | VIS-01 · INTER-06 |
| 5 | Dark 对比 | 大屏区块边框 `dark:border-white/[0.05]`；图表轴/网格线在 dark 下可读 | VIS-02 · A11Y-05 |

**交互动作**：FilterBar 添加 chip → 观察 KPI/图表色板联动 → 切换 light/dark → 对照 golden `bi-filter-linkage` / `data-screen-canvas`。

## VIS-07 — DevOps 流水线与日志面板视觉层级

**对照 golden**：`cicd-run-detail`、`pipeline-stage-bar`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 阶段条色板 | active 阶段 `brand-500`；成功 `success-500`；失败 `error-500` | VIS-07 · MS-10 |
| 2 | 日志面板密度 | LogStream 等宽字体 + `text-theme-sm`；行高不裁切；尾部 loading 区有 padding | VIS-03 · INTER-07 |
| 3 | 制品/审批 | ArtifactTable 行 hover `gray-50`/`dark:gray-800`；ApprovalTimeline pending 用 `warning-*` | VIS-01 · LOGIC-09 |
| 4 | Danger Zone | 危险区块 `error-50`/`dark:error-500/10` 背景 + `error-600` 边框；与主表单视觉隔离 | VIS-07 · LOGIC-02 |
| 5 | Diff 查看器 | DiffViewer 增删行 `success-500/10` / `error-500/10` 高亮；非纯灰底 | VIS-09 · MS-10 |

**交互动作**：PipelineStageBar 切换阶段 → 检查 active 色与日志密度 → 打开 Rollback Dialog → 对照 golden `cicd-run-detail`。

## VIS-08 — Gateway 探测状态与配额面板视觉

**对照 golden**：`gateway-patterns`、`control-plane-hub`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Probe 状态色 | loading `gray-400`；success `success-500`；failed `error-500`；分步结果有 badge 语义色 | VIS-08 · LOGIC-04 |
| 2 | 配额用量条 | BalanceQuota 填充 `brand-500`；超限 `warning-500`/`error-500`；数字 tabular-nums | VIS-08 · MS-09 |
| 3 | License 状态 | 有效/过期/吊销 badge 使用语义色；主操作 disabled 有 opacity 过渡 | VIS-01 · LOGIC-09 |
| 4 | 同步健康 | SyncHealth healthy/degraded 图标与背景色可辨；dark 下边框不丢失 | VIS-02 · ASYNC-04 |
| 5 | 部署模式矩阵 | DeploymentModeMatrix 选中格 `brand-500/12`；未选格边框层级清晰 | VIS-04 · MS-09 |

**交互动作**：EndpointProbeTable 触发 probe → 观察分步状态色 → 模拟配额超限 → 对照 golden `gateway-patterns`。

## VIS-09 — PaaS 危险操作与 ConfigDiff 视觉

**对照 golden**：`paas-patterns`、`paas-restore-dialog-open`、`paas-scale-dialog-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 危险 Dialog | 确认按钮 `destructive` 语义色；Dialog `rounded-3xl` + `shadow-theme-lg` | VIS-04 · INTER-09 |
| 2 | ConfigDiff 高亮 | 变更行 `warning-500/10` 或 `brand-500/8` 背景；展开不撑破栅格 | VIS-09 · MS-12 |
| 3 | ResourceTable | 行选中 `brand-500/12`；状态 badge 语义色一致 | VIS-01 · INTER-09 |
| 4 | Capacity 卡片 | 用量条填充过渡色使用 Token；partial 区块 loading 不拖垮 2×2 栅格 | VIS-03 · ASYNC-04 |
| 5 | Backup 列表 | 恢复/失败态 badge 语义色；操作列按钮高度与 toolbar 对齐 | VIS-05 · LOGIC-02 |

**交互动作**：ResourceTable 筛选 → 打开恢复 Dialog → 观察 ConfigDiff 高亮 → 对照 golden `paas-patterns`。

## VIS-10 — MS 场景视觉 Token 与密度束抽检

**对照 reference**：`business-validation-checklist.md`、`decision-matrix.md`、`scenario-override-recipes.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | MS-09 | 网关：probe 状态色 + 配额条 Token + 部署矩阵选中态 | SOR-05 · VIS-08 |
| 2 | MS-10 | CI/CD：阶段条语义色 + LogStream 密度 + Danger Zone 隔离色 | SOR-02 · VIS-07 |
| 3 | MS-11 | BI：chart 色板 + KPI tabular-nums + 大屏真实信息层次 | SOR-01 · VIS-06 |
| 4 | MS-12 | PaaS：ConfigDiff 高亮 + 危险 Dialog destructive + Capacity 栅格 | SOR-03 · VIS-09 |
| 5 | MS-13 | 治理：PermissionMatrix 勾选态 + Wizard 步骤圆角阴影 + AuditLog 表格密度 | SOR-04 · VIS-04 |

**交互动作**：按 MS 表各抽 1 个场景页 → 对照 decision-matrix **场景视觉 Token（G73）** 选型表 → 确认 VIS-01～10 在场景内组合满足。

## 五类场景视觉 Token 速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| BI/大屏 | 假柱状条、chart 裸色、KPI 裁切 | `bi-data-screen.md` | VIS-06 · DRIFT-01 |
| DevOps | 阶段无色语义、日志过挤、Danger 区不明显 | `devops-template.md` | VIS-07 · VAL-02 |
| Gateway | probe 状态灰一片、配额条无 Token | `gateway-template.md` | VIS-08 · VAL-01 |
| PaaS | diff 无高亮、危险按钮色不对 | `paas-template.md` | VIS-09 · LOGIC-02 |
| MS 束 | 领域页密度与 golden 明显漂移 | `business-validation-checklist.md` | VIS-10 · DRIFT-02 |

## 完整视觉 Token 评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | `visual-token-review-checklist.md` | VIS-01～05 |
| 场景级 | 本文件 | VIS-06～10 |

完整视觉 Token 与密度评审 = **VIS-01～10**；PR 前至少抽检 VIS-01 + VIS-06 + 1 个 MS VIS-10 场景。

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库：硬编码颜色与默认 Tailwind 色板扫描
rg -n "#[0-9a-fA-F]{3,8}|rgb\(|oklch\(" src --glob '!index.css'
rg -n "text-(blue|slate|zinc)-[0-9]" src/components
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的 BI 假占位、Gateway probe 状态色缺失或 PaaS diff 无高亮。
- MS 场景组合视觉密度与 golden 明显不一致（如 DevOps 日志过挤或 BI KPI 首屏空白）。
- 检索路径超过 3 跳才找到本清单或对应 VIS 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 VIS-06（BI 大屏）～ VIS-10（MS 束）；控件级 VIS-01～05 见 `visual-token-review-checklist.md`。

新增 VIS-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 VIS 块。

## 检索入口

| 意图 | 读 |
|---|---|
| 视觉规则与反模式 | `visual-language.md` |
| Token 定义 | `token-index.md` |
| 工程守卫与静态检查 | `engineering-guards.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 响应式栅格 | `responsive-review-checklist.md` |
| 可访问性对比度 | `accessibility-review-checklist.md` |
| 场景交互与动效 | `scene-interaction-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` VIS-* / DRIFT-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
