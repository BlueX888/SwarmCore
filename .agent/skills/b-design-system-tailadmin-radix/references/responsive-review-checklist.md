# 响应式评审清单

> DOCS-011 / G60 产物。对 Agent 生成或人工改写的业务页面执行**可复现响应式抽检**，覆盖壳层、栅格、表单、表格与大屏在 desktop / tablet / mobile 视口下的布局、密度与交互可达性，并与 `state-index.md`、`golden-screens.md` 及 preview 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前响应式抽检 | 对应 RESP 块 + `quality-rubric.md` 截图红线 |
| 大规模 Agent 生成后抽检 | RESP-01～05 各抽 1 页 |
| 首屏大面积空白或文本裁切 | 先跑 RESP-02，再查 `token-index.md` |
| tablet/mobile 侧栏遮挡主内容 | RESP-01 + `state-index.md` 布局状态 |
| DataTable 横向溢出或行操作不可点 | RESP-04 + `decision-matrix.md#表格` |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
2. 抽检视口 **desktop 1440×1000**、**tablet 1024×768**、**mobile 390×844**；**light + dark** 各至少 1 次壳层检查。
3. 用户可见文案默认中文（技术缩写除外，见 `quality-rubric.md`）。
4. 固定格式 UI（KPI 栅格、表格、工具栏、大屏画布）必须按容器宽度响应式展开，禁止 desktop 布局直搬 mobile。

## RESP-01 — 壳层 / 导航 / 门户

**对照 reference**：`state-index.md#响应式`、`layout-patterns/app-shell.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 侧栏断点 | `< xl` 侧栏 overlay + Backdrop；`xl+` fixed 侧栏 + 内容 margin | RESP-01 |
| 2 | 侧栏尺寸 | 展开 290px / 折叠 90px；内容左边界不压入侧栏 | DRIFT-05 |
| 3 | 移动菜单 | hamburger 可开关；关闭后焦点回到触发器 | A11Y-03 |
| 4 | 顶栏换行 | tablet/mobile 顶栏双行或压缩操作区，主任务按钮仍可达 | RESP-01 |
| 5 | Hub Tabs | 设置/配额类 `?tab=` 在窄屏可横向滚动或折行，active 态可读 | `layout-patterns/hub-tabs.md` |

**交互动作**：在 **1024px** 折叠/展开侧栏 → 在 **390px** 打开移动菜单 → 检查主内容区 framing 与 active panel 左边界。

## RESP-02 — 仪表盘 / KPI / 概览栅格

**对照 golden**：`overview-period`、`tablet-overview`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 内容宽度 | 主内容 `max-w-(--breakpoint-2xl)` 展开；无首屏右侧大面积空白 | DRIFT-01 |
| 2 | KPI 栅格 | desktop 4 列；tablet **2×2**；mobile 1 列堆叠 | RESP-02 |
| 3 | 数字裁切 | KPI 数字、趋势标签、单位不被裁切或重叠 | `quality-rubric.md` 截图红线 |
| 4 | 周期筛选 | 筛选控件在窄屏折行或入 Popover，不挤压 KPI 卡片 | RESP-02 |
| 5 | 卡片密度 | 卡片 padding/gap 使用 Token，窄屏不贴边或溢出 | `token-index.md` |

**交互动作**：在 **1024px** 检查 KPI 是否为 2×2 → 在 **390px** 检查首屏主任务信息可见 → 切换 light/dark 各 1 次。

## RESP-03 — 表单 / Dialog / Drawer / Sheet

**对照 golden**：`form-controls-matrix`、`form-dialog-short`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 容器选型 | mobile 筛选/短编辑用 bottom Sheet，非居中 Dialog 直搬 | `decision-matrix.md#表单页面形态` |
| 2 | 字段栅格 | FormSection `cols=2` 在 `< md` 降为单列 | RESP-03 |
| 3 | 长表单 | 独立页/Drawer 在窄屏 sticky actions 不遮挡最后字段 | `layout-patterns/form-composition.md` |
| 4 | Dialog 宽度 | 居中 Dialog `max-w-lg` 级；mobile 留边距不贴屏 | RESP-03 |
| 5 | 布尔对齐 | Switch/Checkbox 标签与轨道在窄屏仍对齐，不错位 | DRIFT-05 |

**交互动作**：在 **390px** 打开 Dialog 短表单 → 打开 bottom Sheet（若有）→ 提交触发错误态检查字段可见。

## RESP-04 — 列表 / DataTable / Master-Detail

**对照 golden**：`data-table-dense`、`paas-resource-table`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 横向滚动 | 列多时在容器内 `overflow-x-auto`，不撑破壳层 | RESP-04 |
| 2 | 固定列 | 关键列（名称/状态）在窄屏仍可见或 sticky | `decision-matrix.md#表格` |
| 3 | 工具栏 | 搜索/筛选/批量操作在 mobile 折行或入 Sheet，不重叠 | RESP-04 |
| 4 | Master-Detail | `< lg` 详情入 Drawer/全屏，不挤压列表到不可读 | `layout-patterns/master-detail-ops.md` |
| 5 | 行操作 | icon-only 行操作 touch target ≥ 40px，间距足够 | A11Y-04 |

**交互动作**：在 **390px** 横向滚动表格 → 打开行操作 Dropdown → 若有 Master-Detail，切换列表/详情视图。

## RESP-05 — BI / 大屏 / 监控画布

**对照 golden**：`bi-filter-linkage`、`data-screen-canvas`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 大屏比例 | 画布按 16:9 或设计稿比例缩放，非空容器占位 | `decision-matrix.md#反例` |
| 2 | 图例/筛选 | FilterBar chips 在窄屏可换行或横向滚动 | RESP-05 |
| 3 | 图表高度 | ChartPanel 在 tablet/mobile 有最小高度，不压成细条 | `extension-audit.md` |
| 4 | 地图块 | 地图/拓扑在 mobile 仍可读，或提供列表降级 | MS-12 |
| 5 | MS 抽检 | MS-09～13 至少 1 页完成 RESP-01 + RESP-02 双视口抽检 | `business-validation-checklist.md` |

**交互动作**：在 **1024px** 检查 BI 筛选与图表并排 → 在 **390px** 检查大屏/监控画布信息层次仍可读。

## 五类响应式速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 壳层/导航 | 侧栏遮挡、移动菜单无法关闭、双顶栏 | `state-index.md` · preview | RESP-01 · MFE-04 |
| 栅格/KPI | 首屏空白、tablet 仍 4 列、数字裁切 | `golden-screens.md` | RESP-02 · DRIFT-01 |
| 表单/浮层 | Dialog 贴边、双列表单溢出 | `form-composition.md` | RESP-03 · SEL-* |
| 表格/详情 | 表格撑破页面、行操作重叠 | `master-detail-ops.md` | RESP-04 |
| BI/大屏 | 假柱状条、筛选挤压图表 | `domain-scenarios.md` | RESP-05 |

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库：Playwright / 真机截图
pnpm exec playwright test --grep responsive
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的 tablet KPI 单列堆叠、mobile Dialog 贴边或表格撑破壳层。
- MS 场景组合在窄屏出现 framing 反模式（如双 AppLayout、Master-Detail 同屏挤压）。
- 检索路径超过 3 跳才找到本清单或对应 RESP 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 RESP-01（壳层）～ RESP-05（BI/大屏）；场景级 RESP-06～10 见 `scene-responsive-review-checklist.md`。

控件/页面级 RESP-01～05 完成后，对 BI/Data Screen、DevOps、Gateway、PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-responsive-review-checklist.md`（DOCS-027 / G76）。

新增 RESP-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 RESP 块。

## 检索入口

| 意图 | 读 |
|---|---|
| 断点与侧栏行为 | `state-index.md` |
| 壳层与门户模板 | `layout-patterns/app-shell.md` |
| 组件/页面正选 | `decision-matrix.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 可访问性抽检 | `accessibility-review-checklist.md` |
| 场景响应式抽检 | `scene-responsive-review-checklist.md` |
| 异步状态抽检 | `async-state-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| SSR / 微前端嵌入 | `ssr-microfrontend-adoption-checklist.md#mfe-04` |
| 症状与回滚 | `upgrade-troubleshooting.md` RESP-* / DRIFT-* / VIS-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
