# 通用后台能力路线图

本文件把项目需求输入抽象为 `b-design-system-tailadmin-radix` 的通用能力包。TailAdmin-Radix 的目标是多项目共用设计系统；来自 Gateway、Nex 等项目的需求只能沉淀为可复用后台模式，不能写成单项目默认实现。

## 抽象原则

- 先提炼业务形态，再命名能力包：例如 Gateway 的 connected/airgap 抽象为“部署模式矩阵”，Nex 的流水线页抽象为“CI/CD Run Detail”。
- 组件优先提供能力矩阵，不只提供单一外观：例如 Input 要覆盖 mask、OTP、number、currency、secret、async validation 等家族能力。
- 场景包必须包含页面组合、关键状态、危险操作、空/错/加载态、响应式和截图验收。
- 项目品牌、路由、专有文案进入 override 或需求说明；TailAdmin 默认只保留通用结构、密度、状态和 Token 接口。

## P0 能力包

| 能力包 | 范围 | 交付物 |
|---|---|---|
| Advanced Form Controls | Input/Textarea/Select/MultiSelect/FileUpload/DatePicker 的高级输入矩阵 | reference + templates + example runtime |
| Data State Contract | Query shell、DataTableCard、KPI、列表和详情页三态/四态 | reference + DataTableCard 模板 + example runtime |
| Admin Layout Pack | Hub Tabs、Master-Detail Ops、Dual Portal Shell、Three-column Workspace、Activation Wizard | layout-patterns + example frames |
| BI / Analytics / Data Screen | 数据源、图表构建器、仪表盘 Builder、数据大屏、筛选联动、Example Golden Screens | PRD 分片 + layout-patterns + example frames |

## P1 能力包

| 能力包 | 范围 | 交付物 |
|---|---|---|
| Gateway / Control Plane | 部署模式、License、同步健康、Endpoint 探测、API Key、余额/配额 | references + composite templates |
| DevOps / Code Platform | PipelineStageBar、LogStreamPanel、ArtifactTable、ApprovalTimeline、DangerZone、DiffViewer、FileTree+CodeViewer、MR/PR shell | layout-patterns + templates + preview |
| Governance / Security | PermissionMatrix、AuditLogTable、Secret/API Key Panel、认证配置向导、合规提示 | references + templates |

## P2 能力包

| 能力包 | 范围 | 交付物 |
|---|---|---|
| PaaS Resource Management | K8s/ES/MySQL/Redis 资源列表、健康/容量、ConfigDiff、备份恢复、伸缩/重启/故障转移动作 | layout-patterns + component templates |
| Brand Override Layer | 项目主色、导航比例、密度、图标入口、文案风格 | override guide |

## Example 验收

新增能力包必须提供 `examples/b-design-system-tailadmin-radix` 中可复现的真实运行 frame。截图出现大面积空白、内容列过窄、文本裁切、控件遮挡/重叠或 dark/light 对比度失效时，不能标记 pass；综合美学封顶 82，总分最高 89。

具体执行清单见 `docs/spec/b-design-system-tailadmin-radix/prd/` 分片；`docs/spec/b-design-system-tailadmin-radix/shards/g21-demand-checklist.md` 仅保留为 G21 快照。

需求开发全部完成后，流水线再回到系统自我演进和维持轮 polish。
