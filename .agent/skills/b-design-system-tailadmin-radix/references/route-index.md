# 路由索引

来源：TailAdmin React Pro v2.3.1 路由表（冻结于 `examples/b-design-system-tailadmin-radix/src/data/tailadminPageCatalog.ts` + `pattern-index.md`）。实现新页面时选择最接近的模式文件。

## 布局壳

| 壳 | 路由范围 | 模式文件 |
|---|---|---|
| `AppLayout` | 主后台（侧栏+顶栏） | `layout-patterns/dashboard.md` |
| `AlternativeLayout` | AI 生成器页 | `layout-patterns/detail-page.md` |
| 无壳 | Auth、Error、Layout 示例 | 见下表 |

## Dashboard（`/` 起）

| 路径 | 页面 | 模式 |
|---|---|---|
| `/` | Ecommerce | dashboard |
| `/analytics` | Analytics | dashboard |
| `/marketing` | Marketing | dashboard |
| `/crm` | CRM | dashboard |
| `/stocks` | Stocks | dashboard |
| `/saas` | SaaS | dashboard |
| `/logistics` | Logistics | dashboard |
| `/sales` | Sales | dashboard |
| `/ai` | AI Dashboard | dashboard |
| `/finance` | Finance | dashboard |

## Apps

| 路径 | 页面 | 模式 |
|---|---|---|
| `/calendar` | Calendar | detail-page · `fullcalendar-theme.md` |
| `/invoice`, `/invoices` | Invoices | table-list |
| `/chat` | Chats | detail-page |
| `/file-manager` | File Manager | table-list |
| `/task-list` | Task List | table-list |
| `/task-kanban` | Kanban | dashboard |
| `/inbox` | Email Inbox | table-list |
| `/inbox-details` | Email Details | detail-page |

## E-commerce

| 路径 | 页面 | 模式 |
|---|---|---|
| `/products-list` | Product List | table-list |
| `/add-product` | Add Product | form-flow |
| `/billing` | Billing | detail-page |
| `/single-invoice` | Single Invoice | detail-page |
| `/create-invoice` | Create Invoice | form-flow |
| `/transactions` | Transactions | table-list |
| `/single-transaction` | Single Transaction | detail-page |

## Support & Utility

| 路径 | 页面 | 模式 |
|---|---|---|
| `/support-tickets` | Ticket List | table-list |
| `/support-ticket-reply` | Ticket Reply | detail-page |
| `/profile` | User Profiles | form-flow |
| `/faq` | FAQs | detail-page |
| `/pricing-tables` | Pricing | detail-page |
| `/integrations` | Integrations | table-list |
| `/api-keys` | API Keys | table-list |
| `/blank` | Blank | dashboard（空模板） |

## Forms & Tables（组件展示）

| 路径 | 用途 |
|---|---|
| `/form-elements` | 表单控件全集参考 |
| `/form-layout` | 多列表单布局 |
| `/basic-tables` | 静态表格样式 |
| `/data-tables` | 分页数据表 |

## UI Elements（`/alerts` … `/tooltips`）

组件画廊路由 — 实现单个 shadcn 组件时对照源项目同名页。

| 路径 | 组件 | 参考 |
|---|---|---|
| `/carousel` | Swiper 轮播四 variant | `carousel-theme.md` |

## Charts & Maps

`/line-chart` … `/radial-chart` · `/maps` · `/vector-map` — 业务图表，非核心 DS。

## AI（AlternativeLayout）

| 路径 | 页面 |
|---|---|
| `/text-generator` | Text Generator |
| `/image-generator` | Image Generator |
| `/code-generator` | Code Generator | `editor-theme.md` |
| `/video-generator` | Video Generator |
| `/ai-settings` | AI Settings |

## Auth

| 路径 | 页面 |
|---|---|
| `/signin` | Sign In |
| `/signup` | Sign Up |
| `/reset-password` | Reset Password |
| `/two-step-verification` | 2FA |

## Status

`/maintenance` · `/success` · `/five-zero-zero` · `/five-zero-three` · `/coming-soon` · `*` NotFound

## SaaS / 企业 / 政府 / PaaS 扩展场景

这些不是 TailAdmin 源项目固定路由，而是本 Skill 面向真实后台系统的推荐落地页面。

| 路径建议 | 页面 | 模式 |
|---|---|---|
| `/ops/overview` | 运维总览 | `ops-monitoring.md` |
| `/ops/alerts` | 告警中心 | `ops-monitoring.md` + `table-list.md` |
| `/ops/incidents/:id` | 事件响应详情 | `detail-page.md` |
| `/delivery/pipelines` | 流水线列表 | `cicd-release.md` |
| `/delivery/pipelines/:id` | 流水线详情 | `cicd-release.md` |
| `/delivery/releases/:id` | 发布单详情 | `cicd-release.md` |
| `/repos` | 代码仓库列表 | `code-repository.md` |
| `/repos/:repo` | 仓库概览 | `code-repository.md` |
| `/repos/:repo/merge-requests/:id` | MR/PR 详情 | `code-repository.md` |
| `/paas/clusters` | K8s 集群列表 | `paas-resource.md` |
| `/paas/namespaces/:ns/workloads` | 工作负载列表 | `paas-resource.md` |
| `/paas/mysql/:id` | MySQL 实例详情 | `paas-resource.md` |
| `/paas/elasticsearch/:id` | ES 集群详情 | `paas-resource.md` |
| `/governance/audit-logs` | 审计日志 | `table-list.md` |
| `/governance/approvals/:id` | 审批详情 | `detail-page.md` |

## 检索提示

- **高密度列表** → `table-list.md`
- **多字段录入** → `form-flow.md`
- **指标+图表** → `dashboard.md`
- **主从详情** → `detail-page.md`
- **SaaS/企业/政府/PaaS 场景** → `domain-scenarios.md`
