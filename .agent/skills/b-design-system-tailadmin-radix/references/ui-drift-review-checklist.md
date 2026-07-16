# UI 漂移评审清单

> DOCS-007 / G56 产物。对 Agent 生成或人工改写的业务页面执行**可复现漂移评审**，覆盖视觉、交互、语义与工程四类漂移，并与 `examples/b-design-system-tailadmin-radix` golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前 UI 评审 | 对应 REV 块 + `quality-rubric.md` 截图红线 |
| 大规模 Agent 生成后抽检 | REV-01～05 各抽 1 页 |
| 与 example golden screen 不一致 | 先跑本清单，再查 `decision-matrix.md` |
| 业务部署验证已通过但视觉仍别扭 | REV-01 视觉 + REV-03 语义叠加检查 |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
2. 截图视口 **desktop 1440×1000**，**light + dark** 各 1 张；交互组件补打开态截图。
3. 用户可见文案默认中文（技术缩写除外，见 `quality-rubric.md`）。
4. 组件/页面选型争议必须先读 `decision-matrix.md`，再填本清单。
5. Agent 常见失败对照 `agent-failure-patterns-review-checklist.md` FAIL-01～05 与 `scene-agent-failure-review-checklist.md` FAIL-06～10。

## REV-01 — 仪表盘 / KPI / 概览页

**对照 golden**：`overview-period`、`tablet-overview`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 内容宽度 | 主内容区按 `max-w-(--breakpoint-2xl)` 展开，无首屏大面积空白 | `quality-rubric.md` 截图红线；DRIFT-01 |
| 2 | KPI 栅格 | desktop 4 列 / tablet 2×2；数字与趋势标签不被裁切 | DRIFT-01 |
| 3 | Token 密度 | 使用 `brand-*` / `gray-*` 语义 Token，无硬编码 hex | `token-index.md` |
| 4 | 周期筛选 | 概览类页面有受控周期或筛选，非静态假数据 | `decision-matrix.md#仪表盘` |
| 5 | 图标语义 | KPI 头图标来自 `icon-system.md`，非随机 lucide | DRIFT-03 |

**交互动作**：切换 light/dark → 切换 KPI 周期（若有）→ 检查首屏无裁切。

## REV-02 — 表单 / 设置 / 向导页

**对照 golden**：`form-controls-matrix`、`form-dialog-short`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 容器选型 | 短表单用 Dialog；长表单用独立页/Drawer/向导，非单页堆叠 | `layout-patterns/form-composition.md` |
| 2 | 高级输入 | 金额/密钥/OTP 用对应 AdvancedInput，非普通 Input | DRIFT-03 |
| 3 | 状态覆盖 | required/error/success/disabled/loading 有视觉区分 | `state-index.md` |
| 4 | 标签对齐 | Boolean 控件标签与轨道/圆点对齐 | DRIFT-05 |
| 5 | 中文文案 | placeholder/helper/按钮为中文 | DRIFT-04 |

**交互动作**：触发校验错误 → 打开 Dialog 短表单（若有）→ 关闭路径可辨。

## REV-03 — 列表 / DataTable / 详情页

**对照 golden**：`data-table-dense`、`paas-resource-table`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 表格选型 | 大数据列表用 DataTableCard/Query shell，非裸 Table | `decision-matrix.md#表格` |
| 2 | 状态矩阵 | loading/empty/error/partial 有占位与重试 | `prd/F02-data-state.md` |
| 3 | 浮层操作 | 行操作/批量操作用 Dropdown 或 Dialog 确认 | DRIFT-02 |
| 4 | 数字对齐 | KPI/金额/百分比列右对齐或 tabular-nums | DRIFT-01 |
| 5 | 场景组合 | MS-09～13 类页面符合决策矩阵正选 | `business-validation-checklist.md` |

**交互动作**：排序或筛选一列 → 打开行操作 Dropdown → 取消批量操作 Dialog。

## REV-04 — 壳层 / 导航 / 门户

**对照 golden**：`overview`、`devops-patterns` shell framing

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 侧栏宽度 | 展开 290px / 折叠 90px，内容区不被侧栏遮挡 | DRIFT-05 |
| 2 | 顶栏 sticky | 顶栏固定，滚动时内容区 framing 稳定 | `interaction-motion.md` |
| 3 | Hub Tabs | 设置/配额类用 `?tab=` Hub，非手写多路由碎片 | `layout-patterns/hub-tabs.md` |
| 4 | 主题切换 | ThemeToggle 可切换 light/dark，对比度可读 | VIS-02 |
| 5 | 门户选型 | 用户/管理/开发者门户用 Dual Portal Shell 模式 | `decision-matrix.md#布局` |

**交互动作**：折叠侧栏 → 切换主题 → 检查 active 导航与内容左边界。

## REV-05 — BI / 大屏 / 监控画布

**对照 golden**：`bi-filter-linkage`、`data-screen-canvas`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 信息层次 | 大屏有 KPI 带、主图区、明细区，非空容器占位 | `quality-rubric.md` 截图红线 |
| 2 | 图表色板 | 使用 `getBaseChartOptions` + `chartPaletteCssVars` | MER-02 |
| 3 | 联动筛选 | 多图页用 FilterBar chips + 受控 `filters` | MS-11 / SOR-01 |
| 4 | 下钻路径 | 下钻有面包屑或返回，非死胡同 | `layout-patterns/bi-drill-down.md` |
| 5 | 导出/分享 | 需要对外分发时有 ExportMenu 或 ShareEmbedDialog | `decision-matrix.md#bi` |

**交互动作**：添加筛选 chip → 观察图表联动 → 打开导出或分享菜单（取消即可）。

## 完整 UI 漂移评审路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件/页面级 | 本文件 | REV-01～05 |
| 场景级 | `scene-ui-drift-review-checklist.md` | REV-06～10 |

完整 UI 漂移评审 = **REV-01～10**；PR 前至少抽检 REV-01 + REV-06 + 1 个 MS REV-10 场景。

## 四类漂移速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 视觉漂移 | 间距突变、hex 硬编码、dark 对比度丢失 | `token-index.md` · `visual-language.md` | DRIFT-01 · VIS-* |
| 交互漂移 | 状态缺失、浮层不可关、控件不可操作 | `state-index.md` · example section | DRIFT-02 · DRIFT-05 |
| 语义漂移 | 组件/页面错选、图标语义错误 | `decision-matrix.md` · `icon-system.md` | DRIFT-03 · SEL-* |
| 工程漂移 | 手写 Modal、缺 `cn()`、英文 mock | `engineering-guards.md` · `quality-rubric.md` | DRIFT-04 · DRIFT-02 |

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库
pnpm exec tsc --noEmit
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的错选或反模式（非一次性笔误）。
- golden screen 与业务页差异根因为 Skill 规则缺口。
- 检索路径超过 3 跳才找到本清单或对应 REV 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 DRIFT-01（视觉密度）～ DRIFT-05（截图红线）。

新增 DRIFT-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 REV 块。

## 检索入口

| 意图 | 读 |
|---|---|
| 评审规程与封顶规则 | `quality-rubric.md` |
| 组件/页面正选 | `decision-matrix.md` |
| Golden screen 路径 | `docs/spec/.../shards/golden-screens.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 首次接入 / vendoring | `adoption-onboarding-checklist.md` |
| SSR / 微前端接入 | `ssr-microfrontend-adoption-checklist.md`（SSR-01～SSR-05 / MFE-01～MFE-05） |
| 可访问性评审 | `accessibility-review-checklist.md`（A11Y-01～A11Y-05） |
| 症状与回滚 | `upgrade-troubleshooting.md` DRIFT-* / VIS-* / SEL-* / SSR-* / MFE-* / A11Y-* |
| 场景级 UI 漂移 | `scene-ui-drift-review-checklist.md`（REV-06～10） |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
