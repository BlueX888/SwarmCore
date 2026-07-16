# 视觉 Token 与密度评审清单

> DOCS-015 / G64 产物。对 Agent 生成或人工改写的业务页面执行**可复现视觉 Token 与密度抽检**，覆盖语义色、暗色对比、间距密度、圆角阴影层级与排版数字对齐，并与 `visual-language.md`、`token-index.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前视觉抽检 | 对应 VIS 块 + `quality-rubric.md` 综合美学 |
| 大规模 Agent 生成后抽检 | VIS-01～05 各抽 1 页 |
| 升级后 KPI/表格密度突变 | 先跑 VIS-03，再查 `api-contracts.md` 风险表 |
| dark 主题对比度或边框丢失 | VIS-02 + `token-index.md` |
| 硬编码 `#hex` 或默认 Tailwind 色板 | VIS-01 + `engineering-guards.md` |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
2. 抽检视口 **desktop 1440×1000**，**light + dark** 各至少 1 次；tablet 1024px 补 KPI 栅格检查。
3. 业务代码禁止页面内 `#hex`、`rgb()`、`oklch()` 硬编码颜色（`index.css` @theme 除外）。
4. 密度与间距须符合 `visual-language.md`：输入 `h-11`、卡片 `p-5`/`p-6`、页面 `gap-6`、表格 cell `py-4`。

## VIS-01 — 语义色与 Token 命中

**对照 reference**：`token-index.md`、`engineering-guards.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 主操作色 | 主按钮/链接/选中导航使用 `brand-500`/`brand-600`，非 `blue-500` 等默认色 | VIS-01 |
| 2 | 状态色 | success/warning/error 使用语义 Token，非手写 hex 或随机色 | VIS-01 |
| 3 | 中性灰阶 | 正文/边框/背景使用 `gray-*` 或 `@theme` 语义灰，非 `slate/zinc` 混用 | VIS-01 |
| 4 | 硬编码扫描 | `rg` 业务代码无 `#465fff` 等 hex；`index.css` 外无内联颜色 style | `engineering-guards.md` |
| 5 | Chart 色板 | 图表 series 走 `chartPaletteCssVars` 或 `getBaseChartOptions`，非页面内写死色值 | MS-11 |

**交互动作**：light/dark 切换主按钮、Badge、Alert → 运行 `rg -n "#[0-9a-fA-F]{3,8}" src --glob '!index.css'` → 对照 golden `overview-period`。

## VIS-02 — Dark 对比度与边框层级

**对照 golden**：`overview-period`、`desktop-dark`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 正文对比 | dark 下正文 `white/90` on `gray-900` 可读；辅助文案 `gray-400` 仍清晰 | VIS-02 |
| 2 | 卡片边框 | 面板 `dark:border-white/[0.05]` 或 `dark:border-gray-800`；非仅改背景不改边框 | VIS-02 |
| 3 | 输入/表格线 | Input、Table 分隔线在 dark 下可见，不糊成一片 | A11Y-05 |
| 4 | 选中/hover | 侧栏 `menu-item-active` 在 dark 下 `brand-500/12` 可辨 | INTER-01 |
| 5 | 浮层背景 | Dialog/Dropdown 在 dark 下背景与 overlay 层级分明 | INTER-02 |

**交互动作**：切换 dark → 检查 Overview KPI 卡、表格、侧栏选中项 → 与 golden `desktop-dark` 对照。

## VIS-03 — 密度、间距与栅格利用率

**对照 golden**：`overview-period`、`layout-patterns-tablet`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 内容区宽度 | 主列 `max-w-(--breakpoint-2xl)` 撑满；首屏无大面积无意义空白 | RESP-02 |
| 2 | KPI 栅格 | desktop 4 列 / tablet 2×2 / mobile 1 列；数字不裁切 | DRIFT-01 |
| 3 | 卡片 padding | 面板内边距 `p-5` 或 `p-6`；toolbar 与内容对齐 | VIS-03 |
| 4 | 表格密度 | cell `py-4`、header `py-3`；`text-theme-sm` 层级一致 | `visual-language.md` |
| 5 | 页面间距 | 区块 `gap-6`；表单字段组 `gap-4`；不出现过疏或过挤 | VIS-03 |

**交互动作**：desktop 与 1024px tablet 各截 1 张 Overview → 量 KPI 栅格列数与右侧空白 → 对照 golden。

## VIS-04 — 圆角、阴影与 z-index 层级

**对照 reference**：`visual-language.md`、`state-index.md#浮层状态`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 圆角层级 | 控件 `rounded-lg`、面板 `rounded-xl`、Modal `rounded-3xl` | VIS-04 |
| 2 | 阴影语义 | 卡片 `shadow-theme-sm`、下拉 `shadow-theme-lg`；非随意 `shadow-xl` | VIS-04 |
| 3 | 浮层 z-index | Modal/Dropdown 使用 `z-99999` 或项目约定高层级，非默认 `z-50` 被遮挡 | INTER-02 |
| 4 | 焦点环 | Input `focus:ring-brand-500/20`；与 `shadow-focus-ring` 一致 | INTER-01 |
| 5 | 图标尺寸 | 导航 `size-6`、按钮内 `size-5`；与 `menu-item-icon` 对齐 | `icon-system.md` |

**交互动作**：打开 Dialog + Header Dropdown → 检查圆角/阴影/层级 → Esc 关闭。

## VIS-05 — 排版层级与数字/KPI 对齐

**对照 golden**：`data-table-dense`、`bi-filter-linkage`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 标题层级 | 页面 `text-title-sm`/`text-xl`；区块 `text-lg`；辅助 `text-theme-xs` | VIS-05 |
| 2 | 数字/KPI | 指标数字 `font-semibold`；千分位/单位对齐；zero 态仍占位 | `state-index.md` |
| 3 | 表格数字列 | 数字/KPI 列右对齐或 tabular-nums；长 ID 可截断+tooltip | RESP-04 |
| 4 | 工具栏对齐 | 表格 toolbar 左筛选右操作；与按钮 `md` 高度对齐 | `decision-matrix.md#表格` |
| 5 | 大屏信息层次 | Data Screen 有 KPI 带+图表+明细层次，非空容器或假柱状条 | RESP-05 |

**交互动作**：打开 DataTable dense + BI 联动面板 → 检查列对齐、KPI 数字层级 → 对照 golden。

## 五类视觉 Token 速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 语义色 | `blue-500`、页面内 hex | `token-index.md` | VIS-01 · DRIFT-04 |
| Dark 对比 | 边框消失、文字发灰 | `visual-language.md` | VIS-02 · A11Y-05 |
| 密度栅格 | 首屏空白、KPI 裁切 | `golden-screens.md` | VIS-03 · DRIFT-01 |
| 圆角阴影 | Modal 被挡、阴影过重 | `state-index.md` | VIS-04 · INTER-02 |
| 排版数字 | 数字列错位、大屏占位 | `visual-language.md` | VIS-05 · RESP-05 |

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

- 评审发现**稳定复现**的硬编码色、默认 Tailwind 色板或 dark 边框缺失。
- MS 场景组合视觉密度与 golden 明显不一致（如网关页 KPI 过疏或表格过挤）。
- 检索路径超过 3 跳才找到本清单或对应 VIS 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 VIS-01（语义色）～ VIS-05（排版数字）；场景级 VIS-06～10 见 `scene-visual-token-review-checklist.md`。

新增 VIS-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 VIS 块。

## 场景级视觉 Token（VIS-06～10）

控件/页面级 VIS-01～05 完成后，对 BI/Data Screen、DevOps、Gateway、PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-visual-token-review-checklist.md`（DOCS-024 / G73）。

完整视觉 Token 与密度评审 = **VIS-01～10**；PR 前至少抽检 VIS-01 + VIS-06 + 1 个 MS VIS-10 场景。

## 检索入口

| 意图 | 读 |
|---|---|
| 视觉规则与反模式 | `visual-language.md` |
| Token 定义 | `token-index.md` |
| 工程守卫与静态检查 | `engineering-guards.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 响应式栅格 | `responsive-review-checklist.md` |
| 可访问性对比度 | `accessibility-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` VIS-* / DRIFT-01 |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
