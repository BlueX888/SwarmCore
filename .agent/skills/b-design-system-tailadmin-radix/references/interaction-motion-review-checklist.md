# 交互与动效评审清单

> DOCS-013 / G62 产物。对 Agent 生成或人工改写的业务页面执行**可复现交互与动效抽检**，覆盖 hover、focus、pressed、open/close、布尔控件、loading 与列表/图表微交互，并与 `interaction-motion.md`、`state-index.md` 及 preview golden screens 对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前交互抽检 | 对应 INTER 块 + `quality-rubric.md` 交互与动效质量 |
| 大规模 Agent 生成后抽检 | INTER-01～05 各抽 1 页 |
| 控件 hover/focus 无反馈或动效突兀 | 先跑 INTER-01，再查 `interaction-motion.md` |
| Dialog/Dropdown 开关生硬或无法关闭 | INTER-02 + `state-index.md#浮层状态` |
| Switch/Slider 圆点错位或 loading 贴边 | INTER-03 / INTER-04 + `ui-drift-review-checklist.md` |

## 通用前置

1. 对照 `docs/spec/b-design-system-tailadmin-radix/shards/golden-screens.md` 选取同类型 golden screen。
2. 抽检视口 **desktop 1440×1000**，**light + dark** 各至少 1 次 hover/focus 检查；浮层补打开/关闭路径截图。
3. 动效时长与缓动须符合 `interaction-motion.md`（侧栏 300ms、颜色 150–200ms、浮层 ~150ms）；禁止无意义 bounce。
4. 开启 `prefers-reduced-motion: reduce` 时，布局动画应降级或关闭（见 `interaction-motion.md`）。

## INTER-01 — Hover / Focus / Pressed 基础交互态

**对照 reference**：`interaction-motion.md`、`state-index.md#交互状态`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Button hover | primary/outline/ghost 有可见背景或边框变化，非瞬时跳色 | INTER-01 |
| 2 | focus-visible | 键盘 Tab 时 Button/Input 有 `focus-visible:ring-*`；鼠标点击不强制粗环 | `state-index.md` |
| 3 | Menu/侧栏 | 菜单项 hover 背景 + active/selected 态可辨；折叠箭头旋转 ~300ms | INTER-01 |
| 4 | 表格行 | 数据行 hover 有浅底；选中行与 hover 不冲突 | `decision-matrix.md#表格` |
| 5 | 禁用态 | disabled 无 hover 反馈；`cursor-not-allowed` + 透明度一致 | A11Y-05 |

**交互动作**：键盘 Tab 遍历主按钮与输入框 → 鼠标 hover 侧栏项与表格行 → 切换 light/dark 各 1 次。

## INTER-02 — 浮层开关与过渡

**对照 golden**：`form-dialog-short`、`header-dropdown-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Dialog 进入/退出 | fade + scale（~150ms）；overlay `backdrop-blur` 不闪烁 | INTER-02 |
| 2 | Drawer/Sheet | 侧滑/底部滑入顺滑；关闭后焦点回到触发器 | A11Y-03 |
| 3 | Dropdown/Popover | 打开有位移 + 阴影；点击外部或 Esc 可关 | INTER-02 |
| 4 | 层级与遮挡 | 打开态不永久遮挡后续组件到无法阅读；有合理 z-index | DRIFT-05 |
| 5 | 滚动锁定 | Dialog 打开时背景不滚动；关闭后恢复 | `state-index.md#浮层状态` |

**交互动作**：打开 Dialog 短表单 → Esc 关闭 → 打开 Header Dropdown → 点击外部关闭 → 补打开态截图。

## INTER-03 — 布尔控件与 Slider 动效

**对照 golden**：`form-controls-matrix`、`boolean-controls`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | Switch | 圆点在轨道内滑动；checked/unchecked 过渡 ~150ms；不错位 | INTER-03 |
| 2 | Checkbox/Radio | 勾选/选中动画克制；indeterminate 态可辨 | INTER-03 |
| 3 | Segmented | 滑块指示器跟随选中项；键盘切换有过渡 | `form-controls-matrix` |
| 4 | Slider | 拇指在轨道内；拖拽与键盘步进同步；disabled 无拖动 | INTER-03 |
| 5 | 标签对齐 | 布尔控件与标签垂直居中；窄屏不错位 | RESP-03 |

**交互动作**：切换 Switch/Checkbox/Radio → 拖动 Slider → 在 **390px** 检查轨道与圆点仍对齐。

## INTER-04 — Loading / Progress / Spinner

**对照 reference**：`interaction-motion.md#加载`、`state-index.md#数据状态`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 按钮 loading | 主按钮 disabled + 左侧 Spinner；文案可保留或变为「提交中…」 | ASYNC-03 |
| 2 | Spinner 位置 | Spinner 在容器内居中或贴文案；不溢出按钮边界 | INTER-04 |
| 3 | Skeleton | 首屏/表格 loading 用 Skeleton 保留结构；非空白闪烁 | ASYNC-01 |
| 4 | Progress | 进度条填充与百分比同步；indeterminate 有循环动画 | INTER-04 |
| 5 | 局部 loading | 区块级 Spinner 不拖垮相邻卡片布局 | ASYNC-04 |

**交互动作**：触发按钮提交 loading → 观察表格 Skeleton → 模拟 partial 区块 loading → 截图 loading 态。

## INTER-05 — 列表 / 表格 / Kanban / Chart 微交互

**对照 golden**：`data-table-dense`、`bi-filter-linkage`、`kanban-column-menu-open`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 排序/筛选 | 表头排序有 hover + active 指示；筛选 chip 添加/移除有过渡 | INTER-05 |
| 2 | 行展开/批量 | 展开行动画不撑破表格外框；批量栏滑入不遮挡分页 | RESP-04 |
| 3 | Kanban | 卡片拖拽或列菜单打开有过渡；列菜单不永久遮挡邻列 | `kanban-theme.md` |
| 4 | Chart hover | 图表 tooltip/highlight 跟随指针；cross-filter 联动有过渡提示 | MS-11 |
| 5 | MS 抽检 | MS-09～13 至少 1 页完成 INTER-02 + INTER-04 组合抽检 | `business-validation-checklist.md` |

**交互动作**：表格排序一列 → 添加 BI 筛选 chip 观察图表联动 → 打开 Kanban 列菜单 → 截图打开态。

## 五类交互与动效速查

| 类型 | 典型信号 | 优先查 | 症状 ID |
|---|---|---|---|
| 基础态 | 无 hover、无 focus 环、禁用仍变色 | `interaction-motion.md` | INTER-01 · A11Y-01 |
| 浮层 | 开关生硬、Esc 无效、遮挡阅读 | `state-index.md` | INTER-02 · DRIFT-05 |
| 布尔控件 | 圆点错位、Slider 脱轨 | preview Form Controls | INTER-03 · DRIFT-05 |
| Loading | Spinner 贴边、按钮双态重叠 | `async-state-review-checklist.md` | INTER-04 · ASYNC-03 |
| 微交互 | 排序无反馈、图表联动生硬 | `golden-screens.md` | INTER-05 · DRIFT-02 |

## 验证命令汇总

```bash
python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix
python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix
# 业务仓库：Playwright hover/focus/打开态截图
pnpm exec playwright test --grep interaction-motion
```

## 写回与下轮演化

以下情况必须写回 `decision-matrix.md` 并在 `docs/spec/b-design-system-tailadmin-radix/state.md` 登记：

- 评审发现**稳定复现**的 Switch 错位、Dialog 无过渡或 loading Spinner 溢出按钮。
- MS 场景组合缺少 observable 交互路径（如流水线阶段无 hover/active、BI 筛选无联动反馈）。
- 检索路径超过 3 跳才找到本清单或对应 INTER 块。

症状 ID 对照：`upgrade-troubleshooting.md` 中 INTER-01（基础态）～ INTER-05（微交互）；场景级 INTER-06～10 见 `scene-interaction-review-checklist.md`。

新增 INTER-* 症状行写入 `upgrade-troubleshooting.md`；可复用检查项可沉淀到本文件对应 INTER 块。

## 场景级交互（INTER-06～10）

控件级 INTER-01～05 完成后，对 BI/Data Screen、DevOps、Gateway、PaaS 与 MS-09～13 领域场景页执行场景级抽检，详见 `scene-interaction-review-checklist.md`（DOCS-023 / G72）。

完整交互与动效评审 = **INTER-01～10**；PR 前至少抽检 INTER-01 + INTER-06 + 1 个 MS INTER-10 场景。

## 检索入口

| 意图 | 读 |
|---|---|
| 时长/缓动/禁止项 | `interaction-motion.md` |
| 状态矩阵 | `state-index.md` |
| 组件/页面正选 | `decision-matrix.md` |
| UI 漂移评审 | `ui-drift-review-checklist.md` |
| 可访问性 focus | `accessibility-review-checklist.md` |
| 响应式与窄屏对齐 | `responsive-review-checklist.md` |
| 异步 loading 反馈 | `async-state-review-checklist.md` |
| 业务部署冒烟 | `business-validation-checklist.md` |
| 症状与回滚 | `upgrade-troubleshooting.md` INTER-* / DRIFT-* / VIS-* |
| Agent ≤3 跳路由 | `agent-retrieval-guide.md` |
