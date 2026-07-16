# 组件丰富度

本文件用于记录目标项目的组件资产厚度。组件多不是天然高分，只有被分类、索引、封装并配套示例后，才能转化为设计系统能力。

## 总览

| 指标 | 数量 | 说明 |
|---|---:|---|
| 组件总量 | 370 | TailAdmin React Pro v2.3.1 历史审计采样；当前以 `templates/` + example runtime 为准 |
| 基础组件 | 27+ | `components/form/*`、按钮/输入/选择器等表单基础件 |
| 复合组件 | 20+ | common/header/chats/file-manager 等组合组件 |
| 数据展示 | 80+ | dashboard metrics、tables、cards、charts、lists |
| 反馈组件 | 10+ | alerts、badges、notifications、spinners、progressbar |
| 浮层组件 | 10+ | modal、dropdown、popover、tooltip、integration settings modal |
| 导航组件 | 10+ | layout/sidebar/header/breadcrumb/menu 类组件 |
| 第三方/复杂组件 | 14+ | apexcharts、FullCalendar、maps、dropzone、flatpickr、swiper、kanban、prism |
| 业务组件 | 200+ | analytics/ecommerce/ai/finance/invoice/task/support 等领域组件 |

## 第三方/复杂组件

| 组件/插件 | 来源 | 封装策略 | 状态覆盖 | 替代/降级 |
|---|---|---|---|---|
| Chart | `apexcharts` / `react-apexcharts` | 统一为 chart wrapper + theme token | loading/empty/error | 静态 stat/card |
| Calendar | `@fullcalendar/*` | `fullcalendar-theme.md` | empty/selected/event | table/list fallback |
| DatePicker | `flatpickr` | 映射到 shadcn/Radix date picker 或受控封装 | focus/disabled/error | native date input |
| Upload | `react-dropzone` | dropzone + progress + error feedback | drag/loading/error | file input |
| Map | `leaflet` / `maplibre-gl` / jvectormap | map panel + loading/empty fallback | loading/error | static image/card |
| Carousel | `swiper` | `carousel-theme.md` | active/disabled/loading | horizontal list |
| Editor | `prismjs` | `editor-theme.md` | copy/loading/empty | plain pre |

## SaaS / 企业 / 政府 / PaaS 场景组件

| 组件/组合 | 主要页面 | 能力边界 |
|---|---|---|
| ResourceTable | K8s/ES/MySQL/Redis/主机列表 | 状态列、用量列、批量操作、行内危险动作 |
| HealthBadge / StatusBadge | 运维、PaaS、CI/CD | healthy/degraded/down/running/failed/unknown |
| LogStreamPanel | 运维日志、构建日志、Pod/DB 日志 | 固定高度、等宽字体、auto-scroll、暂停、搜索 |
| PipelineStageBar | CI/CD 流水线 | queued/running/success/failed/skipped |
| ArtifactTable | CI/CD 制品 | 下载、过期、报告链接、镜像 digest |
| FileTree + CodeViewer | 代码仓库 | 树形导航、长路径截断、大文件/二进制降级 |
| DiffViewer | MR/PR、配置变更 | added/removed/changed/commented |
| ApprovalTimeline | 发布审批、政府审批、变更单 | actor、decision、time、comment、audit |
| ConfigDiff | K8s YAML、DB 参数、策略变更 | before/after、风险提示、重启提示 |
| BackupTable | MySQL/ES/Redis 备份 | available/expired/restoring、恢复确认 |
| PermissionMatrix | RBAC、租户权限 | inherited/custom/disabled、批量勾选 |
| Secret/API Key Panel | API 网关、集成、SaaS 设置 | mask/copy/rotate/revoke、审计提示 |

## 高级表单控件能力目标

TailAdmin-Radix 面向多项目复用时，表单组件不能只提供单一 `Input` 外观；新增或演化输入控件时，必须举一反三沉淀为能力矩阵。

| 能力族 | 必备变体 | 状态要求 |
|---|---|---|
| Text Input | text、search、password、url、email、textarea-like compact | required、optional、helper、counter、prefix/suffix、clearable |
| Numeric Input | number、integer、decimal、currency、percent、unit、stepper | min/max、precision、thousand separator、invalid value、readonly |
| Masked Input | phone、id、license、ip/cidr、custom mask | mask hint、paste normalize、validation error、mobile keyboard |
| OTP / Code Input | 4/6/8 位、分组、paste、auto-focus | error、expired、resend pending、disabled |
| Secret Input | API Key、token、password reveal、copyable one-time secret | masked/revealed、copy feedback、rotate/revoke danger action |
| Async Field | remote unique check、connectivity probe、schema validate | validating、success、warning、retry、server error |

验收：新增表单控件必须在模板或文档中同时说明 props、状态、可访问性、移动端宽度、暗色模式和表单错误呈现方式；只补一个静态截图不算完成。

## 变体深度

| 组件 | size | intent | status | density | dark | loading | 示例数 |
|---|---|---|---|---|---|---|---:|
| Button | sm/md/lg | primary/outline/ghost/danger | disabled/focus | normal | yes | yes | 4+ |
| Form controls | md | default/error/success/warning | disabled/readonly/validating/async | normal | yes | partial → **advanced** | 12+ |
| Table | compact/normal | data/admin | selected/empty/loading | high | yes | yes | 4+ |
| Chart card | normal | analytics/status | loading/empty/error | medium | yes | partial | 6+ |
| Modal/Dropdown | normal | action/context | open/close/focus | medium | yes | no | 6+ |

## 评分规则

- 90+：组件类别完整，复杂组件有封装策略，高频组件有多状态示例。
- 80-89：主类别完整，但复杂组件或业务组件示例不足。
- 70-79：组件多但索引粗，Agent 仍需源码猜测。
- 70 以下：组件丰富度没有转化为可用设计系统资产。
