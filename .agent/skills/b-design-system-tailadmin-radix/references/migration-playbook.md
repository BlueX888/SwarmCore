# 迁移演练手册

> DOCS-003 / G51–G52 产物。统一 MS-01～MS-13 预防性场景到 MN 演练、override 食谱或组件升级路径的检索入口。发生真实破坏性变更时，先读本手册路由，再查 `migration-scenarios.md` 详情。

## 使用顺序

1. `version-pinning-guide.md` — 固定 Skill 快照与升级检查清单
2. **本文件** — 按场景 ID 路由到 MN / override / 预防性检查
3. `migration-scenarios.md` — 场景背景、旧用法、新用法、降级路径
4. `migration-notes/` — 已填写的 MN-01～03 演练记录
5. `api-override-recipes.md` / `scenario-override-recipes.md` — 组件或场景级 override
6. `merge-options-guide.md` — 嵌套 options 浅/深 merge 选型
7. `upgrade-troubleshooting.md` — 升级后症状排查、回滚与选型纠错

## 场景路由表

| MS ID | 场景 | 演练类型 | 目标路径 | 自动验证 |
|---|---|---|---|---|
| MS-01 | ThemeToggle 导出名 alias | **MN 演练** | [MN-01](migration-notes/MN-01-theme-toggle-alias.md) · `templates/ui/deprecated/theme-toggle-alias.tsx` | `audit_migration_drills.py` |
| MS-02 | SearchCommand 无 react-router | **MN 演练** | [MN-02](migration-notes/MN-02-search-command-no-router.md) · `templates/ui/deprecated/search-command-static.tsx` | 同上 |
| MS-03 | Kanban 自建板 → KanbanBoard | **MN 演练** | [MN-03](migration-notes/MN-03-kanban-legacy-board.md) · `templates/ui/deprecated/kanban-legacy-shell.tsx` | 同上 |
| MS-04 | Chart palette 硬编码 | 预防性 override | `api-override-recipes.md#chart-apexcharts` · `templates/lib/chart-theme.ts` | `audit_override_recipes.py` |
| MS-05 | FullCalendar 无 overrides | 预防性 override | `api-override-recipes.md#fullcalendar` · `getDefaultFullCalendarOptions(overrides?)` | 同上 |
| MS-06 | FileUpload → FileDropzone | additive 升级 | `api-override-recipes.md#fileupload--filedropzone` · `templates/ui/file-dropzone.tsx` | `audit_compat_contracts.py` |
| MS-07 | CodeBlock → CodeEditor | additive 升级 | `templates/ui/code-editor.tsx` · `references/layout-patterns/code-editor-editable.md` | `verify_design_system.py` |
| MS-08 | 无路由 Command 搜索 | 降级路径 | `api-override-recipes.md#command-palette--combobox` · `ComboboxPanel` | 同上 |
| MS-09 | Gateway ControlPlaneHub 子面板 | 场景组合 | `scenario-override-recipes.md` SOR-05 · `templates/gateway/control-plane-hub.tsx` | `audit_override_recipes.py` |
| MS-10 | DevOps CicdRunDetail | 场景组合 | `scenario-override-recipes.md` SOR-02 · `templates/devops/cicd-run-detail.tsx` | 同上 |
| MS-11 | BI 联动仪表盘 cross-filter | 场景组合 | `scenario-override-recipes.md` SOR-01 · `templates/bi/cross-filter-dashboard.tsx` | `audit_override_recipes.py` |
| MS-12 | PaaS 资源监控地图热力 | 场景组合 | `scenario-override-recipes.md` SOR-03 · `templates/paas/resource-table.tsx` | 同上 |
| MS-13 | 治理安全 RBAC + 审计 + 认证向导 | 场景组合 | `scenario-override-recipes.md` SOR-04 · `templates/governance/` | 同上 |

### 演练类型说明

| 类型 | 何时用 | 产出要求 |
|---|---|---|
| **MN 演练** | 已有真实 migration note + deprecated wrapper | 按 MN 验证清单勾选；业务侧 `tsc` + 截图 |
| **预防性 override** | 尚未 breaking，但业务硬编码 theme helper | 改用 `getBase*` / `merge*` + overrides；见 `merge-options-guide.md` |
| **additive 升级** | 新能力为可选模板，不替换旧 API | 保留旧组件调用；新页面接入新模板 |
| **场景组合** | 页面级多组件 props 对齐 | 查 SOR 场景食谱；子面板 props 均为 optional |

## 升级检查清单

业务项目升级 Skill 快照前，按序执行：

- [ ] 对比 `api-contracts.md` 风险总表，标记本仓库使用的复杂组件
- [ ] 在本表找到对应 MS ID，打开目标路径阅读旧/新用法
- [ ] MN 场景：运行 `audit_migration_drills.py`；按 MN 验证清单在业务仓库演练
- [ ] MS-04～08：确认无硬编码 palette key、无手动 spread 默认 theme 对象
- [ ] MS-09～13：确认页面组合使用受控 props，非依赖 Skill 内部 mock
- [ ] MS-09～13：按 `business-validation-checklist.md` 执行业务冒烟并归档截图
- [ ] UI 漂移：按 `ui-drift-review-checklist.md` REV-01～05 完成 golden 对照抽检；按 `scene-ui-drift-review-checklist.md` REV-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景 UI 漂移抽检
- [ ] 首次接入：按 `adoption-onboarding-checklist.md` ADOPT-01～05 完成 pin 与首页 smoke
- [ ] SSR/微前端：按 `ssr-microfrontend-adoption-checklist.md` SSR-01～05 / MFE-01～05 完成 client 边界与壳层选型
- [ ] 可访问性：按 `accessibility-review-checklist.md` A11Y-01～05 完成键盘/标签/浮层抽检；按 `scene-accessibility-review-checklist.md` A11Y-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景可访问性抽检
- [ ] 响应式：按 `responsive-review-checklist.md` RESP-01～05 完成 desktop/tablet/mobile 抽检；按 `scene-responsive-review-checklist.md` RESP-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景响应式抽检
- [ ] 异步状态：按 `async-state-review-checklist.md` ASYNC-01～05 完成 loading/empty/error/retry 抽检；按 `scene-async-state-review-checklist.md` ASYNC-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景异步抽检
- [ ] 交互与动效：按 `interaction-motion-review-checklist.md` INTER-01～05 完成 hover/focus/浮层/loading 抽检；按 `scene-interaction-review-checklist.md` INTER-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景交互抽检
- [ ] 中文示例文案：按 `chinese-copy-review-checklist.md` COPY-01～05 完成表单/状态/壳层/领域 mock 抽检；按 `scene-chinese-copy-review-checklist.md` COPY-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景中文文案抽检
- [ ] 视觉 Token 与密度：按 `visual-token-review-checklist.md` VIS-01～05 完成语义色/dark/密度/层级抽检；按 `scene-visual-token-review-checklist.md` VIS-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景视觉抽检
- [ ] 表单校验与逻辑完备：按 `form-validation-logic-review-checklist.md` LOGIC-01～05 完成校验/危险操作/权限/向导/CRUD 抽检
- [ ] 类型完整与 API 契约：按 `type-api-contract-review-checklist.md` TYPE-01～05 完成 props/theme/受控/升级/MS 类型抽检；按 `scene-type-api-contract-review-checklist.md` TYPE-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景类型契约抽检
- [ ] 生成一致性：按 `generation-consistency-review-checklist.md` GEN-01～05 完成选型/Token/状态/检索/MS 组合抽检；按 `scene-generation-consistency-review-checklist.md` GEN-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景生成一致性抽检
- [ ] 组件覆盖率：按 `component-coverage-review-checklist.md` COV-01～05 完成主路径模板/extension-audit/preview/变体/MS 模板抽检；按 `scene-component-coverage-review-checklist.md` COV-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景组件覆盖率抽检
- [ ] 模式覆盖：按 `pattern-coverage-review-checklist.md` PAT-01～05 完成 output modes/页面布局/状态模式/MS 场景页面组合抽检；按 `scene-pattern-coverage-review-checklist.md` PAT-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景页面模式抽检
- [ ] 约束遵守：按 `constraint-compliance-review-checklist.md` CON-01～05 完成语义 Token/框架 API/导入规则/Skill 红线/MS 工程边界抽检；按 `scene-constraint-compliance-review-checklist.md` CON-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景约束抽检
- [ ] 产品逻辑完备：按 `logic-completeness-review-checklist.md` LOGIC-06～10 完成用户流程/筛选因果/主从上下文/审批配额/MS 业务逻辑束抽检；按 `scene-logic-completeness-review-checklist.md` LOGIC-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景逻辑完备抽检
- [ ] Agent 失败模式：按 `agent-failure-patterns-review-checklist.md` FAIL-01～05 完成主内容宽度/卡片嵌套/mobile 表格/dark 边界/手写浮层抽检；按 `scene-agent-failure-review-checklist.md` FAIL-06～10 完成 BI/DevOps/Gateway/PaaS/MS 场景 Agent 失败抽检
- [ ] UiElements 键盘/hover/focus：按 `ui-elements-keyboard-hover-focus-review-checklist.md` KBF-01～05 与 `scene-ui-elements-keyboard-hover-focus-review-checklist.md` KBF-06～10 完成 Specimen Lab 键盘、hover、focus 与失败态抽检；对照 `ui-elements-keyboard-hover-focus-gates.png`
- [ ] UiElements empty/error/loading：按 `ui-elements-empty-error-loading-review-checklist.md` EEL-01～05 与 `scene-ui-elements-empty-error-loading-review-checklist.md` EEL-06～10 完成 Specimen Lab 失败态抽检；对照 `ui-elements-empty-error-loading-gates.png`
- [ ] UiElements 变体/交互态：按 `ui-elements-variant-interaction-review-checklist.md` VAR-01～05 与 `scene-ui-elements-variant-interaction-review-checklist.md` VAR-06～10 完成 Specimen Lab 变体抽检；对照 `ui-elements-variant-interaction-gates.png`
- [ ] 运行 `audit_compat_contracts.py` + `verify_design_system.py`
- [ ] 业务侧 `tsc --noEmit` + 关键页面 light/dark 截图对比

## 与 migration-scenarios 的双向索引

| 文档 | 职责 |
|---|---|
| `migration-scenarios.md` | 每个 MS 的背景、代码片段、降级路径 |
| `migration-notes/README.md` | MN-01～03 注册表与 wrapper 路径 |
| 本文件 | MS → MN / override / SOR 的一站式路由 |
| `backward-compatibility.md` | 兼容原则、deprecated 模式、评分门控 |

MS-01～03 在 `migration-scenarios.md` 场景索引中已链接对应 MN。MS-04～13 无独立 MN（尚未发生 breaking），通过本表路由到 override 或 SOR 食谱。

## 检索入口

| 意图 | 读 |
|---|---|
| 固定快照再升级 | `version-pinning-guide.md` |
| 查场景 ID 路由 | 本文件场景路由表 |
| 场景详情与代码 | `migration-scenarios.md` |
| 已填写 migration note | `migration-notes/` |
| 单项组件 override | `api-override-recipes.md` |
| 跨组件场景 override | `scenario-override-recipes.md` |
| 嵌套 merge 选型 | `merge-options-guide.md` |
| 升级后故障排查 | `upgrade-troubleshooting.md` |
| 业务部署冒烟（MS-09～13） | `business-validation-checklist.md` |
| UI 漂移评审（REV-01～10） | `ui-drift-review-checklist.md` + `scene-ui-drift-review-checklist.md` |
| 首次接入 / vendoring（ADOPT-01～05） | `adoption-onboarding-checklist.md` |
| SSR / 微前端接入（SSR/MFE） | `ssr-microfrontend-adoption-checklist.md` |
| 可访问性评审（A11Y-01～10） | `accessibility-review-checklist.md` + `scene-accessibility-review-checklist.md` |
| 响应式评审（RESP-01～10） | `responsive-review-checklist.md` + `scene-responsive-review-checklist.md` |
| 异步状态评审（ASYNC-01～05） | `async-state-review-checklist.md` |
| 场景异步状态评审（ASYNC-06～10） | `scene-async-state-review-checklist.md` |
| 交互与动效评审（INTER-01～05） | `interaction-motion-review-checklist.md` |
| 场景交互与动效评审（INTER-06～10） | `scene-interaction-review-checklist.md` |
| 中文示例文案评审（COPY-01～10） | `chinese-copy-review-checklist.md` + `scene-chinese-copy-review-checklist.md` |
| 视觉 Token 与密度评审（VIS-01～05） | `visual-token-review-checklist.md` |
| 场景视觉 Token 评审（VIS-06～10） | `scene-visual-token-review-checklist.md` |
| 表单校验与逻辑完备评审（LOGIC-01～05） | `form-validation-logic-review-checklist.md` |
| 类型完整与 API 契约评审（TYPE-01～10） | `type-api-contract-review-checklist.md` + `scene-type-api-contract-review-checklist.md` |
| 生成一致性评审（GEN-01～10） | `generation-consistency-review-checklist.md` + `scene-generation-consistency-review-checklist.md` |
| 组件覆盖率评审（COV-01～10） | `component-coverage-review-checklist.md` + `scene-component-coverage-review-checklist.md` |
| 模式覆盖评审（PAT-01～10） | `pattern-coverage-review-checklist.md` + `scene-pattern-coverage-review-checklist.md` |
| 约束遵守评审（CON-01～10） | `constraint-compliance-review-checklist.md` + `scene-constraint-compliance-review-checklist.md` |
| 产品逻辑完备评审（LOGIC-06～10） | `logic-completeness-review-checklist.md` + `scene-logic-completeness-review-checklist.md` |
| Agent 失败模式评审（FAIL-01～10） | `agent-failure-patterns-review-checklist.md` + `scene-agent-failure-review-checklist.md` |
| UiElements 键盘/hover/focus 评审（KBF-01～10） | `ui-elements-keyboard-hover-focus-review-checklist.md` + `scene-ui-elements-keyboard-hover-focus-review-checklist.md` |
| UiElements empty/error/loading 评审（EEL-01～10） | `ui-elements-empty-error-loading-review-checklist.md` + `scene-ui-elements-empty-error-loading-review-checklist.md` |
| UiElements 变体/交互态评审（VAR-01～10） | `ui-elements-variant-interaction-review-checklist.md` + `scene-ui-elements-variant-interaction-review-checklist.md` |
| 契约与风险 | `api-contracts.md` |
