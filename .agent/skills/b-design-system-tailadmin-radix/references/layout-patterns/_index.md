# 布局模式索引

| 模式 | 文件 | 场景 |
|---|---|---|
| App Shell | `navigation-template.md` + `templates/layout/*` | 侧栏 + 顶栏 + 内容区壳层 |
| Dashboard | `dashboard.md` | KPI + 图表 + 近期数据 |
| Table List | `table-list.md` | CRUD 列表、工单、发票 |
| List Search Filter Toolbar | `list-search-filter-toolbar.md` | 列表搜索 + 筛选 Popover/Drawer |
| CRUD Flow | `crud-flow.md` | 列表→创建→编辑→删除→批量完整业务流 |
| Form Flow | `form-flow.md` | 创建/编辑、设置 |
| Form Composition | `form-composition.md` | 简单/复杂表单、弹窗/抽屉表单、查看态描述列表 |
| Detail Page | `detail-page.md` | 详情、账单、会话 |
| Ops Monitoring | `ops-monitoring.md` | 运维监控、告警、事件响应 |
| CI/CD Release | `cicd-release.md` | 流水线、发布、回滚 |
| Code Repository | `code-repository.md` | 仓库、分支、MR/PR、代码浏览 |
| PaaS Resource | `paas-resource.md` | K8s、ES、MySQL、Redis 等资源管理 |
| Hub Tabs | `hub-tabs.md` | 设置/配额/用量 `?tab=` Hub 页 |
| Master-Detail Ops | `master-detail-ops.md` | 列表 + 右侧多 Tab 运维详情 |
| Dual Portal Shell | `dual-portal-shell.md` | User/Admin/Developer 多壳并存 |
| Three-Column Workspace | `three-column-workspace.md` | 项目轨 + 资源树 + 主工作区 |
| Activation Wizard | `activation-wizard.md` | 部署激活、连通性测试向导 |
| Auth Provider Wizard | `auth-provider-wizard.md` | LDAP/OAuth/OIDC/SAML 认证源配置 |
| BI Dataset Management | `bi-dataset-management.md` | 数据源、数据集、字段浏览 |
| BI Chart Builder | `bi-chart-builder.md` | 图表构建器三栏 |
| BI Dashboard Builder | `bi-dashboard-builder.md` | 仪表盘编辑/查看 |
| BI Data Screen | `bi-data-screen.md` | 16:9 数据大屏 |
| BI Filter Linkage | `bi-filter-linkage.md` | 全局/局部筛选、cross-filter、chips 清除 |

## BI 模板

| 组件 | 模板 | 说明 |
|---|---|---|
| ChartPanel | `templates/bi/chart-panel.tsx` | 图表卡片壳层 |
| MetricCard | `templates/bi/metric-card.tsx` | BI 指标卡 |
| FieldListPanel | `templates/bi/field-list-panel.tsx` | 字段列表面板 |
| ChartConfigPanel | `templates/bi/chart-config-panel.tsx` | 编码槽位 |
| ChartBuilderLayout | `templates/bi/chart-builder-layout.tsx` | 三栏构建器 |
| DashboardGrid | `templates/bi/dashboard-grid.tsx` | 仪表盘栅格 |
| DataScreenCanvas | `templates/bi/data-screen-canvas.tsx` | 大屏画布 |
| DatasetBrowser | `templates/bi/dataset-browser.tsx` | 数据集浏览 |
| FilterBar | `templates/bi/filter-bar.tsx` | 全局/局部筛选 chips |
| CrossFilterDashboard | `templates/bi/cross-filter-dashboard.tsx` | 筛选联动仪表盘组合 |
| MetricDefinitionPanel | `templates/bi/metric-definition-panel.tsx` | BI 语义层指标口径 |

## 壳层模板

| 组件 | 模板 | 说明 |
|---|---|---|
| SidebarProvider | `templates/context/sidebar-context.tsx` | 展开/折叠/移动端状态 |
| AppSidebar | `templates/layout/app-sidebar.tsx` | 290/90px 导航壳 |
| AppHeader | `templates/layout/app-header.tsx` | sticky 顶栏 + 搜索 |
| AppLayout | `templates/layout/app-layout.tsx` | 完整页面壳组合 |
| HubTabsLayout | `templates/layout/hub-tabs-layout.tsx` | URL 同步 Hub Tabs |
| FormPageShell | `templates/layout/form-page-shell.tsx` | 独立页面表单壳 + sticky actions |
| MasterDetailOps | `templates/layout/master-detail-ops.tsx` | 主从分栏 + 详情 Tabs |
| ThreeColumnWorkspace | `templates/layout/three-column-workspace.tsx` | 三栏研发工作台 |
| SearchCommand | `templates/ui/search-command.tsx` | ⌘K 命令面板 |
| FormSection | `templates/ui/form-section.tsx` | 表单分组卡片 |
| DescriptionList | `templates/ui/description-list.tsx` | 查看态描述列表 |
| DescriptionDiff | `templates/ui/description-diff.tsx` | 变更前后对比 |
| FormDrawer | `templates/ui/form-drawer.tsx` | Drawer 内详情/编辑切换 |

## 业务意图反向检索

不确定该用哪种布局或表单容器时，先查 `references/decision-matrix.md`，再按意图打开：

| 业务意图 | 首选模式 | 模板 |
|---|---|---|
| 创建/编辑资源（独立页） | Form Composition 简单表单 | `form-page-shell.tsx` + `form-section.tsx` |
| 多 Tab 复杂配置 | Form Composition + Hub Tabs | `hub-tabs-layout.tsx` + `form-section.tsx` |
| 表格行查看/编辑 | Form Composition Drawer | `form-drawer.tsx` + `description-list.tsx` |
| 只读详情/配置摘要 | DescriptionList | `description-list.tsx` |
| 审批/变更对比 | DescriptionDiff | `description-diff.tsx` |

先读 `pattern-index.md` 决策树，再打开具体文件。
