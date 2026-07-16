# 模式索引

| 模式 | 文件 | 典型路由 |
|---|---|---|
| 仪表盘 | `layout-patterns/dashboard.md` | `/`, `/analytics`, `/crm` |
| 表格列表 | `layout-patterns/table-list.md` | `/products-list`, `/invoices` |
| 数据状态契约 | `component-styles/content-state-contract.md` | QueryShell · DataTableCard · StatMetric |
| 表单流 | `layout-patterns/form-flow.md` | `/add-product`, `/profile` |
| 表单组合 / 描述列表 | `layout-patterns/form-composition.md` | 简单/复杂表单、Drawer 表单、查看态详情 |
| 详情页 | `layout-patterns/detail-page.md` | `/inbox-details`, `/billing` |
| 运维监控 | `layout-patterns/ops-monitoring.md` | 告警、事件、服务健康 |
| CI/CD 发布 | `layout-patterns/cicd-release.md` | 流水线、发布、回滚 |
| 代码仓库 | `layout-patterns/code-repository.md` | 仓库、分支、MR/PR、代码浏览 |
| PaaS 资源 | `layout-patterns/paas-resource.md` | K8s、ES、MySQL、Redis 管理 |
| Hub Tabs | `layout-patterns/hub-tabs.md` | 设置、配额、用量 Hub |
| Master-Detail Ops | `layout-patterns/master-detail-ops.md` | 告警/端点/流水线主从 |
| Dual Portal Shell | `layout-patterns/dual-portal-shell.md` | 用户/管理/开发者门户 |
| Three-Column Workspace | `layout-patterns/three-column-workspace.md` | 仓库/资源树工作区 |
| Activation Wizard | `layout-patterns/activation-wizard.md` | 部署激活向导 |
| BI Dataset | `layout-patterns/bi-dataset-management.md` | 数据源/数据集/字段 |
| BI Chart Builder | `layout-patterns/bi-chart-builder.md` | 图表构建器 |
| BI Dashboard | `layout-patterns/bi-dashboard-builder.md` | 仪表盘 Builder |
| BI Data Screen | `layout-patterns/bi-data-screen.md` | 数据大屏 |
| BI Filter Linkage | `layout-patterns/bi-filter-linkage.md` | 筛选联动 / cross-filter |
| BI Drill Down | `layout-patterns/bi-drill-down.md` | 下钻 / 明细查看 |
| BI Export Subscription | `layout-patterns/bi-export-subscription.md` | 报表 / 导出与订阅 |
| BI Share Embed | `layout-patterns/bi-share-embed.md` | 权限 / 分享与嵌入式 BI |

## 模式选择决策树

```
需要展示 KPI/图表？
  yes → BI 构建/大屏/仪表盘？
    yes → bi-chart-builder / bi-dashboard-builder / bi-data-screen
    no → 运维/资源健康？
      yes → ops-monitoring 或 paas-resource
      no → dashboard
  no → 以表格为主？
    yes → table-list
    no → 以表单提交为主？
      yes → 需要保留列表上下文？
        yes → form-composition Drawer 表单
        no → 字段 ≤6 且无需上下文？
          yes → form-flow 或 Dialog 短表单
          no → form-composition 独立页 / Hub Tabs 复杂表单
    no → 只读详情/配置摘要？
      yes → form-composition 描述列表（禁止 disabled 表单冒充）
      no → 需要 Hub Tab 切换（设置/配额）？
        yes → hub-tabs
        no → 列表 + 右侧详情？
          yes → master-detail-ops
          no → 三栏树 + 编辑器？
            yes → three-column-workspace
            no → 多门户壳层？
              yes → dual-portal-shell
              no → 激活/接入向导？
                yes → activation-wizard
                no → 代码/发布/资源详情？
                  yes → code-repository / cicd-release / paas-resource
                  no → detail-page
```

## 通用页面结构（AppLayout 内）

```tsx
// 1. 可选 PageHeader（标题 + 面包屑 + actions）
// 2. 主内容区（grid 或 stack）
// 3. 可选侧栏 panel（详情页）
```

## 与路由索引联动

先读 `route-index.md` 找相似路径，再打开对应 `layout-patterns/` 文件。

## 业务域入口

SaaS、企业、政府、PaaS、研发平台页面先读 `domain-scenarios.md`，再选具体模式文件。

## 业务意图反向检索

从业务任务反查组件/模式时，按以下顺序：

1. `references/decision-matrix.md` — 组件与页面选型矩阵
2. 本文件决策树 — 页面级模式
3. `references/component-index.md` — 组件组合
4. `references/icon-system.md` + `templates/icons/icon-registry.tsx` — 图标语义

| 用户说的任务 | 推荐模式 | 反例 |
|---|---|---|
| 「编辑表格里这一行」 | FormDrawer + DescriptionList | 不要用全屏跳转或居中 Dialog 承载长表单 |
| 「查看资源详情」 | DescriptionList / DescriptionSection | 不要用 disabled Input 冒充详情 |
| 「创建新租户」 | FormPageShell + FormSection | 不要堆在一个无分组的巨大卡片里 |
| 「对比变更前后」 | DescriptionDiff | 不要并排两个只读表单 |
| 「BI 仪表盘加筛选」 | CrossFilterDashboard + FilterBar | 不要每个 ChartPanel 重复全局日期 |
| 「图表点击下钻看明细」 | DrillDownDashboard + DrillDetailTable | 不要直接跳 Table 丢筛选上下文 |
| 「点击图表筛选其他图」 | cross-filter chips + 清除联动 | 不要无状态手写 onClick |
