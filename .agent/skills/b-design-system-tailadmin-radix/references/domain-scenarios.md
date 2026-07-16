# 业务场景索引 — SaaS / 企业 / 政府 / PaaS 后台

本文件把 TailAdmin 视觉系统映射到常见 B 端落地页面。实现页面时先选业务场景，再读对应 layout pattern 和组件 detail。

## 适用产品域

| 产品域 | 典型用户 | 设计目标 |
|---|---|---|
| SaaS 管理后台 | 租户管理员、运营、客服、财务 | 高密度数据、权限清晰、低学习成本 |
| 企业内部系统 | IT、研发、运维、安全、审计 | 可追踪、可批量操作、风险动作有摩擦 |
| 政府/政企后台 | 经办人、审批人、监管人员 | 稳定、克制、可审计、状态解释清楚 |
| PaaS/IaaS 管理台 | SRE、DevOps、平台工程师 | 资源拓扑、指标、日志、发布与回滚可控 |
| 自研研发平台 | 开发者、Reviewer、Release Manager | 仓库、分支、流水线、制品、权限一体化 |

## 场景到模式

| 场景 | 页面模式 | 推荐文件 |
|---|---|---|
| 运维总览 / NOC 大盘 | Dashboard + Monitoring | `layout-patterns/ops-monitoring.md` |
| 服务实例 / 主机 / Pod 列表 | Table List + Detail | `layout-patterns/table-list.md`、`layout-patterns/paas-resource.md` |
| 告警中心 / 事件响应 | Table List + Detail Page | `layout-patterns/ops-monitoring.md` |
| CI/CD 流水线与发布 | Pipeline Detail + Release Flow | `layout-patterns/cicd-release.md` |
| 企业网关 / 控制平面 | Control Plane Hub + Sync/Probe | `layout-patterns/control-plane.md` |
| 代码仓库 / 分支 / MR/PR | Repo Workspace | `layout-patterns/code-repository.md` |
| K8s / ES / MySQL / Redis 管理 | PaaS Resource Console | `layout-patterns/paas-resource.md` |
| 租户 / 组织 / 用户 / 权限 | CRUD Flow + Form Composition | `crud-flow.md`、`form-composition.md` |
| 审批 / 工单 / 变更单 | Detail Page + Timeline + DescriptionDiff | `detail-page.md`、`form-composition.md` |
| 审计日志 / 操作日志 | Table List + Filter Drawer | `table-list.md` |
| 计费 / 用量 / 配额 | Dashboard + Table List | `dashboard.md` |

## 场景组件清单

| 组件/组合 | 适用场景 | 组合方式 |
|---|---|---|
| MetricCard + Sparkline | 监控、SaaS 用量、成本 | `ComponentCard` + Chart wrapper |
| StatusBadge / HealthBadge | 服务、Pod、Job、告警 | Badge light/solid + icon + tooltip |
| ResourceTable | K8s/ES/MySQL/主机列表 | Table + status column + row actions + pagination |
| FilterDrawer | 日志、告警、资源筛选 | Sheet + Select + DatePicker + MultiSelect |
| LogStreamPanel | 运维、CI/CD、任务执行 | mono text area + severity tag + auto-scroll toggle |
| PipelineStageBar | CI/CD、发布流程 | stage chips + progress + failure focus |
| DiffViewer / FileTree | 代码仓库、配置变更 | tree/detail split + code block |
| ApprovalTimeline | 工单、发布、政府审批 | timeline + actor + decision badge |
| DangerZone | 删除集群、回滚、重启实例 | destructive Button + confirm Dialog |
| QuotaUsageCard | 租户/PaaS 配额 | Progress + limits + request action |
| PermissionMatrix | RBAC、角色授权 | table grid + checkbox + inherited state |
| Secret/API Key Panel | SaaS/API 网关 | masked value + copy + rotate + revoke |
| DeploymentModeMatrix | 企业网关双部署 | connected/airgap chip + 分叉 banner |
| SyncHealthPanel | 网关同步健康 | quota/report/HMAC/heartbeat 四轨 |
| EndpointProbeTable | Endpoint 探测 | ready/failed/unknown + debounce probe |
| BalanceQuotaSummary | 网关余额/配额 | 元/分展示 + 低余额/冻结态 |
| LicenseIssuePanel | License 签发/续期 | one-time copy + expiry guard |

## 导航建议

- Overview：总览、仪表盘、告警
- Resources：集群、命名空间、服务、数据库、消息队列、存储
- Delivery：代码仓库、流水线、发布、制品、环境
- Operations：工单、事件、日志、审计、任务
- Governance：组织、用户、角色、策略、审批
- Billing：用量、账单、配额、成本中心
- Settings：集成、API Keys、通知、系统设置

## 业务意图反向检索

实现页面前先回答「用户在完成什么任务」，再查 `references/decision-matrix.md`：

| 业务域 + 任务 | 推荐模式 | 关键模板 |
|---|---|---|
| SaaS 租户创建 | Form Composition 简单表单 | `form-page-shell.tsx` |
| 企业网关配置 | Hub Tabs + FormSection | `hub-tabs-layout.tsx` |
| PaaS 资源行详情 | FormDrawer + DescriptionList | `form-drawer.tsx` |
| 政府审批变更对比 | DescriptionDiff + ApprovalTimeline | `description-diff.tsx` |
| 运维告警筛选 | Filter Drawer (Sheet bottom/right) | `sheet.tsx` |
| DevOps 发布审批 | Detail Page + DangerZone | `danger-zone.tsx` |
| BI 指标页图标 | icon-registry 语义检索 | `icon-registry.tsx` |

## 信息密度规则

- 首页优先展示异常、待处理、风险和趋势，不展示装饰性 hero。
- 监控/运维页面首屏必须同时看到核心指标、异常列表或最近事件。
- 发布、回滚、删除、扩缩容、重启等危险操作必须带对象名和二次确认。
- 政府/企业审批流必须显示状态、当前处理人、时间线和审计信息。
- PaaS 资源详情必须把 Metrics、Events、Logs、YAML/Config 分成 tabs，避免堆在一屏。

## 持续演化规则

- 每轮自动演化至少检查一个未充分覆盖的业务域或页面组合。
- 新增场景时必须同时记录：目标用户、主要任务、页面模式、场景组件、关键状态、危险操作、截图验收重点。
- 不要只补单个组件；优先沉淀“页面组合 + 组件组合 + 状态流”。
- 运维、CI/CD、代码仓库、PaaS 资源、权限审计、审批工单是当前高优先级扩展方向。

## 截图验收重点

- Dashboard 不得出现左侧窄列 + 右侧空白；KPI 数字不可裁切。
- 资源表格在 1440px desktop 下应充分利用内容宽度。
- 日志、代码、Diff、配置内容必须有稳定滚动容器，不能撑破布局。
- 详情页右侧元信息栏不得压缩主内容到不可读。
