# 升级故障排查与回滚手册

> DOCS-004 / G53 产物。业务项目升级 Skill 快照后若出现类型错误、视觉回归、组件错选或 merge 行为异常，先读本手册按症状路由，再查 `migration-playbook.md` 场景 ID 与 MN/SOR 降级路径。

## 使用顺序

1. `version-pinning-guide.md` — 确认当前 pin 的 commit 与升级目标
2. **本文件** — 按症状定位 MS/MN/SOR 与回滚动作
3. `migration-playbook.md` — 场景路由表与升级检查清单
4. `migration-scenarios.md` — 场景详情、代码片段与降级路径
5. `scenario-override-recipes.md` / `api-override-recipes.md` — 场景或单项 override
6. `merge-options-guide.md` — 嵌套 options 浅/深 merge 选型

## 症状路由表

| 症状 ID | 典型表现 | 优先查 | MS / SOR | 回滚动作 |
|---|---|---|---|---|
| TS-01 | `ThemeToggle` 找不到导出 | `component-index.md` · MN-01 | MS-01 | 改回 `ThemeToggleButton` 或 deprecated wrapper |
| TS-02 | `SearchCommand` 要求 react-router | MN-02 | MS-02 | 使用 `onItemSelect` 或 `SearchCommandStatic` |
| TS-03 | Kanban DnD 类型与 `KanbanBoard` 不兼容 | MN-03 | MS-03 | 暂用 `KanbanLegacyShell` theme class |
| TS-04 | Chart 色板与截图不一致 | `api-override-recipes.md#chart-apexcharts` | MS-04 | pin 旧 sha 或 `getBaseChartOptions` 显式 override |
| TS-05 | FullCalendar 默认视图/工具栏突变 | `merge-options-guide.md` | MS-05 | `getDefaultFullCalendarOptions(overrides?)` 深 merge |
| TS-06 | FileUpload 缺拖拽/进度 | `file-dropzone.tsx` additive | MS-06 | 保留 `FileUpload`，新页才接 `FileDropzone` |
| TS-07 | 代码块不可编辑 | `code-editor-editable.md` | MS-07 | 保留 `CodeBlock` 只读，编辑场景接 `CodeEditor` |
| TS-08 | Command 在无路由环境报错 | `api-override-recipes.md#command-palette` | MS-08 | `ComboboxPanel` 或 `SearchCommandStatic` |
| VIS-01 | 主操作/状态色用默认 Tailwind 色或页面内 hex | `visual-token-review-checklist.md#vis-01` | — | 改用语义 Token；`rg` 扫描硬编码色 |
| VIS-02 | dark 主题对比度丢失或边框层级消失 | `visual-token-review-checklist.md#vis-02` | — | 对比 pin 前后 `index.css` @theme；补 `dark:border-*` |
| VIS-03 | 首屏空白/KPI 栅格过疏或表格过挤 | `visual-token-review-checklist.md#vis-03` | — | 对齐 `golden-screens.md`；desktop 4 列 / tablet 2×2 |
| VIS-04 | 圆角/阴影/z-index 层级错乱或浮层被挡 | `visual-token-review-checklist.md#vis-04` | — | 面板 `rounded-xl`；浮层 `z-99999` |
| VIS-05 | 数字/KPI 错位或大屏只有占位画布 | `visual-token-review-checklist.md#vis-05` | MS-11 | 补 tabular-nums；Chart 走 `chartPaletteCssVars` |
| VIS-06 | BI 大屏 chart 裸色或假占位无真实层次 | `scene-visual-token-review-checklist.md#vis-06` | MS-11 | chartPaletteCssVars；KPI tabular-nums + 信息层次 |
| VIS-07 | CI/CD 阶段无色语义或日志面板过挤裁切 | `scene-visual-token-review-checklist.md#vis-07` | MS-10 | 阶段条 brand/success/error；LogStream 密度对齐 golden |
| VIS-08 | Gateway probe 状态灰一片或配额条无 Token | `scene-visual-token-review-checklist.md#vis-08` | MS-09 | 分步 probe badge 语义色；BalanceQuota Token 填充 |
| VIS-09 | PaaS ConfigDiff 无高亮或危险 Dialog 色不对 | `scene-visual-token-review-checklist.md#vis-09` | MS-12 | diff 行高亮；destructive 确认按钮 |
| VIS-10 | MS 场景视觉密度/色板与 golden 明显漂移 | `scene-visual-token-review-checklist.md#vis-10` | MS-09～13 | 按 MS 表 VIS-01～10 组合抽检 |
| ASYNC-06 | BI 筛选后 KPI/chart 硬切或 chart 白屏无 empty/error | `scene-async-state-review-checklist.md#async-06` | MS-11 | FilterBar chip → KPI loading→刷新；chart lazy 占位 |
| ASYNC-07 | CI/CD 阶段切换日志不同步或 Rollback 无双提交防护 | `scene-async-state-review-checklist.md#async-07` | MS-10 | PipelineStageBar 切换 + LogStream loading；Rollback checking |
| ASYNC-08 | Gateway probe 整表硬切或配额刷新无反馈 | `scene-async-state-review-checklist.md#async-08` | MS-09 | 分步 probe loading→结果；BalanceQuota 刷新过渡 |
| ASYNC-09 | PaaS 危险操作无 checking 或恢复静默失败 | `scene-async-state-review-checklist.md#async-09` | MS-12 | 恢复 Dialog checking；ResourceTable 翻页 loading |
| ASYNC-10 | MS 场景缺 observable loading→success 路径 | `scene-async-state-review-checklist.md#async-10` | MS-09～13 | 按 MS 表 ASYNC-01～10 组合抽检 |
| MER-01 | Carousel/Swiper 嵌套 options 被覆盖 | `merge-options-guide.md` | MS-04～05 | 改用 `mergeSwiperOptionsDeep` |
| MER-02 | Chart series 深嵌套丢失 | `merge-options-guide.md` | MS-04 | `getBaseChartOptions` + `deepMergeOptions` |
| SEL-01 | BI 单图误用 cross-filter 组合 | `decision-matrix.md#bi` | SOR-01 / MS-11 | 降级 `DrillDownDashboard` 或 StatMetric 卡片 |
| SEL-02 | CI/CD 页误用纯 Kanban | `decision-matrix.md#devops` | SOR-02 / MS-10 | 改用 `CicdRunDetail` 或 PipelineStageBar + Table |
| SEL-03 | PaaS 列表缺地图语义 | `decision-matrix.md#paas` | SOR-03 / MS-12 | `ResourceTable` + Maps；纯表降级去掉地图 Card |
| SEL-04 | RBAC 用 Switch 列表替代矩阵 | `decision-matrix.md#治理安全` | SOR-04 / MS-13 | `PermissionMatrix` + `AuditLogTable` 组合 |
| SEL-05 | 网关子面板硬编码 mock | `decision-matrix.md#控制平面` | SOR-05 / MS-09 | `ControlPlaneHub` 受控 props；子面板拆分 |
| VAL-01 | MS-09 端点探测无 loading/结果态 | `business-validation-checklist.md#ms-09` | MS-09 | 补齐 `onProbe` 回调与表格状态 |
| VAL-02 | MS-10 阶段切换与日志不同步 | `business-validation-checklist.md#ms-10` | MS-10 | 受控 `stages` + 当前阶段高亮 |
| VAL-03 | MS-11 筛选 chip 未联动图表 | `business-validation-checklist.md#ms-11` | MS-11 | 受控 `filters` + `chartPaletteCssVars` |
| VAL-04 | MS-12 地图与表格地区语义不一致 | `business-validation-checklist.md#ms-12` | MS-12 | 统一 `regionFilter` / `mapCenter` |
| VAL-05 | MS-13 角色切换未刷新审计表 | `business-validation-checklist.md#ms-13` | MS-13 | `onRoleChange` 同步 `auditQuery` |
| SHEET-01 | 点筛选后全页 blur 但右侧 Drawer 不可见 | `overlay-template.md#sheetcontent-定位` | — | `SheetContent` 仅 `p-0`；禁止 `relative` 覆盖 `fixed` |
| DIALOG-01 | Dialog 关闭后整页不可点 | `engineering-guards.md` 浮层关闭 | — | overlay/content 加 `data-[state=closed]:pointer-events-none` |
| SELECT-01 | Dialog 内 Select 下拉被挡或关闭后挡点击 | `overlay-template.md` | — | `SelectContent` 用 `z-[100000]`；closed 时 `pointer-events-none` |
| OVLY-01 | AlertDialog 取消后整页不可点（生产 build） | `engineering-guards.md` 浮层关闭 | — | 删除页面级 portal cleanup；仅用 Radix `onOpenChange` |
| BTN-01 | `Button asChild loading` 破坏 Link 子节点 | `templates/ui/button.tsx` | — | `asChild` 不注入 spinner；loading 用原生 `<button>` |
| HDR-01 | 顶栏搜索暗色模式双色条 | `list-search-filter-toolbar.md` | — | 单元素 `HeaderSearch`；禁止双层背景外壳 |
| LAYOUT-01 | body `overflow:hidden` 时长页无法滚动 | `gateway-visual.md` · `app-layout.tsx` | — | 外壳 `h-full min-h-screen`；main `flex-1 overflow-y-auto` |
| DRIFT-01 | KPI/卡片间距或密度与 golden 明显不一致 | `ui-drift-review-checklist.md#rev-01` | — | 对齐 `token-index.md`；对比 golden `overview-period` |
| DRIFT-02 | 浮层/菜单用手写 div 而非 Radix/shadcn | `engineering-guards.md` | — | 改用 Dialog/DropdownMenu/Popover |
| DRIFT-03 | 组件或页面选型与 decision-matrix 不符 | `ui-drift-review-checklist.md` + `decision-matrix.md` | SEL-* | 按正选模板替换；写回 when-not |
| DRIFT-04 | 英文 mock/placeholder 无 props 覆盖 | `quality-rubric.md` 中文规则 | — | 中文化或提供 i18n 入口 |
| DRIFT-05 | 截图红线：裁切/空白/遮挡/控件错位 | `ui-drift-review-checklist.md` + `quality-rubric.md` | — | 修布局/浮层层级；重截对照 golden |
| REV-06 | BI 场景 KPI/Chart 密度与 golden 不一致或大屏占位画布 | `scene-ui-drift-review-checklist.md#rev-06` | MS-11 | FilterBar chips + Chart 色板 + `bi-chart-state-gates.png` 对照 |
| REV-07 | CI/CD 阶段条/日志区 framing 错位或危险 Dialog 层级错乱 | `scene-ui-drift-review-checklist.md#rev-07` | MS-10 | PipelineStageBar + LogStream 固定高度 + golden 对照 |
| REV-08 | Gateway Hub 子面板 hex 硬编码或探测 Dialog 遮挡 Tabs | `scene-ui-drift-review-checklist.md#rev-08` | MS-09 | ControlPlaneHub 子面板密度 + 探测 Dialog 层级 |
| REV-09 | PaaS 恢复 Dialog 遮挡表格或 Maps/表格 framing 不一致 | `scene-ui-drift-review-checklist.md#rev-09` | MS-12 | ResourceTable + Maps framing + paas golden 对照 |
| REV-10 | MS 场景与 example runtime golden 明显不一致 | `scene-ui-drift-review-checklist.md#rev-10` | MS-09～13 | 按 MS 表 REV-01～10 组合抽检 |
| FAIL-01 | 首屏主内容过窄或右侧大面积空白 | `agent-failure-patterns-review-checklist.md#fail-01` | — | `app-layout.tsx` + `max-w-(--breakpoint-2xl)`；对照 `dashboard-ai-family.png` |
| FAIL-02 | 多层 Card 嵌套像营销页 | `agent-failure-patterns-review-checklist.md#fail-02` | — | 改用 layout pattern 组合；减少嵌套 Card |
| FAIL-03 | mobile 表格列裁切或行操作不可点 | `agent-failure-patterns-review-checklist.md#fail-03` | MS-12 | 表格 `overflow-x-auto` + sticky 操作列 |
| FAIL-04 | dark 边框/分隔线丢失或控件不可辨认 | `agent-failure-patterns-review-checklist.md#fail-04` | — | 补 `dark:border-gray-800`；对照 dark golden |
| FAIL-05 | 手写 div 弹层无 focus trap/标题 | `agent-failure-patterns-review-checklist.md#fail-05` | — | 改用 Radix Dialog/Drawer；补 DialogTitle |
| FAIL-06 | BI 场景散落 hex 或 Chart 裸色/假占位 | `scene-agent-failure-review-checklist.md#fail-06` | MS-11 | `chartPaletteCssVars`；对照 `bi-chart-state-gates.png` |
| FAIL-07 | DevOps/Gateway 英文 mock 或阶段文案混杂 | `scene-agent-failure-review-checklist.md#fail-07` | MS-09/10 | 中文化 mock；保留 API/CI/CD 固定术语 |
| FAIL-08 | PaaS 恢复 Dialog 遮挡表格或浮层层级错乱 | `scene-agent-failure-review-checklist.md#fail-08` | MS-12 | 调整 z-index；对照 `paas-restore-dialog-open` |
| FAIL-09 | MS 场景仅 happy path 无 empty/error 切换 | `scene-agent-failure-review-checklist.md#fail-09` | MS-09～13 | 补 QueryShell 状态矩阵 + live gates |
| FAIL-10 | example 静态 mock 不可交互或无打开态截图 | `scene-agent-failure-review-checklist.md#fail-10` | MS-09～13 | 跑 `verify:runtime`；补 Specimen Lab 交互 |
| KBF-01 | 按钮/输入 focus 环不可见或 Tab 顺序错乱 | `ui-elements-keyboard-hover-focus-review-checklist.md#kbf-01` | — | 补 `focus-visible:ring-*`；对照 `ui-elements-keyboard-hover-focus-gates.png` |
| KBF-02 | 菜单/分段/标签无法用方向键切换 | `ui-elements-keyboard-hover-focus-review-checklist.md#kbf-02` | — | 改用 Radix roving tabindex；跑 runtime 门禁 |
| KBF-03 | Popover/菜单 Esc 无法关闭或焦点不回 | `ui-elements-keyboard-hover-focus-review-checklist.md#kbf-03` | — | 补 Esc handler + 焦点回触发器 |
| KBF-04 | hover 无反馈或 disabled 仍有 hover 高亮 | `ui-elements-keyboard-hover-focus-review-checklist.md#kbf-04` | — | 对齐 `interaction-motion.md`；禁用 hover |
| KBF-05 | 错误输入无 `aria-invalid` 或 disabled 仍可操作 | `ui-elements-keyboard-hover-focus-review-checklist.md#kbf-05` | — | 补中文错误文案 + disabled 属性 |
| KBF-06 | Modals/Dropdowns Specimen 无键盘路径 | `scene-ui-elements-keyboard-hover-focus-review-checklist.md#kbf-06` | — | 对照 ui-modals + live gates |
| KBF-07 | Tabs/Breadcrumb 无法键盘导航 | `scene-ui-elements-keyboard-hover-focus-review-checklist.md#kbf-07` | — | Arrow 键切换 + mobile 焦点检查 |
| KBF-08 | Switch/Checkbox/Radio hover/focus 错位 | `scene-ui-elements-keyboard-hover-focus-review-checklist.md#kbf-08` | — | 检查轨道尺寸与 focus 环 |
| KBF-09 | Specimen empty/error/loading 英文或无 CTA | `scene-ui-elements-keyboard-hover-focus-review-checklist.md#kbf-09` | — | 中文化失败态 + Skeleton/Spinner |
| KBF-10 | 22 源页矩阵缺键盘束或 runtime 未过 | `scene-ui-elements-keyboard-hover-focus-review-checklist.md#kbf-10` | — | 跑 `verify:runtime` `uiElementKeyboardHoverFocusStates` |
| EEL-01 | 空列表无中文说明或无 CTA | `ui-elements-empty-error-loading-review-checklist.md#eel-01` | — | 中文化空态 + 补新建/刷新按钮 |
| EEL-02 | 错误态无重试或英文 failure copy | `ui-elements-empty-error-loading-review-checklist.md#eel-02` | — | 补中文错误文案 + 重试路径 |
| EEL-03 | Skeleton 塌陷或 loading 可双提交 | `ui-elements-empty-error-loading-review-checklist.md#eel-03` | — | 补 Skeleton/Spinner + disabled 提交 |
| EEL-04 | 错误横幅不可关闭或永久遮挡 | `ui-elements-empty-error-loading-review-checklist.md#eel-04` | — | 补关闭按钮 + `aria-live` |
| EEL-05 | 表格 empty 与筛选无结果混淆 | `ui-elements-empty-error-loading-review-checklist.md#eel-05` | — | 区分「暂无数据」与「无匹配结果」 |
| EEL-06 | Notifications/Progress 仅 happy path | `scene-ui-elements-empty-error-loading-review-checklist.md#eel-06` | — | 对照 ui-notifications + live gates |
| EEL-07 | Ecommerce/Email 表格缺 data-state 矩阵 | `scene-ui-elements-empty-error-loading-review-checklist.md#eel-07` | — | 跑 `ecommerce-crud-live-gates.png` / `email-chat-live-gates.png` |
| EEL-08 | BI 图表面板 error 白屏无重试 | `scene-ui-elements-empty-error-loading-review-checklist.md#eel-08` | — | 对照 `bi-chart-state-gates.png` dataState |
| EEL-09 | 表单提交无 checking 或字段 error 英文 | `scene-ui-elements-empty-error-loading-review-checklist.md#eel-09` | — | 补 async validating + checking 态 |
| EEL-10 | 22 源页缺失败态束或 runtime 未过 | `scene-ui-elements-empty-error-loading-review-checklist.md#eel-10` | — | 跑 `verify:runtime` `uiElementEmptyErrorLoadingStates` |
| VAR-01 | 关键模板变体不足 3 个或不可切换 | `ui-elements-variant-interaction-review-checklist.md#var-01` | — | 补 `ui-var-count` 三门禁变体 + runtime |
| VAR-02 | 语义变体仅改文案不改视觉 | `ui-elements-variant-interaction-review-checklist.md#var-02` | — | 补 success/warning/error 语义色切换 |
| VAR-03 | Segmented/Tabs 无 active 态 | `ui-elements-variant-interaction-review-checklist.md#var-03` | — | 补 active 背景 + `data-state` 索引 |
| VAR-04 | Overlay 无 open 态或无法关闭 | `ui-elements-variant-interaction-review-checklist.md#var-04` | — | 补 Drawer open + 关闭路径 |
| VAR-05 | catalog variants 与 preview 不一致 | `ui-elements-variant-interaction-review-checklist.md#var-05` | — | 对齐 `uiElementSpecimens` 与 UiElementPreview |
| VAR-06 | Buttons/Badges 仅单变体 | `scene-ui-elements-variant-interaction-review-checklist.md#var-06` | — | 对照 `ui-elements-variant-interaction-gates.png` |
| VAR-07 | Cards/Lists 缺布局/hover 变体 | `scene-ui-elements-variant-interaction-review-checklist.md#var-07` | — | 补 metric/media 卡片与行 hover |
| VAR-08 | Modals/Dropdowns 无 open 截图 | `scene-ui-elements-variant-interaction-review-checklist.md#var-08` | — | 对照 live gates + `ui-var-overlay` |
| VAR-09 | Carousel/媒体区占位无交互 | `scene-ui-elements-variant-interaction-review-checklist.md#var-09` | — | 跑 Adapter runtime Swiper 切换 |
| VAR-10 | 22 源页缺 VAR 门禁束 | `scene-ui-elements-variant-interaction-review-checklist.md#var-10` | — | 跑 `verify:runtime` `uiElementVariantInteractionStates` |
| CHART-01 | 折线/柱状无 point hover tooltip | `bi-chart-interaction-review-checklist.md#chart-01` | — | 补 ApexCharts tooltip + `bi-chart-hover-state` |
| CHART-02 | 图例不可点击隐藏系列 | `bi-chart-interaction-review-checklist.md#chart-02` | — | 补 legendClick + `bi-chart-legend-toggle-state` |
| CHART-03 | 趋势图无刷选/缩放选区 | `bi-chart-interaction-review-checklist.md#chart-03` | — | 补 brush/selection + 中文范围标签 |
| CHART-04 | 柱状点击无下钻路径 | `bi-chart-interaction-review-checklist.md#chart-04` | — | 补 dataPointSelection + 返回上级 |
| CHART-05 | 10 类 runtime 缺交互门禁 | `bi-chart-interaction-review-checklist.md#chart-05` | — | 跑 `verify:runtime` `biChartInteractionStates` |
| CHART-06 | Chart Builder 缺深度交互门禁 | `scene-bi-chart-interaction-review-checklist.md#chart-06` | — | 补 interaction gates 四项交互 |
| CHART-07 | Cross-filter 图无联动上下文 | `scene-bi-chart-interaction-review-checklist.md#chart-07` | — | 补筛选 chips + 多 runtime 图 |
| CHART-08 | 指标页缺 10 类 apexcharts marker | `scene-bi-chart-interaction-review-checklist.md#chart-08` | — | 补 `RuntimeChartsGallery` 全类型 |
| CHART-09 | 下钻场景无面包屑/返回 | `scene-bi-chart-interaction-review-checklist.md#chart-09` | — | 补 drill-breadcrumb + detail table |
| CHART-10 | BI 交互束 runtime 失败 | `scene-bi-chart-interaction-review-checklist.md#chart-10` | — | 对照 `bi-chart-interaction-gates.png` |
| CFVR-01 | Sticky 操作栏漂浮遮挡表单字段 | `complex-form-visual-regression-review-checklist.md#cfvr-01` | — | 补 `cfvr-sticky` 贴底门禁 |
| CFVR-02 | Drawer 越界或压入侧栏 | `complex-form-visual-regression-review-checklist.md#cfvr-02` | — | 补 `cfvr-drawer` framing 门禁 |
| CFVR-03 | Dialog 偏移裁切或 guard 不可读 | `complex-form-visual-regression-review-checklist.md#cfvr-03` | — | 补 `cfvr-dialog` 居中门禁 |
| CFVR-04 | 向导步骤指示器挤压重叠 | `complex-form-visual-regression-review-checklist.md#cfvr-04` | — | 补 `cfvr-wizard` 均衡门禁 |
| CFVR-05 | 校验错误被裁切或与操作栏重叠 | `complex-form-visual-regression-review-checklist.md#cfvr-05` | — | 补 `cfvr-validation` 溢出门禁 |
| CFVR-06 | 5 条 complex form flow tab 不可切换 | `scene-complex-form-visual-regression-review-checklist.md#cfvr-06` | — | 补 `complexFormFlows` 矩阵 |
| CFVR-07 | Drawer live overlay 缺 guard 截图 | `scene-complex-form-visual-regression-review-checklist.md#cfvr-07` | — | 对照 `complex-form-drawer-guard.png` |
| CFVR-08 | Dialog live overlay 缺 submitting/guard | `scene-complex-form-visual-regression-review-checklist.md#cfvr-08` | — | 对照 `complex-form-dialog-guard.png` |
| CFVR-09 | Wizard 四步布局在 mobile 挤压 | `scene-complex-form-visual-regression-review-checklist.md#cfvr-09` | — | 补 step indicator 响应式 |
| CFVR-10 | 复杂表单视觉回归束缺五门禁 runtime | `scene-complex-form-visual-regression-review-checklist.md#cfvr-10` | — | 补 `ComplexFormVisualRegressionGates` + 截图 |
| PFVR-01 | 首屏主内容宽度利用率 <80% 或右侧大面积空白 | `page-family-visual-regression-review-checklist.md#pfvr-01` | — | 补响应式栅格 + `pfvr-width` 门禁 |
| PFVR-02 | 主内容压入侧栏或 framing 错位 | `page-family-visual-regression-review-checklist.md#pfvr-02` | — | 补 `pfvr-framing` 对齐门禁 |
| PFVR-03 | KPI/标题/按钮文本裁切或溢出 | `page-family-visual-regression-review-checklist.md#pfvr-03` | — | 补 ellipsis/换行 + `pfvr-clipping` 门禁 |
| PFVR-04 | desktop/tablet/mobile 比例失衡 | `page-family-visual-regression-review-checklist.md#pfvr-04` | — | 补三视口切换 + `pfvr-viewport` 门禁 |
| PFVR-05 | light/dark 对比度不足或层级丢失 | `page-family-visual-regression-review-checklist.md#pfvr-05` | — | 补 `pfvr-theme` 主题门禁 |
| PFVR-06 | 42 子页 tab 矩阵缺截图或 active 校验失败 | `scene-page-family-visual-regression-review-checklist.md#pfvr-06` | — | 跑 `verifyPageFamilyTabs` 全矩阵 |
| PFVR-07 | Dashboard 10 族压成单页或缺 runtime 图 | `scene-page-family-visual-regression-review-checklist.md#pfvr-07` | — | 补独立 dashboard family tab + 图表 |
| PFVR-08 | Layout Variants 移动层 framing 异常 | `scene-page-family-visual-regression-review-checklist.md#pfvr-08` | — | 对照 `layout-variants-mobile-layer.png` |
| PFVR-09 | BI Chart Builder 首屏宽度不足 | `scene-page-family-visual-regression-review-checklist.md#pfvr-09` | — | 对照 `bi-chart-builder-runtime.png` |
| PFVR-10 | 页面族视觉回归束缺五门禁 runtime | `scene-page-family-visual-regression-review-checklist.md#pfvr-10` | — | 补 `PageFamilyVisualRegressionGates` + 截图 |
| SPVR-01 | BI KPI 稀疏堆叠或首屏大面积空白 | `scenario-page-visual-regression-review-checklist.md#spvr-01` | — | 补 `spvr-density` 4 列 KPI 门禁 |
| SPVR-02 | DevOps 流水线阶段条错位 | `scenario-page-visual-regression-review-checklist.md#spvr-02` | — | 补 `spvr-pipeline` framing 门禁 |
| SPVR-03 | Gateway Hub 子面板拥挤重叠 | `scenario-page-visual-regression-review-checklist.md#spvr-03` | — | 补 `spvr-hub` 对齐门禁 |
| SPVR-04 | Governance 表格列溢出或行高不一致 | `scenario-page-visual-regression-review-checklist.md#spvr-04` | — | 补 `spvr-table` 密度门禁 |
| SPVR-05 | PaaS 容量卡片挤压数值裁切 | `scenario-page-visual-regression-review-checklist.md#spvr-05` | — | 补 `spvr-capacity` 布局门禁 |
| SPVR-06 | BI 多页面工作台压成单页 | `scene-scenario-page-visual-regression-review-checklist.md#spvr-06` | — | 补 `tailadmin-bi-analytics` tab 矩阵 |
| SPVR-07 | DevOps 场景缺流水线/日志 framing | `scene-scenario-page-visual-regression-review-checklist.md#spvr-07` | — | 对照 `scenario-devops` section |
| SPVR-08 | Gateway 控制平面 Hub 对齐异常 | `scene-scenario-page-visual-regression-review-checklist.md#spvr-08` | — | 对照 `scenario-gateway` section |
| SPVR-09 | Governance 权限矩阵行列不对齐 | `scene-scenario-page-visual-regression-review-checklist.md#spvr-09` | — | 对照 `scenario-governance` section |
| SPVR-10 | 场景页面视觉回归束缺五门禁 runtime | `scene-scenario-page-visual-regression-review-checklist.md#spvr-10` | — | 补 `ScenarioPageVisualRegressionGates` + 截图 |
| SDIS-01 | BI 场景缺独立截图或 framing 错位 | `scenario-domain-independent-screenshot-review-checklist.md#sdis-01` | — | 补 `scenario-bi-domain.png` + Data Screen tab |
| SDIS-02 | DevOps 场景缺独立截图或流水线首屏不可见 | `scenario-domain-independent-screenshot-review-checklist.md#sdis-02` | — | 补 `scenario-devops-domain.png` + `data-audit="scenario-devops"` |
| SDIS-03 | Gateway 场景缺独立截图或部署矩阵首屏不可见 | `scenario-domain-independent-screenshot-review-checklist.md#sdis-03` | — | 补 `scenario-gateway-domain.png` + `data-audit="scenario-gateway"` |
| SDIS-04 | Governance 场景缺独立截图或权限矩阵首屏不可见 | `scenario-domain-independent-screenshot-review-checklist.md#sdis-04` | — | 补 `scenario-governance-domain.png` + `data-audit="scenario-governance"` |
| SDIS-05 | PaaS 场景缺独立截图或容量卡片首屏不可见 | `scenario-domain-independent-screenshot-review-checklist.md#sdis-05` | — | 补 `scenario-paas-domain.png` + `data-audit="scenario-paas"` |
| SDIS-06 | BI 独立截图 framing 错位或首屏大面积空白 | `scene-scenario-domain-independent-screenshot-review-checklist.md#sdis-06` | — | 对照 `scenario-bi-domain.png` 修复宽度利用 |
| SDIS-07 | DevOps 独立截图流水线/日志区裁切 | `scene-scenario-domain-independent-screenshot-review-checklist.md#sdis-07` | — | 对照 `scenario-devops-domain.png` 修复 framing |
| SDIS-08 | Gateway 独立截图部署矩阵/KPI 对齐异常 | `scene-scenario-domain-independent-screenshot-review-checklist.md#sdis-08` | — | 对照 `scenario-gateway-domain.png` 修复对齐 |
| SDIS-09 | Governance 独立截图权限矩阵/审计表裁切 | `scene-scenario-domain-independent-screenshot-review-checklist.md#sdis-09` | — | 对照 `scenario-governance-domain.png` 修复密度 |
| SDIS-10 | 场景域独立截图束缺 5 域 runtime | `scene-scenario-domain-independent-screenshot-review-checklist.md#sdis-10` | — | 补 `verifyScenarioDomainScreenshots` + 5 张截图 |
| SDLD-01 | BI 场景缺 dark 独立截图或 dark 下 KPI/图表对比度不足 | `scenario-domain-light-dark-screenshot-review-checklist.md#sdld-01` | — | 补 `scenario-bi-domain-dark.png` + Data Screen tab |
| SDLD-02 | DevOps 场景缺 dark 独立截图或流水线 dark 不可见 | `scenario-domain-light-dark-screenshot-review-checklist.md#sdld-02` | — | 补 `scenario-devops-domain-dark.png` + `.app.dark` |
| SDLD-03 | Gateway 场景缺 dark 独立截图或部署矩阵 dark 层级丢失 | `scenario-domain-light-dark-screenshot-review-checklist.md#sdld-03` | — | 补 `scenario-gateway-domain-dark.png` |
| SDLD-04 | Governance 场景缺 dark 独立截图或权限矩阵 dark 对比度不足 | `scenario-domain-light-dark-screenshot-review-checklist.md#sdld-04` | — | 补 `scenario-governance-domain-dark.png` |
| SDLD-05 | PaaS 场景缺 dark 独立截图或容量卡片 dark 不可辨认 | `scenario-domain-light-dark-screenshot-review-checklist.md#sdld-05` | — | 补 `scenario-paas-domain-dark.png` |
| SDLD-06 | BI dark 独立截图 framing 错位或 chart grid 丢失 | `scene-scenario-domain-light-dark-screenshot-review-checklist.md#sdld-06` | — | 对照 `scenario-bi-domain-dark.png` 修复主题对比 |
| SDLD-07 | DevOps dark 独立截图流水线/日志区不可读 | `scene-scenario-domain-light-dark-screenshot-review-checklist.md#sdld-07` | — | 对照 `scenario-devops-domain-dark.png` 修复 dark framing |
| SDLD-08 | Gateway dark 独立截图部署矩阵/KPI 对齐异常 | `scene-scenario-domain-light-dark-screenshot-review-checklist.md#sdld-08` | — | 对照 `scenario-gateway-domain-dark.png` 修复 dark 对齐 |
| SDLD-09 | Governance dark 独立截图权限矩阵/审计表裁切 | `scene-scenario-domain-light-dark-screenshot-review-checklist.md#sdld-09` | — | 对照 `scenario-governance-domain-dark.png` 修复 dark 密度 |
| SDLD-10 | 场景域 light/dark 独立截图束缺 10 张 runtime | `scene-scenario-domain-light-dark-screenshot-review-checklist.md#sdld-10` | — | 补 `verifyScenarioDomainLightDarkScreenshots` + 10 张截图 |
| SDTM-01 | BI 场景缺 tablet/mobile dark 独立截图或 mobile 首屏 KPI 不可见 | `scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-01` | — | 补 `scenario-bi-domain-{tablet,mobile}{,-dark}.png` + Data Screen tab |
| SDTM-02 | DevOps 场景缺 tablet/mobile dark 独立截图或 mobile 流水线不可见 | `scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-02` | — | 补 `scenario-devops-domain-{tablet,mobile}{,-dark}.png` |
| SDTM-03 | Gateway 场景缺 tablet/mobile dark 独立截图或 mobile 部署矩阵层级丢失 | `scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-03` | — | 补 `scenario-gateway-domain-{tablet,mobile}{,-dark}.png` |
| SDTM-04 | Governance 场景缺 tablet/mobile dark 独立截图或 mobile 权限矩阵对比度不足 | `scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-04` | — | 补 `scenario-governance-domain-{tablet,mobile}{,-dark}.png` |
| SDTM-05 | PaaS 场景缺 tablet/mobile dark 独立截图或 mobile 容量卡片不可辨认 | `scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-05` | — | 补 `scenario-paas-domain-{tablet,mobile}{,-dark}.png` |
| SDTM-06 | BI tablet/mobile dark 独立截图 framing 错位或 mobile chart grid 丢失 | `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-06` | — | 对照 `scenario-bi-domain-mobile-dark.png` 修复主题对比 |
| SDTM-07 | DevOps tablet/mobile dark 独立截图流水线/日志区不可读 | `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-07` | — | 对照 `scenario-devops-domain-mobile-dark.png` 修复 dark framing |
| SDTM-08 | Gateway tablet/mobile dark 独立截图部署矩阵/KPI 对齐异常 | `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-08` | — | 对照 `scenario-gateway-domain-mobile-dark.png` 修复 dark 对齐 |
| SDTM-09 | Governance tablet/mobile dark 独立截图权限矩阵/审计表裁切 | `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-09` | — | 对照 `scenario-governance-domain-mobile-dark.png` 修复 dark 密度 |
| SDTM-10 | 场景域 tablet/mobile light/dark 独立截图束缺 20 张 runtime | `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md#sdtm-10` | — | 补 `verifyScenarioDomainViewportLightDarkScreenshots` + 20 张截图 |
| SDIO-01 | BI 场景缺 ShareEmbedDialog tablet/mobile 打开态截图或 Dialog dark 对比度不足 | `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-01` | — | 补 `scenario-bi-domain-{tablet,mobile}{,-dark}-open.png` + Data Screen tab |
| SDIO-02 | DevOps 场景缺 RollbackDialog tablet/mobile 打开态截图 | `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-02` | — | 补 `scenario-devops-domain-{tablet,mobile}{,-dark}-open.png` |
| SDIO-03 | Gateway 场景缺 ApiKeyReveal tablet/mobile 打开态截图 | `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-03` | — | 补 `scenario-gateway-domain-{tablet,mobile}{,-dark}-open.png` |
| SDIO-04 | Governance 场景缺 AuditLog 导出 Drawer tablet/mobile 打开态截图 | `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-04` | — | 补 `scenario-governance-domain-{tablet,mobile}{,-dark}-open.png` |
| SDIO-05 | PaaS 场景缺 OpsDangerFlow tablet/mobile 打开态截图 | `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-05` | — | 补 `scenario-paas-domain-{tablet,mobile}{,-dark}-open.png` |
| SDIO-06 | BI ShareEmbedDialog mobile dark 打开态 framing 错位 | `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-06` | — | 对照 `scenario-bi-domain-mobile-dark-open.png` 修复打开态对比 |
| SDIO-07 | DevOps RollbackDialog mobile dark 打开态无法关闭 | `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-07` | — | 对照 `scenario-devops-domain-mobile-dark-open.png` 修复关闭路径 |
| SDIO-08 | Gateway ApiKeyReveal mobile dark 打开态按钮层级丢失 | `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-08` | — | 对照 `scenario-gateway-domain-mobile-dark-open.png` 修复 dark 对齐 |
| SDIO-09 | Governance AuditLog Drawer mobile dark 打开态 footer 不可读 | `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-09` | — | 对照 `scenario-governance-domain-mobile-dark-open.png` 修复 Drawer 密度 |
| SDIO-10 | 场景域交互态打开态 tablet/mobile light/dark 独立截图束缺 20 张 runtime | `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdio-10` | — | 补 `verifyScenarioDomainInteractiveOpenViewportLightDarkScreenshots` + 20 张 `-open.png` |
| SDPC-01 | BI 场景缺导出 Dropdown tablet/mobile 打开态截图或 dark 对比度不足 | `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-01` | — | 补 `scenario-bi-domain-{tablet,mobile}{,-dark}-dropdown-open.png` |
| SDPC-02 | DevOps 场景缺流水线 Popover tablet/mobile 打开态截图 | `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-02` | — | 补 `scenario-devops-domain-{tablet,mobile}{,-dark}-popover-open.png` |
| SDPC-03 | Gateway 场景缺 Command Palette tablet/mobile 打开态截图 | `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-03` | — | 补 `scenario-gateway-domain-{tablet,mobile}{,-dark}-command-open.png` |
| SDPC-04 | Governance 场景缺审计筛选 Dropdown tablet/mobile 打开态截图 | `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-04` | — | 补 `scenario-governance-domain-{tablet,mobile}{,-dark}-dropdown-open.png` |
| SDPC-05 | PaaS 场景缺容量 Popover tablet/mobile 打开态截图 | `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-05` | — | 补 `scenario-paas-domain-{tablet,mobile}{,-dark}-popover-open.png` |
| SDPC-06 | BI 导出 Dropdown mobile dark 打开态 framing 错位 | `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-06` | — | 对照 `scenario-bi-domain-mobile-dark-dropdown-open.png` 修复打开态对比 |
| SDPC-07 | DevOps Popover mobile dark 打开态无法关闭 | `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-07` | — | 对照 `scenario-devops-domain-mobile-dark-popover-open.png` 修复关闭路径 |
| SDPC-08 | Gateway Command mobile dark 打开态搜索框层级丢失 | `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-08` | — | 对照 `scenario-gateway-domain-mobile-dark-command-open.png` 修复 dark 对齐 |
| SDPC-09 | Governance Dropdown mobile dark 打开态菜单裁切 | `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-09` | — | 对照 `scenario-governance-domain-mobile-dark-dropdown-open.png` 修复菜单密度 |
| SDPC-10 | 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图束缺 20 张 runtime | `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdpc-10` | — | 补 `verifyScenarioDomainFloatingInteractiveOpenViewportLightDarkScreenshots` + 20 张浮层 `-open.png` |
| SDTC-01 | BI 场景缺指标 Tooltip tablet/mobile 打开态截图或 dark 对比度不足 | `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-01` | — | 补 `scenario-bi-domain-{tablet,mobile}{,-dark}-tooltip-open.png` |
| SDTC-02 | DevOps 场景缺流水线 Context Menu tablet/mobile 打开态截图 | `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-02` | — | 补 `scenario-devops-domain-{tablet,mobile}{,-dark}-context-menu-open.png` |
| SDTC-03 | Gateway 场景缺端点 Tooltip tablet/mobile 打开态截图 | `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-03` | — | 补 `scenario-gateway-domain-{tablet,mobile}{,-dark}-tooltip-open.png` |
| SDTC-04 | Governance 场景缺审计行 Context Menu tablet/mobile 打开态截图 | `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-04` | — | 补 `scenario-governance-domain-{tablet,mobile}{,-dark}-context-menu-open.png` |
| SDTC-05 | PaaS 场景缺容量 Tooltip tablet/mobile 打开态截图 | `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-05` | — | 补 `scenario-paas-domain-{tablet,mobile}{,-dark}-tooltip-open.png` |
| SDTC-06 | BI 指标 Tooltip mobile dark 打开态 framing 错位 | `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-06` | — | 对照 `scenario-bi-domain-mobile-dark-tooltip-open.png` 修复打开态对比 |
| SDTC-07 | DevOps Context Menu mobile dark 打开态无法关闭 | `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-07` | — | 对照 `scenario-devops-domain-mobile-dark-context-menu-open.png` 修复关闭路径 |
| SDTC-08 | Gateway Tooltip mobile dark 打开态说明层级丢失 | `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-08` | — | 对照 `scenario-gateway-domain-mobile-dark-tooltip-open.png` 修复 dark 对齐 |
| SDTC-09 | Governance Context Menu mobile dark 打开态菜单裁切 | `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-09` | — | 对照 `scenario-governance-domain-mobile-dark-context-menu-open.png` 修复菜单密度 |
| SDTC-10 | 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图束缺 20 张 runtime | `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md#sdtc-10` | — | 补 `verifyScenarioDomainTooltipContextMenuInteractiveOpenViewportLightDarkScreenshots` + 20 张 `-tooltip-open.png`/`-context-menu-open.png` |
| SDHO-01 | BI 场景指标 Hover tablet/mobile light/dark 截图 framing 异常 | `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-01` | SDTC-01 | 补 `scenario-bi-domain-{tablet,mobile}{,-dark}-hover.png` + hover 移出消失 |
| SDHO-02 | DevOps 阶段 Hover mobile dark 提示不可读 | `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-02` | SDPC-02 | 检查 hover 面板 contrast 与 `ScenarioDomainHoverOverlay` |
| SDHO-03 | Gateway 端点 Hover mobile dark 说明层级丢失 | `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-03` | SDTC-03 | 补 Gateway hover golden + dark theme token |
| SDHO-04 | Governance 审计行 Hover 移出后仍残留面板 | `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-04` | SDTC-04 | 检查 `onMouseLeave` + hover dismiss |
| SDHO-05 | PaaS 容量 Hover mobile dark 列表项不可辨认 | `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-05` | SDTC-05 | 补 PaaS hover golden + 容量摘要文案 |
| SDHO-06 | BI Analytics Hover 四视口截图矩阵缺项 | `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-06` | SDHO-01 | 补 BI 四张 hover 截图 + runtime biDomain |
| SDHO-07 | DevOps Hover 四视口截图矩阵缺项 | `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-07` | SDHO-02 | 补 DevOps 四张 hover 截图 |
| SDHO-08 | Gateway Hover 四视口截图矩阵缺项 | `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-08` | SDHO-03 | 补 Gateway 四张 hover 截图 |
| SDHO-09 | Governance Hover 四视口截图矩阵缺项 | `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-09` | SDHO-04 | 补 Governance 四张 hover 截图 |
| SDHO-10 | 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图束缺 20 张 runtime | `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md#sdho-10` | — | 补 `verifyScenarioDomainHoverViewportLightDarkScreenshots` + 20 张 `-hover.png` |
| SDFK-01 | BI 场景指标 Focus tablet/mobile light/dark 截图 framing 异常 | `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-01` | SDHO-01 | 补 `scenario-bi-domain-{tablet,mobile}{,-dark}-focus.png` + focus Esc 关闭 |
| SDFK-02 | DevOps 阶段 Focus mobile dark 导航不可读 | `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-02` | SDPC-02 | 检查 focus 面板 contrast 与 `ScenarioDomainFocusNavigationOverlay` |
| SDFK-03 | Gateway 端点 Focus mobile dark 说明层级丢失 | `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-03` | SDTC-03 | 补 Gateway focus golden + dark theme token |
| SDFK-04 | Governance 审计行 Focus Esc 后仍残留面板 | `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-04` | SDTC-04 | 检查 Escape handler + focus dismiss |
| SDFK-05 | PaaS 容量 Focus mobile dark 列表项不可辨认 | `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-05` | SDTC-05 | 补 PaaS focus golden + 容量摘要文案 |
| SDFK-06 | BI Analytics Focus 四视口截图矩阵缺项 | `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-06` | SDFK-01 | 补 BI 四张 focus 截图 + runtime biDomain |
| SDFK-07 | DevOps Focus 四视口截图矩阵缺项 | `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-07` | SDFK-02 | 补 DevOps 四张 focus 截图 |
| SDFK-08 | Gateway Focus 四视口截图矩阵缺项 | `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-08` | SDFK-03 | 补 Gateway 四张 focus 截图 |
| SDFK-09 | Governance Focus 四视口截图矩阵缺项 | `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-09` | SDFK-04 | 补 Governance 四张 focus 截图 |
| SDFK-10 | 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图束缺 20 张 runtime | `scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md#sdfk-10` | — | 补 `verifyScenarioDomainFocusKeyboardViewportLightDarkScreenshots` + 20 张 `-focus.png` |
| SDDL-01 | BI 场景指标 disabled/loading tablet/mobile light/dark 截图 framing 异常 | `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-01` | SDFK-01 | 补 `scenario-bi-domain-{tablet,mobile}{,-dark}-{disabled,loading}.png` + disabled 按钮与 loading spinner |
| SDDL-02 | DevOps 阶段 disabled mobile dark 禁用态不可读 | `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-02` | SDFK-02 | 检查 disabled 按钮 contrast 与 `ScenarioDomainDisabledLoadingOverlay` |
| SDDL-03 | Gateway 端点 loading mobile dark spinner 不可辨认 | `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-03` | SDFK-03 | 补 Gateway loading golden + dark theme spinner token |
| SDDL-04 | Governance 审计 loading 文案裁切 | `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-04` | SDFK-04 | 检查 loading 面板 padding 与文案换行 |
| SDDL-05 | PaaS 容量 disabled mobile dark 列表项不可辨认 | `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-05` | SDFK-05 | 补 PaaS disabled golden + 容量摘要文案 |
| SDDL-06 | BI Analytics disabled/loading 八视口截图矩阵缺项 | `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-06` | SDDL-01 | 补 BI 八张 disabled/loading 截图 + runtime biDomain |
| SDDL-07 | DevOps disabled/loading 八视口截图矩阵缺项 | `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-07` | SDDL-02 | 补 DevOps 八张 disabled/loading 截图 |
| SDDL-08 | Gateway disabled/loading 八视口截图矩阵缺项 | `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-08` | SDDL-03 | 补 Gateway 八张 disabled/loading 截图 |
| SDDL-09 | Governance disabled/loading 八视口截图矩阵缺项 | `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-09` | SDDL-04 | 补 Governance 八张 disabled/loading 截图 |
| SDDL-10 | 场景域 disabled/loading tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md#sddl-10` | — | 补 `verifyScenarioDomainDisabledLoadingViewportLightDarkScreenshots` + 40 张 `-disabled.png`/`-loading.png` |
| SDEE-01 | BI 指标 empty/error tablet/mobile light/dark 独立截图缺 golden | `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-01` | — | 补 `scenario-bi-domain-{tablet,mobile}{,-dark}-{empty,error}.png` |
| SDEE-02 | DevOps 阶段 empty/error tablet/mobile light/dark 独立截图缺 golden | `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-02` | — | 补 `scenario-devops-domain-{tablet,mobile}{,-dark}-{empty,error}.png` |
| SDEE-03 | Gateway 端点 empty/error tablet/mobile light/dark 独立截图缺 golden | `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-03` | — | 补 `scenario-gateway-domain-{tablet,mobile}{,-dark}-{empty,error}.png` |
| SDEE-04 | Governance 审计行 empty/error tablet/mobile light/dark 独立截图缺 golden | `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-04` | — | 补 `scenario-governance-domain-{tablet,mobile}{,-dark}-{empty,error}.png` |
| SDEE-05 | PaaS 容量 empty/error tablet/mobile light/dark 独立截图缺 golden | `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-05` | — | 补 `scenario-paas-domain-{tablet,mobile}{,-dark}-{empty,error}.png` |
| SDEE-06 | BI 指标 empty/error 截图矩阵缺门禁 | `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-06` | — | 补 BI 场景 empty/error overlay + 八视口截图 |
| SDEE-07 | DevOps empty/error 截图矩阵缺门禁 | `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-07` | — | 补 DevOps 场景 empty/error overlay + 八视口截图 |
| SDEE-08 | Gateway empty/error 截图矩阵缺门禁 | `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-08` | — | 补 Gateway 场景 empty/error overlay + 八视口截图 |
| SDEE-09 | Governance empty/error 截图矩阵缺门禁 | `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-09` | — | 补 Governance 场景 empty/error overlay + 八视口截图 |
| SDEE-10 | 场景域 empty/error tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md#sdee-10` | — | 补 `verifyScenarioDomainEmptyErrorViewportLightDarkScreenshots` + 40 张 `-empty.png`/`-error.png` |
| SDPR-01 | BI 指标 partial/retry tablet/mobile 截图缺门禁 | `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-01` | — | 补 BI 场景 partial/retry overlay + 八视口截图 |
| SDPR-02 | DevOps 阶段 partial/retry tablet/mobile 截图缺门禁 | `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-02` | — | 补 DevOps 场景 partial/retry overlay + 八视口截图 |
| SDPR-03 | Gateway 端点 partial/retry tablet/mobile 截图缺门禁 | `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-03` | — | 补 Gateway 场景 partial/retry overlay + 八视口截图 |
| SDPR-04 | Governance 审计行 partial/retry tablet/mobile 截图缺门禁 | `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-04` | — | 补 Governance 场景 partial/retry overlay + 八视口截图 |
| SDPR-05 | PaaS 容量 partial/retry tablet/mobile 截图缺门禁 | `scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-05` | — | 补 PaaS 场景 partial/retry overlay + 八视口截图 |
| SDPR-06 | BI 指标 partial/retry 截图矩阵缺门禁 | `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-06` | — | 补 BI 场景 partial/retry overlay + 八视口截图 |
| SDPR-07 | DevOps partial/retry 截图矩阵缺门禁 | `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-07` | — | 补 DevOps 场景 partial/retry overlay + 八视口截图 |
| SDPR-08 | Gateway partial/retry 截图矩阵缺门禁 | `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-08` | — | 补 Gateway 场景 partial/retry overlay + 八视口截图 |
| SDPR-09 | Governance partial/retry 截图矩阵缺门禁 | `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-09` | — | 补 Governance 场景 partial/retry overlay + 八视口截图 |
| SDPR-10 | 场景域 partial/retry tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-partial-retry-viewport-light-dark-screenshot-review-checklist.md#sdpr-10` | — | 补 `verifyScenarioDomainPartialRetryViewportLightDarkScreenshots` + 40 张 `-partial.png`/`-retry.png` |
| SDRP-01 | BI 指标 refetch/pending tablet/mobile 截图缺门禁 | `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-01` | — | 补 BI 场景 refetch/pending overlay + 八视口截图 |
| SDRP-02 | DevOps 阶段 refetch/pending tablet/mobile 截图缺门禁 | `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-02` | — | 补 DevOps 场景 refetch/pending overlay + 八视口截图 |
| SDRP-03 | Gateway 端点 refetch/pending tablet/mobile 截图缺门禁 | `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-03` | — | 补 Gateway 场景 refetch/pending overlay + 八视口截图 |
| SDRP-04 | Governance 审计行 refetch/pending tablet/mobile 截图缺门禁 | `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-04` | — | 补 Governance 场景 refetch/pending overlay + 八视口截图 |
| SDRP-05 | PaaS 容量 refetch/pending tablet/mobile 截图缺门禁 | `scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-05` | — | 补 PaaS 场景 refetch/pending overlay + 八视口截图 |
| SDRP-06 | BI 指标 refetch/pending 截图矩阵缺门禁 | `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-06` | — | 补 BI 场景 refetch/pending overlay + 八视口截图 |
| SDRP-07 | DevOps refetch/pending 截图矩阵缺门禁 | `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-07` | — | 补 DevOps 场景 refetch/pending overlay + 八视口截图 |
| SDRP-08 | Gateway refetch/pending 截图矩阵缺门禁 | `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-08` | — | 补 Gateway 场景 refetch/pending overlay + 八视口截图 |
| SDRP-09 | Governance refetch/pending 截图矩阵缺门禁 | `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-09` | — | 补 Governance 场景 refetch/pending overlay + 八视口截图 |
| SDRP-10 | 场景域 refetch/pending tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-refetch-pending-viewport-light-dark-screenshot-review-checklist.md#sdrp-10` | — | 补 `verifyScenarioDomainRefetchPendingViewportLightDarkScreenshots` + 40 张 `-pending.png`/`-refetch.png` |
| SDSO-01 | BI 指标 stale/optimistic tablet/mobile 截图缺门禁 | `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-01` | — | 补 BI 场景 stale/optimistic overlay + 八视口截图 |
| SDSO-02 | DevOps 阶段 stale/optimistic tablet/mobile 截图缺门禁 | `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-02` | — | 补 DevOps 场景 stale/optimistic overlay + 八视口截图 |
| SDSO-03 | Gateway 端点 stale/optimistic tablet/mobile 截图缺门禁 | `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-03` | — | 补 Gateway 场景 stale/optimistic overlay + 八视口截图 |
| SDSO-04 | Governance 审计行 stale/optimistic tablet/mobile 截图缺门禁 | `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-04` | — | 补 Governance 场景 stale/optimistic overlay + 八视口截图 |
| SDSO-05 | PaaS 容量 stale/optimistic tablet/mobile 截图缺门禁 | `scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-05` | — | 补 PaaS 场景 stale/optimistic overlay + 八视口截图 |
| SDSO-06 | BI 指标 stale/optimistic 截图矩阵缺门禁 | `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-06` | — | 补 BI 场景 stale/optimistic overlay + 八视口截图 |
| SDSO-07 | DevOps stale/optimistic 截图矩阵缺门禁 | `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-07` | — | 补 DevOps 场景 stale/optimistic overlay + 八视口截图 |
| SDSO-08 | Gateway stale/optimistic 截图矩阵缺门禁 | `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-08` | — | 补 Gateway 场景 stale/optimistic overlay + 八视口截图 |
| SDSO-09 | Governance stale/optimistic 截图矩阵缺门禁 | `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-09` | — | 补 Governance 场景 stale/optimistic overlay + 八视口截图 |
| SDSO-10 | 场景域 stale/optimistic tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-stale-optimistic-viewport-light-dark-screenshot-review-checklist.md#sdso-10` | — | 补 `verifyScenarioDomainStaleOptimisticViewportLightDarkScreenshots` + 40 张 `-stale.png`/`-optimistic.png` |
| SDMR-01 | BI 指标 mutation pending/rollback tablet/mobile 截图缺门禁 | `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-01` | — | 补 BI 场景 mutation pending/rollback overlay + 八视口截图 |
| SDMR-02 | DevOps 阶段 mutation pending/rollback tablet/mobile 截图缺门禁 | `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-02` | — | 补 DevOps 场景 mutation pending/rollback overlay + 八视口截图 |
| SDMR-03 | Gateway 端点 mutation pending/rollback tablet/mobile 截图缺门禁 | `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-03` | — | 补 Gateway 场景 mutation pending/rollback overlay + 八视口截图 |
| SDMR-04 | Governance 审计行 mutation pending/rollback tablet/mobile 截图缺门禁 | `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-04` | — | 补 Governance 场景 mutation pending/rollback overlay + 八视口截图 |
| SDMR-05 | PaaS 容量 mutation pending/rollback tablet/mobile 截图缺门禁 | `scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-05` | — | 补 PaaS 场景 mutation pending/rollback overlay + 八视口截图 |
| SDMR-06 | BI 指标 mutation pending/rollback 截图矩阵缺门禁 | `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-06` | — | 补 BI 场景 mutation pending/rollback overlay + 八视口截图 |
| SDMR-07 | DevOps mutation pending/rollback 截图矩阵缺门禁 | `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-07` | — | 补 DevOps 场景 mutation pending/rollback overlay + 八视口截图 |
| SDMR-08 | Gateway mutation pending/rollback 截图矩阵缺门禁 | `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-08` | — | 补 Gateway 场景 mutation pending/rollback overlay + 八视口截图 |
| SDMR-09 | Governance mutation pending/rollback 截图矩阵缺门禁 | `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-09` | — | 补 Governance 场景 mutation pending/rollback overlay + 八视口截图 |
| SDMR-10 | 场景域 mutation pending/rollback tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-mutation-rollback-viewport-light-dark-screenshot-review-checklist.md#sdmr-10` | — | 补 `verifyScenarioDomainMutationRollbackViewportLightDarkScreenshots` + 40 张 `-mutation-pending.png`/`-rollback.png` |
| SDCM-01 | BI 指标 conflict/merge tablet/mobile 截图缺门禁 | `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-01` | — | 补 BI 场景 conflict/merge overlay + 八视口截图 |
| SDCM-02 | DevOps 阶段 conflict/merge tablet/mobile 截图缺门禁 | `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-02` | — | 补 DevOps 场景 conflict/merge overlay + 八视口截图 |
| SDCM-03 | Gateway 端点 conflict/merge tablet/mobile 截图缺门禁 | `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-03` | — | 补 Gateway 场景 conflict/merge overlay + 八视口截图 |
| SDCM-04 | Governance 审计行 conflict/merge tablet/mobile 截图缺门禁 | `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-04` | — | 补 Governance 场景 conflict/merge overlay + 八视口截图 |
| SDCM-05 | PaaS 容量 conflict/merge tablet/mobile 截图缺门禁 | `scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-05` | — | 补 PaaS 场景 conflict/merge overlay + 八视口截图 |
| SDCM-06 | BI 场景 conflict/merge tablet/mobile light/dark 独立截图矩阵缺门禁 | `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-06` | — | 补 BI 场景八视口双主题 conflict/merged 截图 |
| SDCM-07 | DevOps 场景 conflict/merge tablet/mobile light/dark 独立截图矩阵缺门禁 | `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-07` | — | 补 DevOps 场景八视口双主题 conflict/merged 截图 |
| SDCM-08 | Gateway 场景 conflict/merge tablet/mobile light/dark 独立截图矩阵缺门禁 | `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-08` | — | 补 Gateway 场景八视口双主题 conflict/merged 截图 |
| SDCM-09 | Governance 场景 conflict/merge tablet/mobile light/dark 独立截图矩阵缺门禁 | `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-09` | — | 补 Governance 场景八视口双主题 conflict/merged 截图 |
| SDCM-10 | 场景域 conflict/merge tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-conflict-merge-viewport-light-dark-screenshot-review-checklist.md#sdcm-10` | — | 补 `verifyScenarioDomainConflictMergeViewportLightDarkScreenshots` + 40 张 `-conflict.png`/`-merged.png` |
| SDOSC-01 | BI 指标 offline/sync conflict tablet/mobile 截图缺门禁 | `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-01` | — | 补 BI 场景 offline/sync conflict overlay + 八视口截图 |
| SDOSC-02 | DevOps 阶段 offline/sync conflict tablet/mobile 截图缺门禁 | `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-02` | — | 补 DevOps 场景 offline/sync conflict overlay + 八视口截图 |
| SDOSC-03 | Gateway 端点 offline/sync conflict tablet/mobile 截图缺门禁 | `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-03` | — | 补 Gateway 场景 offline/sync conflict overlay + 八视口截图 |
| SDOSC-04 | Governance 审计行 offline/sync conflict tablet/mobile 截图缺门禁 | `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-04` | — | 补 Governance 场景 offline/sync conflict overlay + 八视口截图 |
| SDOSC-05 | PaaS 容量 offline/sync conflict tablet/mobile 截图缺门禁 | `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-05` | — | 补 PaaS 场景 offline/sync conflict overlay + 八视口截图 |
| SDOSC-06 | BI 指标 offline/sync conflict 截图矩阵缺门禁 | `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-06` | — | 补 BI 场景八视口 offline/synced 截图 |
| SDOSC-07 | DevOps offline/sync conflict 截图矩阵缺门禁 | `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-07` | — | 补 DevOps 场景八视口 offline/synced 截图 |
| SDOSC-08 | Gateway offline/sync conflict 截图矩阵缺门禁 | `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-08` | — | 补 Gateway 场景八视口 offline/synced 截图 |
| SDOSC-09 | Governance offline/sync conflict 截图矩阵缺门禁 | `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-09` | — | 补 Governance 场景八视口 offline/synced 截图 |
| SDOSC-10 | 场景域 offline/sync conflict tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md#sdosc-10` | — | 补 `verifyScenarioDomainOfflineSyncConflictViewportLightDarkScreenshots` + 40 张 `-offline.png`/`-synced.png` |
| SDNPR-01 | BI 指标 network partition/recovery tablet/mobile 截图缺门禁 | `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-01` | — | 补 BI 场景 network partition/recovery overlay + 八视口截图 |
| SDNPR-02 | DevOps 阶段 network partition/recovery tablet/mobile 截图缺门禁 | `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-02` | — | 补 DevOps 场景 network partition/recovery overlay + 八视口截图 |
| SDNPR-03 | Gateway 端点 network partition/recovery tablet/mobile 截图缺门禁 | `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-03` | — | 补 Gateway 场景 network partition/recovery overlay + 八视口截图 |
| SDNPR-04 | Governance 审计行 network partition/recovery tablet/mobile 截图缺门禁 | `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-04` | — | 补 Governance 场景 network partition/recovery overlay + 八视口截图 |
| SDNPR-05 | PaaS 容量 network partition/recovery tablet/mobile 截图缺门禁 | `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-05` | — | 补 PaaS 场景 network partition/recovery overlay + 八视口截图 |
| SDNPR-06 | BI 指标 network partition/recovery 截图矩阵缺门禁 | `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-06` | — | 补 BI 场景八视口 partitioned/recovered 截图 |
| SDNPR-07 | DevOps network partition/recovery 截图矩阵缺门禁 | `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-07` | — | 补 DevOps 场景八视口 partitioned/recovered 截图 |
| SDNPR-08 | Gateway network partition/recovery 截图矩阵缺门禁 | `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-08` | — | 补 Gateway 场景八视口 partitioned/recovered 截图 |
| SDNPR-09 | Governance network partition/recovery 截图矩阵缺门禁 | `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-09` | — | 补 Governance 场景八视口 partitioned/recovered 截图 |
| SDNPR-10 | 场景域 network partition/recovery tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md#sdnpr-10` | — | 补 `verifyScenarioDomainNetworkPartitionRecoveryViewportLightDarkScreenshots` + 40 张 `-partitioned.png`/`-recovered.png` |
| SDRHT-01 | BI 指标断连重试/心跳超时 tablet/mobile 截图缺门禁 | `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-01` | — | 补 BI 场景断连重试/心跳超时 overlay + 八视口截图 |
| SDRHT-02 | DevOps 阶段断连重试/心跳超时 tablet/mobile 截图缺门禁 | `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-02` | — | 补 DevOps 场景断连重试/心跳超时 overlay + 八视口截图 |
| SDRHT-03 | Gateway 端点断连重试/心跳超时 tablet/mobile 截图缺门禁 | `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-03` | — | 补 Gateway 场景断连重试/心跳超时 overlay + 八视口截图 |
| SDRHT-04 | Governance 审计行断连重试/心跳超时 tablet/mobile 截图缺门禁 | `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-04` | — | 补 Governance 场景断连重试/心跳超时 overlay + 八视口截图 |
| SDRHT-05 | PaaS 容量断连重试/心跳超时 tablet/mobile 截图缺门禁 | `scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-05` | — | 补 PaaS 场景断连重试/心跳超时 overlay + 八视口截图 |
| SDRHT-06 | BI 指标断连重试/心跳超时截图矩阵缺门禁 | `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-06` | — | 补 BI 场景八视口 retrying/heartbeat-restored 截图 |
| SDRHT-07 | DevOps 断连重试/心跳超时截图矩阵缺门禁 | `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-07` | — | 补 DevOps 场景八视口 retrying/heartbeat-restored 截图 |
| SDRHT-08 | Gateway 断连重试/心跳超时截图矩阵缺门禁 | `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-08` | — | 补 Gateway 场景八视口 retrying/heartbeat-restored 截图 |
| SDRHT-09 | Governance 断连重试/心跳超时截图矩阵缺门禁 | `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-09` | — | 补 Governance 场景八视口 retrying/heartbeat-restored 截图 |
| SDRHT-10 | 场景域断连重试/心跳超时 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-disconnect-retry-heartbeat-timeout-viewport-light-dark-screenshot-review-checklist.md#sdrht-10` | — | 补 `verifyScenarioDomainDisconnectRetryHeartbeatViewportLightDarkScreenshots` + 40 张 `-retrying.png`/`-heartbeat-restored.png` |
| SDSRB-01 | BI 指标 SSE 重连/背压释放 tablet/mobile 截图缺门禁 | `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-01` | — | 补 BI 场景 SSE 重连/背压释放 overlay + 八视口截图 |
| SDSRB-02 | DevOps 阶段 SSE 重连/背压释放 tablet/mobile 截图缺门禁 | `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-02` | — | 补 DevOps 场景 SSE 重连/背压释放 overlay + 八视口截图 |
| SDSRB-03 | Gateway 端点 SSE 重连/背压释放 tablet/mobile 截图缺门禁 | `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-03` | — | 补 Gateway 场景 SSE 重连/背压释放 overlay + 八视口截图 |
| SDSRB-04 | Governance 审计行 SSE 重连/背压释放 tablet/mobile 截图缺门禁 | `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-04` | — | 补 Governance 场景 SSE 重连/背压释放 overlay + 八视口截图 |
| SDSRB-05 | PaaS 容量 SSE 重连/背压释放 tablet/mobile 截图缺门禁 | `scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-05` | — | 补 PaaS 场景 SSE 重连/背压释放 overlay + 八视口截图 |
| SDSRB-06 | BI 指标 SSE 重连/背压释放截图矩阵缺门禁 | `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-06` | — | 补 BI 场景八视口 sse-reconnecting/backpressure-released 截图 |
| SDSRB-07 | DevOps SSE 重连/背压释放截图矩阵缺门禁 | `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-07` | — | 补 DevOps 场景八视口 sse-reconnecting/backpressure-released 截图 |
| SDSRB-08 | Gateway SSE 重连/背压释放截图矩阵缺门禁 | `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-08` | — | 补 Gateway 场景八视口 sse-reconnecting/backpressure-released 截图 |
| SDSRB-09 | Governance SSE 重连/背压释放截图矩阵缺门禁 | `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-09` | — | 补 Governance 场景八视口 sse-reconnecting/backpressure-released 截图 |
| SDSRB-10 | 场景域 SSE 重连/背压释放 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-sse-reconnect-backpressure-viewport-light-dark-screenshot-review-checklist.md#sdsrb-10` | — | 补 `verifyScenarioDomainSseReconnectBackpressureViewportLightDarkScreenshots` + 40 张 `-sse-reconnecting.png`/`-backpressure-released.png` |
| SDLPS-01 | BI 指标长轮询/流式订阅 tablet/mobile 截图缺门禁 | `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-01` | — | 补 BI 场景长轮询/流式订阅 overlay + 八视口截图 |
| SDLPS-02 | DevOps 阶段长轮询/流式订阅 tablet/mobile 截图缺门禁 | `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-02` | — | 补 DevOps 场景长轮询/流式订阅 overlay + 八视口截图 |
| SDLPS-03 | Gateway 端点长轮询/流式订阅 tablet/mobile 截图缺门禁 | `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-03` | — | 补 Gateway 场景长轮询/流式订阅 overlay + 八视口截图 |
| SDLPS-04 | Governance 审计行长轮询/流式订阅 tablet/mobile 截图缺门禁 | `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-04` | — | 补 Governance 场景长轮询/流式订阅 overlay + 八视口截图 |
| SDLPS-05 | PaaS 容量长轮询/流式订阅 tablet/mobile 截图缺门禁 | `scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-05` | — | 补 PaaS 场景长轮询/流式订阅 overlay + 八视口截图 |
| SDLPS-06 | BI 指标长轮询/流式订阅截图矩阵缺门禁 | `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-06` | — | 补 BI 场景八视口 long-polling/stream-subscribed 截图 |
| SDLPS-07 | DevOps 长轮询/流式订阅截图矩阵缺门禁 | `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-07` | — | 补 DevOps 场景八视口 long-polling/stream-subscribed 截图 |
| SDLPS-08 | Gateway 长轮询/流式订阅截图矩阵缺门禁 | `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-08` | — | 补 Gateway 场景八视口 long-polling/stream-subscribed 截图 |
| SDLPS-09 | Governance 长轮询/流式订阅截图矩阵缺门禁 | `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-09` | — | 补 Governance 场景八视口 long-polling/stream-subscribed 截图 |
| SDLPS-10 | 场景域长轮询/流式订阅 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-long-polling-stream-subscription-viewport-light-dark-screenshot-review-checklist.md#sdlps-10` | — | 补 `verifyScenarioDomainLongPollingStreamSubscriptionViewportLightDarkScreenshots` + 40 张 `-long-polling.png`/`-stream-subscribed.png` |
| SDPCDR-01 | BI 指标推送通道降级/恢复 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-01` | — | 补 BI 场景推送通道降级/恢复 overlay + 八视口截图 |
| SDPCDR-02 | DevOps 阶段推送通道降级/恢复 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-02` | — | 补 DevOps 场景推送通道降级/恢复 overlay + 八视口截图 |
| SDPCDR-03 | Gateway 端点推送通道降级/恢复 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-03` | — | 补 Gateway 场景推送通道降级/恢复 overlay + 八视口截图 |
| SDPCDR-04 | Governance 审计行推送通道降级/恢复 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-04` | — | 补 Governance 场景推送通道降级/恢复 overlay + 八视口截图 |
| SDPCDR-05 | PaaS 容量推送通道降级/恢复 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-05` | — | 补 PaaS 场景推送通道降级/恢复 overlay + 八视口截图 |
| SDPCDR-06 | BI 指标推送通道降级/恢复截图矩阵缺门禁 | `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-06` | — | 补 BI 场景八视口 channel-degraded/channel-recovered 截图 |
| SDPCDR-07 | DevOps 推送通道降级/恢复截图矩阵缺门禁 | `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-07` | — | 补 DevOps 场景八视口 channel-degraded/channel-recovered 截图 |
| SDPCDR-08 | Gateway 推送通道降级/恢复截图矩阵缺门禁 | `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-08` | — | 补 Gateway 场景八视口 channel-degraded/channel-recovered 截图 |
| SDPCDR-09 | Governance 推送通道降级/恢复截图矩阵缺门禁 | `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-09` | — | 补 Governance 场景八视口 channel-degraded/channel-recovered 截图 |
| SDPCDR-10 | 场景域推送通道降级/恢复 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-degradation-recovery-viewport-light-dark-screenshot-review-checklist.md#sdpcdr-10` | — | 补 `verifyScenarioDomainPushChannelDegradationRecoveryViewportLightDarkScreenshots` + 40 张 `-channel-degraded.png`/`-channel-recovered.png` |
| SDPCBRL-01 | BI 指标推送通道熔断/限流 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-01` | — | 补 BI 场景推送通道熔断/限流 overlay + 八视口截图 |
| SDPCBRL-02 | DevOps 阶段推送通道熔断/限流 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-02` | — | 补 DevOps 场景推送通道熔断/限流 overlay + 八视口截图 |
| SDPCBRL-03 | Gateway 端点推送通道熔断/限流 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-03` | — | 补 Gateway 场景推送通道熔断/限流 overlay + 八视口截图 |
| SDPCBRL-04 | Governance 审计行推送通道熔断/限流 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-04` | — | 补 Governance 场景推送通道熔断/限流 overlay + 八视口截图 |
| SDPCBRL-05 | PaaS 容量推送通道熔断/限流 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-05` | — | 补 PaaS 场景推送通道熔断/限流 overlay + 八视口截图 |
| SDPCBRL-06 | BI 指标推送通道熔断/限流截图矩阵缺门禁 | `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-06` | — | 补 BI 场景八视口 channel-breaker-open/rate-limit-released 截图 |
| SDPCBRL-07 | DevOps 推送通道熔断/限流截图矩阵缺门禁 | `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-07` | — | 补 DevOps 场景八视口 channel-breaker-open/rate-limit-released 截图 |
| SDPCBRL-08 | Gateway 推送通道熔断/限流截图矩阵缺门禁 | `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-08` | — | 补 Gateway 场景八视口 channel-breaker-open/rate-limit-released 截图 |
| SDPCBRL-09 | Governance 推送通道熔断/限流截图矩阵缺门禁 | `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-09` | — | 补 Governance 场景八视口 channel-breaker-open/rate-limit-released 截图 |
| SDPCBRL-10 | 场景域推送通道熔断/限流 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-circuit-breaker-rate-limit-viewport-light-dark-screenshot-review-checklist.md#sdpcbrl-10` | — | 补 `verifyScenarioDomainPushChannelCircuitBreakerRateLimitViewportLightDarkScreenshots` + 40 张 `-channel-breaker-open.png`/`-rate-limit-released.png` |
| SDPCBQ-01 | BI 指标推送通道背压/队列积压 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-01` | — | 补 BI 场景推送通道背压/队列积压 overlay + 八视口截图 |
| SDPCBQ-02 | DevOps 阶段推送通道背压/队列积压 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-02` | — | 补 DevOps 场景推送通道背压/队列积压 overlay + 八视口截图 |
| SDPCBQ-03 | Gateway 端点推送通道背压/队列积压 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-03` | — | 补 Gateway 场景推送通道背压/队列积压 overlay + 八视口截图 |
| SDPCBQ-04 | Governance 审计行推送通道背压/队列积压 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-04` | — | 补 Governance 场景推送通道背压/队列积压 overlay + 八视口截图 |
| SDPCBQ-05 | PaaS 容量推送通道背压/队列积压 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-05` | — | 补 PaaS 场景推送通道背压/队列积压 overlay + 八视口截图 |
| SDPCBQ-06 | BI 指标推送通道背压/队列积压截图矩阵缺门禁 | `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-06` | — | 补 BI 场景八视口 backpressure-active/queue-drained 截图 |
| SDPCBQ-07 | DevOps 推送通道背压/队列积压截图矩阵缺门禁 | `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-07` | — | 补 DevOps 场景八视口 backpressure-active/queue-drained 截图 |
| SDPCBQ-08 | Gateway 推送通道背压/队列积压截图矩阵缺门禁 | `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-08` | — | 补 Gateway 场景八视口 backpressure-active/queue-drained 截图 |
| SDPCBQ-09 | Governance 推送通道背压/队列积压截图矩阵缺门禁 | `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-09` | — | 补 Governance 场景八视口 backpressure-active/queue-drained 截图 |
| SDPCBQ-10 | 场景域推送通道背压/队列积压 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-backpressure-queue-viewport-light-dark-screenshot-review-checklist.md#sdpcbq-10` | — | 补 `verifyScenarioDomainPushChannelBackpressureQueueViewportLightDarkScreenshots` + 40 张 `-backpressure-active.png`/`-queue-drained.png` |
| SDPCRDL-01 | BI 指标推送通道重试/死信队列 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-01` | — | 补 BI 场景推送通道重试/死信队列 overlay + 八视口截图 |
| SDPCRDL-02 | DevOps 阶段推送通道重试/死信队列 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-02` | — | 补 DevOps 场景推送通道重试/死信队列 overlay + 八视口截图 |
| SDPCRDL-03 | Gateway 端点推送通道重试/死信队列 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-03` | — | 补 Gateway 场景推送通道重试/死信队列 overlay + 八视口截图 |
| SDPCRDL-04 | Governance 审计行推送通道重试/死信队列 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-04` | — | 补 Governance 场景推送通道重试/死信队列 overlay + 八视口截图 |
| SDPCRDL-05 | PaaS 容量推送通道重试/死信队列 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-05` | — | 补 PaaS 场景推送通道重试/死信队列 overlay + 八视口截图 |
| SDPCRDL-06 | BI 指标推送通道重试/死信队列 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-06` | — | 补 BI 场景八视口双主题 retry-active/dead-letter-drained 截图 |
| SDPCRDL-07 | DevOps 阶段推送通道重试/死信队列 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-07` | — | 补 DevOps 场景八视口双主题 retry-active/dead-letter-drained 截图 |
| SDPCRDL-08 | Gateway 端点推送通道重试/死信队列 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-08` | — | 补 Gateway 场景八视口双主题 retry-active/dead-letter-drained 截图 |
| SDPCRDL-09 | Governance 审计行推送通道重试/死信队列 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-09` | — | 补 Governance 场景八视口双主题 retry-active/dead-letter-drained 截图 |
| SDPCRDL-10 | 场景域推送通道重试/死信队列 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-retry-dead-letter-viewport-light-dark-screenshot-review-checklist.md#sdpcrdl-10` | — | 补 `verifyScenarioDomainPushChannelRetryDeadLetterViewportLightDarkScreenshots` + 40 张 `-retry-active.png`/`-dead-letter-drained.png` |
| SDPCAT-01 | BI 指标推送通道后续审计追踪 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-01` | — | 补 BI 场景推送通道后续审计追踪 overlay + 八视口截图 |
| SDPCAT-02 | DevOps 阶段推送通道后续审计追踪 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-02` | — | 补 DevOps 场景推送通道后续审计追踪 overlay + 八视口截图 |
| SDPCAT-03 | Gateway 端点推送通道后续审计追踪 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-03` | — | 补 Gateway 场景推送通道后续审计追踪 overlay + 八视口截图 |
| SDPCAT-04 | Governance 审计行推送通道后续审计追踪 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-04` | — | 补 Governance 场景推送通道后续审计追踪 overlay + 八视口截图 |
| SDPCAT-05 | PaaS 容量推送通道后续审计追踪 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-05` | — | 补 PaaS 场景推送通道后续审计追踪 overlay + 八视口截图 |
| SDPCAT-06 | BI 指标推送通道后续审计追踪 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-06` | — | 补 BI 场景八视口双主题 audit-tracking-pending/audit-tracking-complete 截图 |
| SDPCAT-07 | DevOps 阶段推送通道后续审计追踪 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-07` | — | 补 DevOps 场景八视口双主题 audit-tracking-pending/audit-tracking-complete 截图 |
| SDPCAT-08 | Gateway 端点推送通道后续审计追踪 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-08` | — | 补 Gateway 场景八视口双主题 audit-tracking-pending/audit-tracking-complete 截图 |
| SDPCAT-09 | Governance 审计行推送通道后续审计追踪 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-09` | — | 补 Governance 场景八视口双主题 audit-tracking-pending/audit-tracking-complete 截图 |
| SDPCAT-10 | 场景域推送通道后续审计追踪 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-audit-tracking-viewport-light-dark-screenshot-review-checklist.md#sdpcat-10` | — | 补 `verifyScenarioDomainPushChannelAuditTrackingViewportLightDarkScreenshots` + 40 张 `-audit-tracking-pending.png`/`-audit-tracking-complete.png` |
| SDPCCT-01 | BI 指标推送通道后续合规留痕 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-01` | — | 补 BI 场景推送通道后续合规留痕 overlay + 八视口截图 |
| SDPCCT-02 | DevOps 阶段推送通道后续合规留痕 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-02` | — | 补 DevOps 场景推送通道后续合规留痕 overlay + 八视口截图 |
| SDPCCT-03 | Gateway 端点推送通道后续合规留痕 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-03` | — | 补 Gateway 场景推送通道后续合规留痕 overlay + 八视口截图 |
| SDPCCT-04 | Governance 审计行推送通道后续合规留痕 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-04` | — | 补 Governance 场景推送通道后续合规留痕 overlay + 八视口截图 |
| SDPCCT-05 | PaaS 容量推送通道后续合规留痕 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-05` | — | 补 PaaS 场景推送通道后续合规留痕 overlay + 八视口截图 |
| SDPCCT-06 | BI 指标推送通道后续合规留痕 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-06` | — | 补 BI 场景八视口双主题 compliance-trace-pending/compliance-trace-complete 截图 |
| SDPCCT-07 | DevOps 阶段推送通道后续合规留痕 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-07` | — | 补 DevOps 场景八视口双主题 compliance-trace-pending/compliance-trace-complete 截图 |
| SDPCCT-08 | Gateway 端点推送通道后续合规留痕 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-08` | — | 补 Gateway 场景八视口双主题 compliance-trace-pending/compliance-trace-complete 截图 |
| SDPCCT-09 | Governance 审计行推送通道后续合规留痕 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-09` | — | 补 Governance 场景八视口双主题 compliance-trace-pending/compliance-trace-complete 截图 |
| SDPCCT-10 | 场景域推送通道后续合规留痕 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-compliance-trace-viewport-light-dark-screenshot-review-checklist.md#sdpcct-10` | — | 补 `verifyScenarioDomainPushChannelComplianceTraceViewportLightDarkScreenshots` + 40 张 `-compliance-trace-pending.png`/`-compliance-trace-complete.png` |
| SDPCLF-01 | BI 指标推送通道后续生命周期 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-01` | — | 补 BI 场景推送通道后续生命周期 overlay + 八视口截图 |
| SDPCLF-02 | DevOps 阶段推送通道后续生命周期 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-02` | — | 补 DevOps 场景推送通道后续生命周期 overlay + 八视口截图 |
| SDPCLF-03 | Gateway 端点推送通道后续生命周期 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-03` | — | 补 Gateway 场景推送通道后续生命周期 overlay + 八视口截图 |
| SDPCLF-04 | Governance 审计行推送通道后续生命周期 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-04` | — | 补 Governance 场景推送通道后续生命周期 overlay + 八视口截图 |
| SDPCLF-05 | PaaS 容量推送通道后续生命周期 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-05` | — | 补 PaaS 场景推送通道后续生命周期 overlay + 八视口截图 |
| SDPCLF-06 | BI 指标推送通道后续生命周期 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-06` | — | 补 BI 场景八视口双主题 channel-lifecycle-pending/channel-lifecycle-complete 截图 |
| SDPCLF-07 | DevOps 阶段推送通道后续生命周期 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-07` | — | 补 DevOps 场景八视口双主题 channel-lifecycle-pending/channel-lifecycle-complete 截图 |
| SDPCLF-08 | Gateway 端点推送通道后续生命周期 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-08` | — | 补 Gateway 场景八视口双主题 channel-lifecycle-pending/channel-lifecycle-complete 截图 |
| SDPCLF-09 | Governance 审计行推送通道后续生命周期 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-09` | — | 补 Governance 场景八视口双主题 channel-lifecycle-pending/channel-lifecycle-complete 截图 |
| SDPCLF-10 | 场景域推送通道后续生命周期 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-lifecycle-viewport-light-dark-screenshot-review-checklist.md#sdpclf-10` | — | 补 `verifyScenarioDomainPushChannelLifecycleViewportLightDarkScreenshots` + 40 张 `-channel-lifecycle-pending.png`/`-channel-lifecycle-complete.png` |
| SDPCRET-01 | BI 指标推送通道后续退役 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-01` | — | 补 BI 场景推送通道后续退役 overlay + 八视口截图 |
| SDPCRET-02 | DevOps 阶段推送通道后续退役 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-02` | — | 补 DevOps 场景推送通道后续退役 overlay + 八视口截图 |
| SDPCRET-03 | Gateway 端点推送通道后续退役 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-03` | — | 补 Gateway 场景推送通道后续退役 overlay + 八视口截图 |
| SDPCRET-04 | Governance 审计行推送通道后续退役 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-04` | — | 补 Governance 场景推送通道后续退役 overlay + 八视口截图 |
| SDPCRET-05 | PaaS 容量推送通道后续退役 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-05` | — | 补 PaaS 场景推送通道后续退役 overlay + 八视口截图 |
| SDPCRET-06 | BI 指标推送通道后续退役 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-06` | — | 补 BI 场景八视口双主题 channel-retirement-pending/channel-retirement-complete 截图 |
| SDPCRET-07 | DevOps 阶段推送通道后续退役 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-07` | — | 补 DevOps 场景八视口双主题 channel-retirement-pending/channel-retirement-complete 截图 |
| SDPCRET-08 | Gateway 端点推送通道后续退役 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-08` | — | 补 Gateway 场景八视口双主题 channel-retirement-pending/channel-retirement-complete 截图 |
| SDPCRET-09 | Governance 审计行推送通道后续退役 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-09` | — | 补 Governance 场景八视口双主题 channel-retirement-pending/channel-retirement-complete 截图 |
| SDPCCLN-01 | BI 指标推送通道后续清理 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-01` | — | 补 BI场景推送通道后续清理 overlay + 八视口截图 |
| SDPCCLN-02 | DevOps 阶段推送通道后续清理 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-02` | — | 补 DevOps场景推送通道后续清理 overlay + 八视口截图 |
| SDPCCLN-03 | Gateway 端点推送通道后续清理 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-03` | — | 补 Gateway场景推送通道后续清理 overlay + 八视口截图 |
| SDPCCLN-04 | Governance 审计行推送通道后续清理 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-04` | — | 补 Governance场景推送通道后续清理 overlay + 八视口截图 |
| SDPCCLN-05 | PaaS 容量推送通道后续清理 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-05` | — | 补 PaaS场景推送通道后续清理 overlay + 八视口截图 |
| SDPCCLN-06 | BI Analytics 指标推送通道后续清理 tablet/mobile 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-06` | — | 补 BI场景八视口双主题 channel-cleanup 截图 |
| SDPCCLN-07 | DevOps 阶段推送通道后续清理 tablet/mobile 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-07` | — | 补 DevOps场景八视口双主题 channel-cleanup 截图 |
| SDPCCLN-08 | Gateway 端点推送通道后续清理 tablet/mobile 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-08` | — | 补 Gateway场景八视口双主题 channel-cleanup 截图 |
| SDPCCLN-09 | Governance 审计行推送通道后续清理 tablet/mobile 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-09` | — | 补 Governance场景八视口双主题 channel-cleanup 截图 |
| SDPCCLN-10 | 推送通道后续清理 tablet/mobile light/dark 独立截图束推送通道后续清理 tablet/mobile light/dark 独立截图束缺门禁 | `scene-scenario-domain-push-channel-cleanup-viewport-light-dark-screenshot-review-checklist.md#sdpccln-10` | — | 补 场景`verifyScenarioDomainPushChannelCleanupViewportLightDarkScreenshots` + 40 张截图 |
| SDPCDEST-01 | BI 指标推送通道后续销毁 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-01` | — | 补 BI 场景推送通道后续销毁 overlay + 八视口截图 |
| SDPCDEST-02 | DevOps 阶段推送通道后续销毁 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-02` | — | 补 DevOps 场景推送通道后续销毁 overlay + 八视口截图 |
| SDPCDEST-03 | Gateway 端点推送通道后续销毁 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-03` | — | 补 Gateway 场景推送通道后续销毁 overlay + 八视口截图 |
| SDPCDEST-04 | Governance 审计行推送通道后续销毁 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-04` | — | 补 Governance 场景推送通道后续销毁 overlay + 八视口截图 |
| SDPCDEST-05 | PaaS 容量推送通道后续销毁 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-05` | — | 补 PaaS 场景推送通道后续销毁 overlay + 八视口截图 |
| SDPCDEST-06 | BI Analytics 指标推送通道后续销毁 tablet/mobile 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-06` | — | 补 BI 场景八视口双主题 channel-destruction 截图 |
| SDPCDEST-07 | DevOps 阶段推送通道后续销毁 tablet/mobile 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-07` | — | 补 DevOps 场景八视口双主题 channel-destruction 截图 |
| SDPCDEST-08 | Gateway 端点推送通道后续销毁 tablet/mobile 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-08` | — | 补 Gateway 场景八视口双主题 channel-destruction 截图 |
| SDPCDEST-09 | Governance 审计行推送通道后续销毁 tablet/mobile 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-09` | — | 补 Governance 场景八视口双主题 channel-destruction 截图 |
| SDPCDEST-10 | 推送通道后续销毁 tablet/mobile light/dark 独立截图束缺门禁 | `scene-scenario-domain-push-channel-destruction-viewport-light-dark-screenshot-review-checklist.md#sdpcdest-10` | — | 补 `verifyScenarioDomainPushChannelDestructionViewportLightDarkScreenshots` + 40 张截图 |
| SDPCRET-10 | 场景域推送通道后续退役 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-retirement-viewport-light-dark-screenshot-review-checklist.md#sdpcret-10` | — | 补 `verifyScenarioDomainPushChannelRetirementViewportLightDarkScreenshots` + 40 张 `-channel-retirement-pending.png`/`-channel-retirement-complete.png` |
| SDPCARCH-01 | BI 指标推送通道后续归档 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-01` | — | 补 BI 场景推送通道后续归档 overlay + 八视口截图 |
| SDPCARCH-02 | DevOps 阶段推送通道后续归档 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-02` | — | 补 DevOps 场景推送通道后续归档 overlay + 八视口截图 |
| SDPCARCH-03 | Gateway 端点推送通道后续归档 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-03` | — | 补 Gateway 场景推送通道后续归档 overlay + 八视口截图 |
| SDPCARCH-04 | Governance 审计行推送通道后续归档 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-04` | — | 补 Governance 场景推送通道后续归档 overlay + 八视口截图 |
| SDPCARCH-05 | PaaS 容量推送通道后续归档 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-05` | — | 补 PaaS 场景推送通道后续归档 overlay + 八视口截图 |
| SDPCARCH-06 | BI 指标推送通道后续归档 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-06` | — | 补 BI 场景八视口双主题 channel-archive-pending/channel-archive-complete 截图 |
| SDPCARCH-07 | DevOps 阶段推送通道后续归档 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-07` | — | 补 DevOps 场景八视口双主题 channel-archive-pending/channel-archive-complete 截图 |
| SDPCARCH-08 | Gateway 端点推送通道后续归档 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-08` | — | 补 Gateway 场景八视口双主题 channel-archive-pending/channel-archive-complete 截图 |
| SDPCARCH-09 | Governance 审计行推送通道后续归档 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-09` | — | 补 Governance 场景八视口双主题 channel-archive-pending/channel-archive-complete 截图 |
| SDPCARCH-10 | 场景域推送通道后续归档 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-archive-viewport-light-dark-screenshot-review-checklist.md#sdpcarch-10` | — | 补 `verifyScenarioDomainPushChannelArchiveViewportLightDarkScreenshots` + 40 张 `-channel-archive-pending.png`/`-channel-archive-complete.png` |
| SDPCCR-01 | BI 指标推送通道后续补偿/对账 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-01` | — | 补 BI 场景推送通道后续补偿/对账 overlay + 八视口截图 |
| SDPCCR-02 | DevOps 阶段推送通道后续补偿/对账 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-02` | — | 补 DevOps 场景推送通道后续补偿/对账 overlay + 八视口截图 |
| SDPCCR-03 | Gateway 端点推送通道后续补偿/对账 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-03` | — | 补 Gateway 场景推送通道后续补偿/对账 overlay + 八视口截图 |
| SDPCCR-04 | Governance 审计行推送通道后续补偿/对账 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-04` | — | 补 Governance 场景推送通道后续补偿/对账 overlay + 八视口截图 |
| SDPCCR-05 | PaaS 容量推送通道后续补偿/对账 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-05` | — | 补 PaaS 场景推送通道后续补偿/对账 overlay + 八视口截图 |
| SDPCCR-06 | BI 指标推送通道后续补偿/对账 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-06` | — | 补 BI 场景八视口双主题 compensation-pending/reconciliation-complete 截图 |
| SDPCCR-07 | DevOps 阶段推送通道后续补偿/对账 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-07` | — | 补 DevOps 场景八视口双主题 compensation-pending/reconciliation-complete 截图 |
| SDPCCR-08 | Gateway 端点推送通道后续补偿/对账 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-08` | — | 补 Gateway 场景八视口双主题 compensation-pending/reconciliation-complete 截图 |
| SDPCCR-09 | Governance 审计行推送通道后续补偿/对账 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-09` | — | 补 Governance 场景八视口双主题 compensation-pending/reconciliation-complete 截图 |
| SDPCCR-10 | 场景域推送通道后续补偿/对账 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-compensation-reconciliation-viewport-light-dark-screenshot-review-checklist.md#sdpccr-10` | — | 补 `verifyScenarioDomainPushChannelCompensationReconciliationViewportLightDarkScreenshots` + 40 张 `-compensation-pending.png`/`-reconciliation-complete.png` |
| SDPCAR-01 | BI 指标推送通道后续异步韧性 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-01` | — | 补 BI 场景推送通道后续异步韧性 overlay + 八视口截图 |
| SDPCAR-02 | DevOps 阶段推送通道后续异步韧性 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-02` | — | 补 DevOps 场景推送通道后续异步韧性 overlay + 八视口截图 |
| SDPCAR-03 | Gateway 端点推送通道后续异步韧性 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-03` | — | 补 Gateway 场景推送通道后续异步韧性 overlay + 八视口截图 |
| SDPCAR-04 | Governance 审计行推送通道后续异步韧性 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-04` | — | 补 Governance 场景推送通道后续异步韧性 overlay + 八视口截图 |
| SDPCAR-05 | PaaS 容量推送通道后续异步韧性 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-05` | — | 补 PaaS 场景推送通道后续异步韧性 overlay + 八视口截图 |
| SDPCAR-06 | BI 指标推送通道后续异步韧性 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-06` | — | 补 BI 场景八视口双主题 async-pending/async-recovered 截图 |
| SDPCAR-07 | DevOps 阶段推送通道后续异步韧性 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-07` | — | 补 DevOps 场景八视口双主题 async-pending/async-recovered 截图 |
| SDPCAR-08 | Gateway 端点推送通道后续异步韧性 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-08` | — | 补 Gateway 场景八视口双主题 async-pending/async-recovered 截图 |
| SDPCAR-09 | Governance 审计行推送通道后续异步韧性 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-09` | — | 补 Governance 场景八视口双主题 async-pending/async-recovered 截图 |
| SDPCAR-10 | 场景域推送通道后续异步韧性 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-async-resilience-viewport-light-dark-screenshot-review-checklist.md#sdpcar-10` | — | 补 `verifyScenarioDomainPushChannelAsyncResilienceViewportLightDarkScreenshots` + 40 张 `-async-pending.png`/`-async-recovered.png` |
| SDPCSCIR-01 | BI 指标推送通道订阅确认/幂等重放 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-01` | — | 补 BI 场景推送通道订阅确认/幂等重放 overlay + 八视口截图 |
| SDPCSCIR-02 | DevOps 阶段推送通道订阅确认/幂等重放 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-02` | — | 补 DevOps 场景推送通道订阅确认/幂等重放 overlay + 八视口截图 |
| SDPCSCIR-03 | Gateway 端点推送通道订阅确认/幂等重放 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-03` | — | 补 Gateway 场景推送通道订阅确认/幂等重放 overlay + 八视口截图 |
| SDPCSCIR-04 | Governance 审计行推送通道订阅确认/幂等重放 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-04` | — | 补 Governance 场景推送通道订阅确认/幂等重放 overlay + 八视口截图 |
| SDPCSCIR-05 | PaaS 容量推送通道订阅确认/幂等重放 tablet/mobile 截图缺门禁 | `scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-05` | — | 补 PaaS 场景推送通道订阅确认/幂等重放 overlay + 八视口截图 |
| SDPCSCIR-06 | BI 指标推送通道订阅确认/幂等重放 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-06` | — | 补 BI 场景八视口双主题 subscription-confirm/idempotent-replay 截图 |
| SDPCSCIR-07 | DevOps 阶段推送通道订阅确认/幂等重放 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-07` | — | 补 DevOps 场景八视口双主题 subscription-confirm/idempotent-replay 截图 |
| SDPCSCIR-08 | Gateway 端点推送通道订阅确认/幂等重放 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-08` | — | 补 Gateway 场景八视口双主题 subscription-confirm/idempotent-replay 截图 |
| SDPCSCIR-09 | Governance 审计行推送通道订阅确认/幂等重放 tablet/mobile light/dark 截图矩阵缺门禁 | `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-09` | — | 补 Governance 场景八视口双主题 subscription-confirm/idempotent-replay 截图 |
| SDPCSCIR-10 | 场景域推送通道订阅确认/幂等重放 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-push-channel-subscription-confirm-idempotent-replay-viewport-light-dark-screenshot-review-checklist.md#sdpcscir-10` | — | 补 `verifyScenarioDomainPushChannelSubscriptionConfirmIdempotentReplayViewportLightDarkScreenshots` + 40 张 `-subscription-confirm.png`/`-idempotent-replay.png` |
| SDWRCB-01 | BI 指标 WebSocket 重连/熔断恢复 tablet/mobile 截图缺门禁 | `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-01` | — | 补 BI 场景 WebSocket 重连/熔断恢复 overlay + 八视口截图 |
| SDWRCB-02 | DevOps 阶段 WebSocket 重连/熔断恢复 tablet/mobile 截图缺门禁 | `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-02` | — | 补 DevOps 场景 WebSocket 重连/熔断恢复 overlay + 八视口截图 |
| SDWRCB-03 | Gateway 端点 WebSocket 重连/熔断恢复 tablet/mobile 截图缺门禁 | `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-03` | — | 补 Gateway 场景 WebSocket 重连/熔断恢复 overlay + 八视口截图 |
| SDWRCB-04 | Governance 审计行 WebSocket 重连/熔断恢复 tablet/mobile 截图缺门禁 | `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-04` | — | 补 Governance 场景 WebSocket 重连/熔断恢复 overlay + 八视口截图 |
| SDWRCB-05 | PaaS 容量 WebSocket 重连/熔断恢复 tablet/mobile 截图缺门禁 | `scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-05` | — | 补 PaaS 场景 WebSocket 重连/熔断恢复 overlay + 八视口截图 |
| SDWRCB-06 | BI 指标 WebSocket 重连/熔断恢复截图矩阵缺门禁 | `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-06` | — | 补 BI 场景八视口 reconnecting/circuit-closed 截图 |
| SDWRCB-07 | DevOps WebSocket 重连/熔断恢复截图矩阵缺门禁 | `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-07` | — | 补 DevOps 场景八视口 reconnecting/circuit-closed 截图 |
| SDWRCB-08 | Gateway WebSocket 重连/熔断恢复截图矩阵缺门禁 | `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-08` | — | 补 Gateway 场景八视口 reconnecting/circuit-closed 截图 |
| SDWRCB-09 | Governance WebSocket 重连/熔断恢复截图矩阵缺门禁 | `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-09` | — | 补 Governance 场景八视口 reconnecting/circuit-closed 截图 |
| SDWRCB-10 | 场景域 WebSocket 重连/熔断恢复 tablet/mobile light/dark 独立截图束缺 40 张 runtime | `scene-scenario-domain-websocket-reconnect-circuit-breaker-viewport-light-dark-screenshot-review-checklist.md#sdwrcb-10` | — | 补 `verifyScenarioDomainWebsocketReconnectCircuitBreakerViewportLightDarkScreenshots` + 40 张 `-reconnecting.png`/`-circuit-closed.png` |
| ADOPT-01 | 接入后白屏或 shadcn 组件/alias 报错 | `adoption-onboarding-checklist.md#adopt-01` | — | 对照 `from-zero.md` 补 components.json 与核心 UI |
| ADOPT-02 | Token 未复制导致默认色板或 dark 失效 | `adoption-onboarding-checklist.md#adopt-02` | — | 复制 `@theme` + `@utility menu-*` |
| ADOPT-03 | 无壳层或侧栏/内容 framing 错位 | `adoption-onboarding-checklist.md#adopt-03` | — | 接 AppLayout + ThemeContext + SidebarContext |
| ADOPT-04 | 未记录 pin，升级后不知契约基线 | `adoption-onboarding-checklist.md#adopt-04` | — | 创建 `docs/design-system-pin.md` 并跑 verify |
| ADOPT-05 | 首个业务页组件/页面错选 | `adoption-onboarding-checklist.md#adopt-05` | SEL-* | 按 decision-matrix 正选；跑 REV 对应块 |
| ADOPT-06 | copy 后改模板未登记 upstream | `adoption-onboarding-checklist.md#adopt-06` | UP-* | 读 `upstream-contribution-guide.md`；补 `design-system-upstream.md` |
| UP-01 | runtime 改了未同步 local_skill | `upstream-contribution-guide.md` | — | runtime → local_skill 再登记 |
| UP-02 | 改了 local_skill 未写 upstream | `upstream-contribution-guide.md` | — | 补 `docs/design-system-upstream.md` pending 条目 |
| UP-03 | 业务域组件误标 pending | `upstream-contribution-guide.md` | — | 改 `status: local-only` |
| UP-04 | breaking 未标导致 compat 失败 | `upstream-contribution-guide.md` | TYPE-* | migration note + deprecated wrapper |
| UP-05 | pin 缺 pinned_commit 无法 diff | `version-pinning-guide.md` | ADOPT-04 | 补 `design-system-pin.md` |
| SSR-01 | SSR 构建报 `window`/`document` 未定义 | `ssr-microfrontend-adoption-checklist.md#ssr-01` | — | 壳层与第三方组件加 client 边界 |
| SSR-02 | Chart/Maps/Kanban 等 SSR 白块或构建失败 | `ssr-microfrontend-adoption-checklist.md#ssr-02` | MS-11/12 | dynamic import + StatMetric/表格降级 |
| SSR-03 | hydration 后主题闪白/闪黑 | `ssr-microfrontend-adoption-checklist.md#ssr-03` | — | 对齐 `html.dark` 初始 class 与 ThemeProvider |
| SSR-04 | Dialog/Dropdown hydration mismatch | `ssr-microfrontend-adoption-checklist.md#ssr-04` | — | Portal 仅 client mount；补 TooltipProvider |
| SSR-05 | SSR 环境 MS 场景交互失败 | `ssr-microfrontend-adoption-checklist.md#ssr-05` | MS-09～13 | 跑 business-validation + 写回 decision-matrix |
| MFE-01 | 子应用卸载泄漏或白屏 | `ssr-microfrontend-adoption-checklist.md#mfe-01` | — | 清理 Portal/订阅；补错误边界 |
| MFE-02 | 主/子应用 Token 或 dark 不同步 | `ssr-microfrontend-adoption-checklist.md#mfe-02` | — | 共享 `@theme` 或主应用 dark 事件同步 |
| MFE-03 | 子应用刷新 404 或 basename 错位 | `ssr-microfrontend-adoption-checklist.md#mfe-03` | MS-10 | 对齐 Router basename 与主应用注册路径 |
| MFE-04 | 双顶栏/双侧栏或内容被挤压 | `ssr-microfrontend-adoption-checklist.md#mfe-04` | — | 嵌入模式去掉重复 AppLayout |
| MFE-05 | 微前端升级后 MS 冒烟失败 | `ssr-microfrontend-adoption-checklist.md#mfe-05` | MS-09～13 | 统一 pin；主/子应用分阶段升级 |
| A11Y-01 | Tab 无法到达主任务或 focus 环不可见 | `accessibility-review-checklist.md#a11y-01` | — | 补 `focus-visible`；修正 Tab 顺序与侧栏可见性 |
| A11Y-02 | 表单无 Label 或错误不可读 | `accessibility-review-checklist.md#a11y-02` | — | 补 `htmlFor`/`aria-invalid` + FormMessage 中文 |
| A11Y-03 | Dialog 无标题或 Esc/焦点不回 | `accessibility-review-checklist.md#a11y-03` | — | 改用 Radix Dialog + DialogTitle；关闭回焦 |
| A11Y-04 | 图标按钮无 aria-label | `accessibility-review-checklist.md#a11y-04` | — | 补中文 `aria-label` 或可见文本 |
| A11Y-05 | dark 对比不足或 loading 无反馈 | `accessibility-review-checklist.md#a11y-05` | — | 对齐 Token；补 Spinner/`aria-live` |
| A11Y-06 | BI 筛选 chip 无法键盘清除或图表失败白屏 | `scene-accessibility-review-checklist.md#a11y-06` | MS-11 | FilterBar 键盘清除 + KPI 标签 + chart 降级 |
| A11Y-07 | CI/CD 阶段条不可键盘达或 LogStream 无 aria-live | `scene-accessibility-review-checklist.md#a11y-07` | MS-10 | PipelineStageBar 键盘激活 + Rollback Dialog 标题 |
| A11Y-08 | Gateway 探测 Dialog 无标题或行操作无名称 | `scene-accessibility-review-checklist.md#a11y-08` | MS-09 | 补 DialogTitle + 行操作中文 aria-label |
| A11Y-09 | PaaS 地图无 title 或危险 Dialog 焦点不回 | `scene-accessibility-review-checklist.md#a11y-09` | MS-12 | 地图 iframe title + Dialog 焦点陷阱 |
| A11Y-10 | MS 场景 RBAC 仅 Switch 或 Wizard 无 Label | `scene-accessibility-review-checklist.md#a11y-10` | MS-09～13 | 按 MS 表 A11Y-01～10 组合抽检 |
| RESP-01 | 侧栏遮挡主内容或移动菜单 framing 错位 | `responsive-review-checklist.md#resp-01` | — | 对齐 `state-index.md` 断点；检查 Backdrop 与 margin |
| RESP-02 | 首屏大面积空白或 KPI 数字裁切 | `responsive-review-checklist.md#resp-02` | — | desktop 4 列 / tablet 2×2；补 `max-w-(--breakpoint-2xl)` |
| RESP-03 | mobile Dialog 贴边或长表单溢出 | `responsive-review-checklist.md#resp-03` | — | 改用 bottom Sheet/Drawer；FormSection 单列 |
| RESP-04 | 表格撑破壳层或行操作重叠 | `responsive-review-checklist.md#resp-04` | MS-12 | 容器 `overflow-x-auto`；Master-Detail 窄屏分屏 |
| RESP-05 | BI/大屏在窄屏不可读或假占位 | `responsive-review-checklist.md#resp-05` | MS-11 | FilterBar 换行；ChartPanel 最小高度；地图降级 |
| RESP-06 | BI 筛选挤压图表或 tablet KPI 仍 4 列 | `scene-responsive-review-checklist.md#resp-06` | MS-11 | FilterBar 换行/横滚；KPI 2×2；ChartPanel 最小高度 |
| RESP-07 | CI/CD 阶段条溢出或 LogStream 撑破壳层 | `scene-responsive-review-checklist.md#resp-07` | MS-10 | 阶段条横滚/折行；制品与审批纵向堆叠 |
| RESP-08 | Gateway 探测表撑破或配额卡片贴边 | `scene-responsive-review-checklist.md#resp-08` | MS-09 | 表格 `overflow-x-auto`；BalanceQuota 栅格 |
| RESP-09 | PaaS 表格行操作重叠或地图压扁 | `scene-responsive-review-checklist.md#resp-09` | MS-12 | ResourceTable sticky；Capacity 栅格；地图可读高度 |
| RESP-10 | MS 场景窄屏 framing 反模式 | `scene-responsive-review-checklist.md#resp-10` | MS-09～13 | 按 MS 表 RESP-01～10 组合抽检 |
| ASYNC-01 | 页面长时间空白或 error 无重试 | `async-state-review-checklist.md#async-01` | — | 补 QueryShell Skeleton/error+retry 中文文案 |
| ASYNC-02 | 表格翻页丢态或筛选与空态混淆 | `async-state-review-checklist.md#async-02` | MS-12 | 表级 loading；区分「无匹配结果」与真 empty |
| ASYNC-03 | 表单可双提交或异步校验无反馈 | `async-state-review-checklist.md#async-03` | MS-13 | 提交按钮 disabled+Spinner；AsyncField validating |
| ASYNC-04 | 多面板一错全页白或无 retry | `async-state-review-checklist.md#async-04` | MS-09 | 子面板独立 error；补重试按钮 |
| ASYNC-05 | Chart/地图白屏或重组件阻塞全页 | `async-state-review-checklist.md#async-05` | MS-11 | dynamic import+占位；见 `extension-audit.md` 降级 |
| INTER-01 | 按钮/菜单无 hover 或 focus 环不可见 | `interaction-motion-review-checklist.md#inter-01` | — | 对齐 `interaction-motion.md`；补 `focus-visible:ring-*` |
| INTER-02 | Dialog/Dropdown 开关生硬或无法 Esc 关闭 | `interaction-motion-review-checklist.md#inter-02` | — | 改用 Radix 浮层；补 fade+scale 与 `onOpenChange` |
| INTER-03 | Switch/Slider 圆点错位或轨道脱轨 | `interaction-motion-review-checklist.md#inter-03` | MS-13 | 检查轨道尺寸与 `translate`；窄屏单列对齐 |
| INTER-04 | Spinner 溢出按钮或 loading 双态重叠 | `interaction-motion-review-checklist.md#inter-04` | — | 按钮 disabled+内联 Spinner；表级 Skeleton |
| INTER-05 | 排序/筛选无反馈或图表联动生硬 | `interaction-motion-review-checklist.md#inter-05` | MS-11 | 补表头 active 态；FilterBar chip 过渡 + chart tooltip |
| INTER-06 | BI 大屏 KPI 硬切或假占位无真实层次 | `scene-interaction-review-checklist.md#inter-06` | MS-11 | KPI Skeleton→内容；chart cross-filter 过渡 |
| INTER-07 | CI/CD 阶段无 active 或日志流无滚动反馈 | `scene-interaction-review-checklist.md#inter-07` | MS-10 | PipelineStageBar active 过渡；LogStream 尾部 loading |
| INTER-08 | Gateway probe 整表硬切或配额条无过渡 | `scene-interaction-review-checklist.md#inter-08` | MS-09 | 分步 probe loading→结果；BalanceQuota 填充过渡 |
| INTER-09 | PaaS 危险 Dialog 无过渡或 ConfigDiff 无高亮 | `scene-interaction-review-checklist.md#inter-09` | MS-12 | Dialog fade+scale；diff 行高亮过渡 |
| INTER-10 | MS 场景缺场景级交互路径 | `scene-interaction-review-checklist.md#inter-10` | MS-09～13 | 按 MS 表 INTER-01～10 组合抽检 |
| COPY-01 | 表单 placeholder/helper/校验仍为英文 | `chinese-copy-review-checklist.md#copy-01` | — | 中文化 Label/placeholder/error；或提供 `locale` props |
| COPY-02 | 空态/错误/loading 为英文或无 CTA | `chinese-copy-review-checklist.md#copy-02` | — | 对齐 `state-index.md` 中文状态文案矩阵 |
| COPY-03 | 侧栏/顶栏/页面标题英文直译 | `chinese-copy-review-checklist.md#copy-03` | — | 改中文领域名；对照 `route-index.md` |
| COPY-04 | 网关/DevOps/PaaS/BI mock 英文混杂 | `chinese-copy-review-checklist.md#copy-04` | MS-09～13 | 按 MS 场景替换 mock；技术缩写可保留 |
| COPY-05 | Dialog/Toast/图标按钮英文可读文案 | `chinese-copy-review-checklist.md#copy-05` | — | 中文化标题/按钮；补中文 `aria-label` |
| COPY-06 | BI 筛选/KPI/图表标题或空态仍为英文 | `scene-chinese-copy-review-checklist.md#copy-06` | MS-11 | FilterBar/KPI/图表标题中文化；补中文空态/错误态 CTA |
| COPY-07 | CI/CD 阶段/日志/制品或 Rollback Dialog 英文 | `scene-chinese-copy-review-checklist.md#copy-07` | MS-10 | 阶段/日志/制品中文化；回滚 Dialog 中文标题与按钮 |
| COPY-08 | Gateway License/端点/配额 mock 英文混杂 | `scene-chinese-copy-review-checklist.md#copy-08` | MS-09 | 探测表/配额/License 中文 mock；API Key 术语可保留 |
| COPY-09 | PaaS 资源列头/危险 Dialog/ConfigDiff 英文 | `scene-chinese-copy-review-checklist.md#copy-09` | MS-12 | ResourceTable/ConfigDiff/恢复伸缩 Dialog 中文化 |
| COPY-10 | MS 场景缺场景级中文文案路径 | `scene-chinese-copy-review-checklist.md#copy-10` | MS-09～13 | 按 MS 表 COPY-01～10 组合抽检 |
| LOGIC-01 | 校验仅 toast、无双提交防护或错误不可读 | `form-validation-logic-review-checklist.md#logic-01` | — | blur+submit 内联 FormMessage；提交 disabled+Spinner |
| LOGIC-02 | 删除/吊销/回滚无确认或 Danger Zone 混在主表单 | `form-validation-logic-review-checklist.md#logic-02` | MS-10/12 | AlertDialog + destructive；隔离 DangerZone |
| LOGIC-03 | RBAC 用 Switch 列表或无权限仍可点击 | `form-validation-logic-review-checklist.md#logic-03` | MS-13 | PermissionMatrix + disabled tooltip |
| LOGIC-04 | 向导可跳步、probe 无结果或一步提交全部 | `form-validation-logic-review-checklist.md#logic-04` | MS-09/13 | 分步局部校验；probe loading→结果 |
| LOGIC-05 | 列表缺编辑/删除或 dirty 关闭丢数据 | `form-validation-logic-review-checklist.md#logic-05` | MS-11 | CRUD 闭环；FormDialog dirty 确认 |
| LOGIC-06 | 返回丢筛选/分页或列表→详情导航断裂 | `logic-completeness-review-checklist.md#logic-06` | PAT-02 | 面包屑+返回保留 URL 筛选/页码 |
| LOGIC-06 | BI 筛选 chips 无 KPI/图表因果或下钻返回丢筛选 | `scene-logic-completeness-review-checklist.md#logic-06` | MS-11 | FilterBar + CrossFilter + DrillBreadcrumb 因果链 |
| LOGIC-07 | 筛选变更无结果反馈或清除无效 | `logic-completeness-review-checklist.md#logic-07` | MS-11 | FilterBar chip 因果链 + 无结果空态 |
| LOGIC-07 | CI/CD 阶段可跳步或 Rollback 无确认/日志不同步 | `scene-logic-completeness-review-checklist.md#logic-07` | MS-10 | PipelineStageBar 依赖 + LogStream 联动 + Rollback 确认 |
| LOGIC-08 | Master-Detail 切换丢 Tab/翻页丢选中 | `logic-completeness-review-checklist.md#logic-08` | MS-10/12 | 选中高亮 + 详情 Tab 状态保留 |
| LOGIC-08 | Gateway probe 无分步或配额超限仍可提交 | `scene-logic-completeness-review-checklist.md#logic-08` | MS-09 | EndpointProbe 分步 + BalanceQuota disabled |
| LOGIC-09 | 配额超限仍可提交或审批流不可见 | `logic-completeness-review-checklist.md#logic-09` | MS-09/10 | BalanceQuota disabled + ApprovalTimeline |
| LOGIC-09 | PaaS 筛选与地图不一致或危险操作无审批 | `scene-logic-completeness-review-checklist.md#logic-09` | MS-12 | ResourceTable 筛选 + 恢复/伸缩 Dialog 审批闭环 |
| LOGIC-10 | MS 场景缺 probe/联动/审计业务闭环 | `logic-completeness-review-checklist.md#logic-10` | MS-09～13 | 按 MS 表 LOGIC-01～10 组合抽检 |
| LOGIC-10 | MS 场景缺场景级逻辑完备路径 | `scene-logic-completeness-review-checklist.md#logic-10` | MS-09～13 | 按 MS 表 LOGIC-01～10 场景组合抽检 |
| TYPE-01 | props 缺失/重命名或 `tsc` 报导出名错误 | `type-api-contract-review-checklist.md#type-01` | TS-* | 对照 `api-contracts.md`；禁止 `@ts-ignore` |
| TYPE-02 | Chart/Calendar override 嵌套类型丢失 | `type-api-contract-review-checklist.md#type-02` | MS-11 | `getBaseChartOptions`/`getDefaultFullCalendarOptions` deep merge |
| TYPE-03 | 受控 props 断裂或 Kanban/DataTable 类型不匹配 | `type-api-contract-review-checklist.md#type-03` | MS-10/12 | 对齐 `extension-audit.md` 受控契约 |
| TYPE-04 | 升级后大面积 TS 错误或无 migration note | `type-api-contract-review-checklist.md#type-04` | MN-* | pin 回滚；用 deprecated wrapper |
| TYPE-05 | MS 场景子面板 props 与模板契约不一致 | `type-api-contract-review-checklist.md#type-05` | MS-09～13 | 受控 props；跑 `audit_compat_contracts.py` |
| TYPE-06 | BI 场景 Chart override 编译报错或 chips 受控类型断裂 | `scene-type-api-contract-review-checklist.md#type-06` | MS-11 | FilterBar chips + `getBaseChartOptions(overrides?)` + CrossFilter 类型联动 |
| TYPE-07 | CI/CD stages 受控类型与 LogStream 流式 props 不匹配 | `scene-type-api-contract-review-checklist.md#type-07` | MS-10 | PipelineStageBar `stages` 受控 + LogStream 流式 props 类型闭合 |
| TYPE-08 | Gateway Hub 子面板 props 与 api-contracts 不一致 | `scene-type-api-contract-review-checklist.md#type-08` | MS-09 | ControlPlaneHub 子面板受控 props + `onProbe` 回调类型 |
| TYPE-09 | PaaS ResourceTable row type 或 Maps override 类型丢失 | `scene-type-api-contract-review-checklist.md#type-09` | MS-12 | ResourceTable row type + `mergeMapLibreOptions` center/zoom |
| TYPE-10 | MS 场景缺场景级类型契约路径 | `scene-type-api-contract-review-checklist.md#type-10` | MS-09～13 | 按 MS 表 TYPE-01～10 组合抽检 |
| GEN-01 | 同类页面组件/浮层选型不一致或 Kanban/Switch 误选 | `generation-consistency-review-checklist.md#gen-01` | SEL-* | 按 decision-matrix 正选；写回 when-not |
| GEN-02 | 同类页面 Token/间距/密度漂移 | `generation-consistency-review-checklist.md#gen-02` | — | 对齐 `token-index.md` + golden screens |
| GEN-03 | loading/empty/hover 状态表现不一致 | `generation-consistency-review-checklist.md#gen-03` | — | 对齐 `state-index.md` 状态矩阵 |
| GEN-04 | Agent 检索路径 >3 跳或误扫描 templates/ | `generation-consistency-review-checklist.md#gen-04` | — | 按 `agent-retrieval-guide.md` 路由表修正 |
| GEN-05 | MS 场景组合与模板契约/受控 props 不一致 | `generation-consistency-review-checklist.md#gen-05` | MS-09～13 | 按 MS 表正选；跑 business-validation |
| GEN-06 | BI 单图冒充联动或 KPI/图表组合漂移 | `scene-generation-consistency-review-checklist.md#gen-06` | MS-11 | FilterBar + CrossFilterDashboard；对齐 chartPaletteCssVars |
| GEN-07 | CI/CD 误用 Kanban 或阶段/日志密度不一致 | `scene-generation-consistency-review-checklist.md#gen-07` | MS-10 | PipelineStageBar + LogStream + ArtifactTable 正选 |
| GEN-08 | Gateway 散落 mock Card 或非受控 Hub | `scene-generation-consistency-review-checklist.md#gen-08` | MS-09 | ControlPlaneHub 受控 props + 探测表组合 |
| GEN-09 | PaaS 扁平表硬塞地图或 ConfigDiff 模式漂移 | `scene-generation-consistency-review-checklist.md#gen-09` | MS-12 | ResourceTable + 可选 Maps + ConfigDiff 正选 |
| GEN-10 | MS 场景缺场景级生成一致性路径 | `scene-generation-consistency-review-checklist.md#gen-10` | MS-09～13 | 按 MS 表 GEN-01～10 组合抽检 |
| COV-01 | 主路径组件缺模板或 component-index 未登记 | `component-coverage-review-checklist.md#cov-01` | — | 补 `templates/` + 更新 component-index when/when-not |
| COV-02 | extension-audit partial 或复杂组件仅 CSS mock | `component-coverage-review-checklist.md#cov-02` | AUDIT-001 | 补可复制模板/theme lib；跑 audit_override_recipes |
| COV-03 | 主路径模板无 preview section 或 golden 截图缺失 | `component-coverage-review-checklist.md#cov-03` | PREVIEW-* | 补 preview panel + golden-screens 注册 |
| COV-04 | Form/Buttons/Overlays/DataTable 变体明显不足 | `component-coverage-review-checklist.md#cov-04` | — | 补变体矩阵；对照 state-index |
| COV-05 | MS 场景缺领域 `templates/*/` 组合模板 | `component-coverage-review-checklist.md#cov-05` | MS-09～13 | 按 SOR 食谱补领域模板；跑 business-validation |
| COV-06 | BI 场景缺 `templates/bi/*` 或 Chart 仅 CSS mock | `scene-component-coverage-review-checklist.md#cov-06` | MS-11 | FilterBar + CrossFilterDashboard + Chart theme lib |
| COV-07 | CI/CD 误用 Kanban 或缺 `templates/devops/*` 组合 | `scene-component-coverage-review-checklist.md#cov-07` | MS-10 | PipelineStageBar + LogStream + ArtifactTable 正选 |
| COV-08 | Gateway 散落 mock Card 或缺 `templates/gateway/*` | `scene-component-coverage-review-checklist.md#cov-08` | MS-09 | ControlPlaneHub 子面板 + 领域模板路径 |
| COV-09 | PaaS 缺 ResourceTable/ConfigDiff 模板或 Maps 无 theme lib | `scene-component-coverage-review-checklist.md#cov-09` | MS-12 | ResourceTable + 可选 Maps + ConfigDiff 正选 |
| COV-10 | MS 场景缺场景级组件覆盖率路径 | `scene-component-coverage-review-checklist.md#cov-10` | MS-09～13 | 按 MS 表 COV-01～10 组合抽检 |
| PAT-01 | 任务类型不明或缺 output mode 指引 | `pattern-coverage-review-checklist.md#pat-01` | — | 按 from-zero/migration/missing-component 路由 |
| PAT-02 | 页面模式错选或 route-index 无相似路径 | `pattern-coverage-review-checklist.md#pat-02` | SEL-* | 先读 pattern-index 决策树；补 route-index |
| PAT-03 | 布局组合缺失（Hub/Master-Detail/向导） | `pattern-coverage-review-checklist.md#pat-03` | — | 对照 form-composition 与 layout-patterns |
| PAT-04 | 状态模式不足（仅 happy path） | `pattern-coverage-review-checklist.md#pat-04` | ASYNC-* | 对齐 state-index；补 loading/empty/error |
| PAT-05 | MS 场景缺完整页面组合或 preview 占位 | `pattern-coverage-review-checklist.md#pat-05` | MS-09～13 | 按 domain-scenarios + SOR 补场景 layout |
| PAT-06 | BI 场景缺 layout pattern 或大屏占位画布 | `scene-pattern-coverage-review-checklist.md#pat-06` | MS-11 | bi-filter-linkage + CrossFilterDashboard + data-screen-canvas |
| PAT-07 | CI/CD 误用 Kanban 或缺 pipeline/master-detail 页面模式 | `scene-pattern-coverage-review-checklist.md#pat-07` | MS-10 | CicdRunDetail + master-detail-ops 正选 |
| PAT-08 | Gateway 散落 Card 或缺 Hub/控制平面 layout | `scene-pattern-coverage-review-checklist.md#pat-08` | MS-09 | ControlPlaneHub Hub 布局 + gateway layout |
| PAT-09 | PaaS 缺 table-list/detail-page 模式或危险流程布局漂移 | `scene-pattern-coverage-review-checklist.md#pat-09` | MS-12 | ResourceTable + detail-page + ops-danger-flow |
| PAT-10 | MS 场景缺场景级页面模式路径 | `scene-pattern-coverage-review-checklist.md#pat-10` | MS-09～13 | 按 MS 表 PAT-01～10 组合抽检 |
| CON-01 | 页面内 `#hex`/裸色值或 dark 边框层级丢失 | `constraint-compliance-review-checklist.md#con-01` | — | 对齐 `token-index.md` + VIS-01～02 |
| CON-02 | 手写 div 弹层或非 Radix 浮层实现 | `constraint-compliance-review-checklist.md#con-02` | — | 改用 `@/components/ui/*` Radix 包装 |
| CON-03 | 深层相对 import 或 SSR 直渲 Chart/Maps | `constraint-compliance-review-checklist.md#con-03` | SSR-* | dynamic import + `engineering-guards.md` |
| CON-04 | 英文默认 mock/品牌路由硬编码 | `constraint-compliance-review-checklist.md#con-04` | COPY-* | 中文化 + 移除项目专有字符串 |
| CON-05 | MS 场景工程边界违规（Token+API+文案组合） | `constraint-compliance-review-checklist.md#con-05` | MS-09～13 | 按 MS 表约束遵守列逐项修复 |
| CON-06 | BI 筛选硬编码色或 Chart SSR 直渲 | `scene-constraint-compliance-review-checklist.md#con-06` | MS-11 | FilterBar 语义 Token；Chart dynamic + `chartPaletteCssVars` |
| CON-07 | CI/CD 手写 div 弹层或英文阶段文案 | `scene-constraint-compliance-review-checklist.md#con-07` | MS-10 | 改用 Radix 浮层；LogStream client-only；阶段中文化 |
| CON-08 | Gateway 探测表裸色值或非受控 props | `scene-constraint-compliance-review-checklist.md#con-08` | MS-09 | 受控 props + 语义 Token badge + 配额中文 mock |
| CON-09 | PaaS Maps SSR 直渲或 ConfigDiff `#hex` | `scene-constraint-compliance-review-checklist.md#con-09` | MS-12 | Maps client-only；diff 语义背景 Token |
| CON-10 | MS 场景 Token+API+文案组合违规 | `scene-constraint-compliance-review-checklist.md#con-10` | MS-09～13 | 按 MS 表 CON-01～10 组合抽检 |
| RUN-01 | `audit_compat_contracts.py` 失败 | `api-contracts.md` | 对应 MS | 按失败项查 MN 或 override 食谱 |
| RUN-02 | `audit_migration_drills.py` 失败 | `migration-notes/` | MS-01～03 | 补齐 MN 验证清单或 wrapper |
| RUN-03 | `tsc --noEmit` 通过但页面白屏 | `engineering-guards.md` | — | 查 Radix Portal 容器与 ThemeProvider |
| RUN-04 | `run_token_hit_tests.py` 未命中或检索路径过长 | `agent-retrieval-guide.md` | — | 按任务路由表修正索引入口；更新 token-index |

## 回滚决策树

```
升级后出现回归？
├─ 类型错误 → 症状路由表 TS-* → 对应 MN / additive 模板
├─ 视觉回归 → VIS-01～05 → visual-token-review-checklist；VIS-06～10 → scene-visual-token-review-checklist
├─ merge 行为异常 → MER-* → merge-options-guide 深 merge
├─ 组件/页面错选 → SEL-* → decision-matrix 正例 + SOR 降级注释
├─ 生成 UI 漂移评审 → DRIFT-* → ui-drift-review-checklist 对应 REV 块；REV-06～10 → scene-ui-drift-review-checklist
├─ 首次接入失败 → ADOPT-* → adoption-onboarding-checklist 对应 ADOPT 块
├─ SSR/hydration 失败 → SSR-* → ssr-microfrontend-adoption-checklist 对应 SSR 块
├─ 微前端嵌入失败 → MFE-* → ssr-microfrontend-adoption-checklist 对应 MFE 块
├─ 可访问性抽检失败 → A11Y-01～05 → accessibility-review-checklist 对应 A11Y 块；A11Y-06～10 → scene-accessibility-review-checklist
├─ 响应式抽检失败 → RESP-01～05 → responsive-review-checklist 对应 RESP 块；RESP-06～10 → scene-responsive-review-checklist
├─ 异步状态抽检失败 → ASYNC-01～05 → async-state-review-checklist；ASYNC-06～10 → scene-async-state-review-checklist
├─ 交互与动效抽检失败 → INTER-01～05 → interaction-motion-review-checklist；INTER-06～10 → scene-interaction-review-checklist
├─ 中文文案抽检失败 → COPY-01～05 → chinese-copy-review-checklist 对应 COPY 块；COPY-06～10 → scene-chinese-copy-review-checklist
├─ 逻辑完备抽检失败 → LOGIC-01～05 → form-validation-logic-review-checklist；LOGIC-06～10 页面级 → logic-completeness-review-checklist；LOGIC-06～10 场景级 → scene-logic-completeness-review-checklist
├─ 类型契约抽检失败 → TYPE-01～05 → type-api-contract-review-checklist 对应 TYPE 块；TYPE-06～10 → scene-type-api-contract-review-checklist
├─ 生成一致性抽检失败 → GEN-01～05 → generation-consistency-review-checklist 对应 GEN 块；GEN-06～10 → scene-generation-consistency-review-checklist
├─ 组件覆盖率抽检失败 → COV-01～05 → component-coverage-review-checklist 对应 COV 块；COV-06～10 → scene-component-coverage-review-checklist
├─ 模式覆盖抽检失败 → PAT-01～05 → pattern-coverage-review-checklist 对应 PAT 块；PAT-06～10 → scene-pattern-coverage-review-checklist
├─ 约束遵守抽检失败 → CON-01～05 → constraint-compliance-review-checklist 对应 CON 块；CON-06～10 → scene-constraint-compliance-review-checklist
└─ 审计/CI 失败 → RUN-* → 先修契约再重新 pin
```

### 紧急回滚（生产）

1. **Submodule / vendor pin**：`git checkout <old-sha>` 于 design-system 目录。
2. **Vendored copy**：从备份分支恢复 `src/components/tailadmin/`。
3. **单组件隔离**：启用 `templates/ui/deprecated/` 对应 wrapper，业务 import 不改路径。
4. **场景降级**：在 SOR 食谱中查找 `// 降级：` 注释块，临时移除跨组件组合。

回滚后必须在业务 `docs/design-system-pin.md` 记录旧 sha 与回滚原因。

## 与 migration-playbook 的衔接

| playbook 演练类型 | 故障时读本手册 |
|---|---|
| MN 演练（MS-01～03） | TS-01～03 + 各 MN「兼容期与回滚」 |
| 预防性 override（MS-04～08） | TS-04～08、MER-01～02 |
| additive 升级（MS-06～07） | 保留旧组件；新能力仅新页面接入 |
| 场景组合（MS-09～13） | SEL-01～05 + SOR 降级块 |

## 选型纠错写回

若故障根因是组件或页面错选（非 Skill breaking），必须：

1. 在 `decision-matrix.md` 补充 when-not 反例（若缺失）。
2. 在对应 SOR 食谱标注「常见误选 → 正选」。
3. 将修复项写入 `docs/spec/b-design-system-tailadmin-radix/state.md` 下轮选题（若需模板级修复）。

## 验证清单

升级或回滚后按序执行：

- [ ] `python3 create-design-system/scripts/audit_migration_drills.py b-design-system-tailadmin-radix`
- [ ] `python3 create-design-system/scripts/audit_override_recipes.py b-design-system-tailadmin-radix`
- [ ] `python3 create-design-system/scripts/audit_compat_contracts.py b-design-system-tailadmin-radix`
- [ ] `python3 create-design-system/scripts/verify_design_system.py b-design-system-tailadmin-radix`
- [ ] 业务侧 `tsc --noEmit`
- [ ] 关键页面 light/dark 截图对比（无首屏空白、无文本裁切）

## 检索入口

| 意图 | 读 |
|---|---|
| 按症状排查 | 本文件症状路由表 |
| 按场景 ID 排查 | `migration-playbook.md` 场景路由表 |
| 已填写 migration note 回滚 | `migration-notes/` 各 MN「兼容期与回滚」 |
| 固定快照再升级 | `version-pinning-guide.md` |
| 嵌套 merge 异常 | `merge-options-guide.md` |
| 组件/页面选型 | `decision-matrix.md` |
| Agent 检索路径 / ≤3 跳规则 | `agent-retrieval-guide.md` |
| UI 漂移评审 / PR 前抽检 | `ui-drift-review-checklist.md` + `scene-ui-drift-review-checklist.md` |
| 首次接入 / vendoring | `adoption-onboarding-checklist.md` |
| SSR / 微前端接入 | `ssr-microfrontend-adoption-checklist.md` |
| 中文示例文案评审 / PR 前抽检 | `chinese-copy-review-checklist.md` |
| 生成一致性评审 / PR 前抽检 | `generation-consistency-review-checklist.md` |
| 组件覆盖率评审 / PR 前抽检 | `component-coverage-review-checklist.md` |
