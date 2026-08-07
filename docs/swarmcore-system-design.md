# SwarmCore 系统设计

| 属性 | 值 |
|---|---|
| 状态 | Baseline / 可实施 |
| 版本 | 2.1 |
| 日期 | 2026-08-06 |
| 目标版本 | SwarmCore v1 |

## 1. 定位与边界

SwarmCore 是协议无关的多 Agent 编排与耐久执行内核。调用方负责目标理解、能力选择和方案生成；SwarmCore 负责校验、编译、调度、状态、可靠性、安全、事件和结果交付。

固定边界：

1. REST、MCP 和控制台复用同一应用服务、权限、幂等、编译和结果契约；控制台不建立独立执行链路。
2. Agno 是 Agent Adapter，不是系统调度状态源；Temporal 是唯一耐久执行引擎。
3. PostgreSQL 是产品状态、权限、审计和查询事实源；Temporal History 只属于执行引擎。
4. NATS JetStream 只负责事件分发，不保存最终业务状态；S3 保存文件字节，数据库保存元数据。
5. Workflow 必须确定性；模型、网络、数据库、文件和当前时间访问只允许出现在 Activity、Tool 或 Adapter。
6. 用户策略使用 SwarmSpec、受限条件和模板，不执行 Python `eval` 或上传任意控制面代码。
7. Tool、模型、Secret、文件和外部 Provider 必须经过 Gateway、OPA、预算、审计和租户边界。
8. SwarmCore 提供 at-least-once 执行、幂等和补偿，不承诺外部副作用 exactly-once。

非目标：自研模型推理引擎、通用聊天产品、公开能力市场、第二套工作流引擎，以及让 Runtime 取代上游目标理解。

## 2. 技术基线与质量目标

| 领域 | 基线 |
|---|---|
| Python/API | Python 3.12、FastAPI、Pydantic v2、uv |
| Agent/模型 | Agno 2.7、LiteLLM Proxy、OpenAI 兼容 Provider、可选 vLLM |
| 执行 | Temporal Python SDK |
| 数据 | PostgreSQL 17、SQLAlchemy 2、Alembic、pgvector、S3 API |
| 事件/缓存 | NATS JetStream、可选 Valkey |
| 安全 | OIDC、OPA、Vault Provider、Kubernetes Job + gVisor |
| 可观测 | OpenTelemetry、Phoenix、Prometheus/Grafana、Loki |
| Web | React 19、TypeScript、Vite、React Router、TanStack Query、Zustand |
| 测试 | pytest、Vitest、Playwright |

核心 SLO：控制面月可用性 99.9%；`POST /runs` p95 小于 300 ms；durable event 到客户端 p95 小于 1 s；有空闲 Worker 时排队到开始 p95 小于 5 s；Worker 故障后 60 s 内恢复或进入重试；备份 RPO 不超过 5 min、RTO 不超过 30 min。Provider 延迟不计入控制面 SLO，但计入 Run 端到端耗时。

默认安全上限：单 Run 32 个 AgentInstance、并行度 8、子蜂群深度 4、Loop 20 次、Run 60 min、Task 15 min、模型调用 120 s、Tool 300 s、Token 1,000,000、成本 25 USD、单 Artifact 100 MiB、Run Artifact 合计 1 GiB。租户策略可以降低，只有平台管理员可以提高。

Model Gateway 必须在调用前同时预留 Token 与成本。Provider 未返回价格时按部署配置的保守输入/输出单价计费并标记 fallback price version，禁止把有 Token 消耗的调用记录为零成本而使 `maxCostUsd` 失效。

## 3. 总体架构

~~~mermaid
flowchart TB
    Caller[DeepTalk / 外部系统 / 控制台]
    Entry[REST / MCP Adapter]
    App[统一应用服务]
    Registry[Strategy / Capability Registry]
    Compiler[SwarmSpec Compiler]
    RunService[Run Command Service]
    Outbox[PostgreSQL Outbox]
    Temporal[Temporal]
    Control[Control Worker]
    Agent[Agent Worker]
    Tool[Tool Worker / Gateway]
    Sandbox[Sandbox Manager]
    Provider[Model / OCR / Document Parser]
    Artifact[Artifact Gateway / S3]
    PG[(PostgreSQL / pgvector)]
    NATS[NATS JetStream]
    Events[Event Gateway / Webhook]

    Caller --> Entry --> App
    App --> Registry --> Compiler
    App --> RunService --> PG
    PG --> Outbox --> Temporal --> Control
    Control --> Agent --> Provider
    Control --> Tool --> Provider
    Control --> Sandbox
    Agent --> Artifact
    Tool --> Artifact
    Control --> PG
    PG --> NATS --> Events --> Caller
~~~

### 3.1 五层三横切

业务能力按五层组织：

| 层次 | 职责 | 禁止事项 |
|---|---|---|
| Runtime 执行层 | 编译、耐久调度、状态机、重试、并发、幂等、补偿和人工等待 | 不包含合同、发票等业务语义，不用模型替代状态判断 |
| 模型与 Provider 层 | LLM、Embedding、Vision、OCR、文档解析和知识库 | 不直接写业务状态或持有 Run 生命周期；不承担外部业务数据连接 |
| 原子工具能力层 | 解析、切片、抽取、检索、规则、计算和渲染 | 硬规则不写进 Prompt；副作用不绕过 Tool Gateway |
| 领域智能体层 | 分类、语义抽取、归纳、根因解释、评审和报告叙述 | Agent 不等同微服务，不直连数据库、Secret 或外部 Endpoint |
| 业务应用层 | Business Work、Workbench、内部 Capability Pack 执行定义、RuleSet、领域状态、问题和报告 | 不复制 Runtime、权限、审计和事件体系；Capability Pack 不再作为用户可见业务入口 |

逻辑分层不是强制调用链：确定性规则或偏差计算可由 Runtime 直接调度 Tool，不必经过 Agent 或模型。

三个横切平面：

- 数据与证据：Blob、Artifact、页/块/表格、字段证据、知识、向量、哈希、版本和血缘。
- 质量评测与人工复核：Schema、样本集、指标、置信度校准、运行时质量门和改判反馈。
- 安全治理与可观测：tenant/project、OPA、Secret、预算、审计、Trace、日志、指标和保留策略。

调度校准拆为两部分：Runtime 对状态、重试、备用路由、预算和人工等待拥有最终决定权；质量监督 Agent 只能返回结构化建议，由 Runtime 按冻结策略执行。

## 4. 核心组件

| 组件 | 稳定职责 |
|---|---|
| 入站 Adapter | 协议映射、认证和 DTO 转换，不复制业务规则 |
| 统一应用服务 | tenant/project、Scope、幂等、命令、查询、审批、Workbench 和能力中心 |
| Registry | 保存不可变 Agent、Tool、Model、Strategy、Capability Pack 定义和版本引用 |
| Readiness Service | 按 tenant/project/environment 计算动态可用性；健康状态不写回 Registry |
| Spec Compiler | Parse、Schema 校验、规范化、引用解析、语义/策略校验、生成 ExecutionPlan 和哈希 |
| Run Command Service | 在同一事务创建 Run、RunCommand 和 Outbox，只返回“已耐久接受” |
| Command Dispatcher | 按 Run 的 `command_seq` 将 start/control 命令可靠投递 Temporal |
| Temporal Workflow | 解释不可变 ExecutionPlan，计算 ready nodes，管理并行、等待、预算和取消 |
| Agent Worker | 通过 Agno Adapter 调用模型，只注入受控 GatewayProxyTool |
| Tool Gateway/Worker | Schema、OPA、Secret、超时、风险、幂等、effect journal 和 Provider 调用 |
| Sandbox Manager | 在隔离 Job 中运行不可信代码，默认拒绝出网和宿主权限 |
| Projector/Ingestor | 幂等写入 Run/Task/Attempt/Event 投影，大输出转 Artifact |
| Event Publisher/Gateway | PostgreSQL Outbox 到 NATS，再提供 SSE、Webhook 和历史补读 |
| Artifact Gateway | Blob/Artifact 上传、哈希、扫描、授权、保留和短期下载能力 |

### 4.1 能力注册、就绪和运行

三者必须分离：

1. Registry 只证明不可变定义可解析。
2. Readiness Service 证明当前项目和环境可运行。
3. Capability Run Service 只把 Agent、Tool 等具备任务语义的能力直接运行转换成标准 SwarmSpec/ExecutionPlan，再调用 Run Service；Model 不能直接运行。

状态仅为 `READY` 或 `NOT_READY`，后者返回稳定原因码：`EXECUTOR_MISSING`、`ADAPTER_MISSING`、`MODEL_ROUTE_MISSING`、`SECRET_MISSING`、`DEPENDENCY_NOT_READY`、`DEPENDENCY_CYCLE`、`HEALTH_CHECK_FAILED`、`ENVIRONMENT_NOT_ALLOWED`、`CAPABILITY_PACK_DISABLED`、`SCHEMA_INVALID`、`POLICY_DENIED`。

就绪门槛：Tool 必须有合法 Schema、executor、风险/幂等/恢复策略和健康状态；Model 必须有 Route、可租用 Secret 和健康 Endpoint；Agent 的 Adapter、模型和 Tool 依赖必须全部就绪；Strategy 必须已发布并编译；Capability Pack 启用前全部必需依赖必须就绪。

能力中心目录对 Model 额外收窄：Registry 可声明系统内置逻辑模型，但只有当前部署在 `SWARMCORE_MODEL_ROUTES`（Model Gateway）中登记了路由的模型才会作为系统模型出现在能力中心列表。无路由的系统模型不作为“未就绪卡片”展示，仍参与 Agent 依赖就绪计算（`DEPENDENCY_NOT_READY`）。Gateway 不可达时不按“无路由”隐藏，而是保留条目并标记健康检查失败。

项目也可通过三要素（API URL、ModelName、API Key）直接创建项目级模型连接，引用形如 `model://project/{uuid}@{revision}`。这类模型不进入全局 Registry / `SWARMCORE_MODEL_ROUTES`，凭证仍写入 Vault；Model Gateway 在存在项目运行时 Provider 配置时允许 Agent 调用。目录与智能体/策略模型选择器会合并展示项目模型。Model 只定义 API 连接、调用与就绪状态，不承载角色、提示词、工具或任务能力；这些执行语义必须在 Agent 中定义。模型详情页只负责连通与保存配置，不提供运行输入、预设、加入画布或立即运行，Capability Run Service 也必须拒绝 Model 直接运行。保存模型配置后，Web 自动发起一次真实模型调用；检测成功且被检测的 URL、ModelName 和 API Key 与已保存配置一致时，记录项目级连接验证并立即标记可调用，据此覆盖不适用于该 Provider 的通用 `/health` / `/models` 探测结果；保存配置变更会清除旧验证。项目范围内的配置页可通过专用 `no-store` 接口按需读取已保存的 API Key，以支持再次打开后由用户主动显示；密钥不得进入普通配置 JSON、URL、日志或浏览器持久化存储。

`ProjectConfiguration` 继续使用 `project_configurations` 表和旧 API。Tool 的用户层配置称为 Capability Preset，只保存能力引用和可复用参数，不保存 Secret。Agent 配置则投影为项目级、版本化的 `agent://project/{configurationId}@{revision}` 能力，参与 Readiness、能力中心直接运行；策略画布中智能体节点可绑定已保存的项目 Agent 配置，绑定时把入口 Agent 声明复制进当前 SwarmSpec，并把 `configurationId/revision/name/sourceRef` 记入草稿 `editorState.agentBindings`（非执行元数据）。后续配置更新或删除不自动改写已保存草稿快照；用户需显式重新绑定。发布后的执行语义完全来自 StrategyVersion 冻结的 SwarmSpec / ExecutionPlan，运行时不得旁路读取可变 ProjectConfiguration。执行时仍由 Agent Worker 通过 Agno Adapter 按任务创建运行实例，不把 SDK 对象作为持久状态。能力中心的直接运行和 REST/MCP 均复用同一应用服务，不建立旁路。

## 5. 执行与一致性契约

### 5.1 SwarmSpec 与 ExecutionPlan

当前 Compiler/Runtime 支持 `agent`、`tool`、`router`、`loop`、`parallel`、`join`、`reducer`、`approval`、`input`。Schema 中的 `team`、`transform`、`subflow`、`emit` 在 v1 基线中不可执行，提交时返回 `UNSUPPORTED_NODE_TYPE`；是否实现由后续里程碑决定。

条件表达式使用受限语法/CEL，不使用 Python `eval`。Router 按声明顺序选择首个匹配分支；Loop 必须有 1..20 的确定上限。ExecutionPlan 至少冻结 Spec/Compiler/Runtime 版本、Registry Snapshot、Policy Revision、输入内容版本、重试/超时/预算和输入输出 Schema；Run 不读取可变 Draft。

### 5.2 命令与状态

~~~mermaid
stateDiagram-v2
    [*] --> ACCEPTED
    ACCEPTED --> VALIDATING
    VALIDATING --> REJECTED
    VALIDATING --> QUEUED
    QUEUED --> RUNNING
    RUNNING --> WAITING_INPUT
    RUNNING --> WAITING_APPROVAL
    RUNNING --> PAUSING
    WAITING_INPUT --> PAUSING
    WAITING_APPROVAL --> PAUSING
    PAUSING --> PAUSED
    PAUSED --> RUNNING
    WAITING_INPUT --> RUNNING
    WAITING_APPROVAL --> RUNNING
    RUNNING --> CANCELLING
    PAUSED --> CANCELLING
    CANCELLING --> COMPENSATING
    CANCELLING --> CANCELLED
    COMPENSATING --> CANCELLED
    COMPENSATING --> FAILED
    RUNNING --> SUCCEEDED
    RUNNING --> FAILED
    RUNNING --> TIMED_OUT
~~~

终态不可逆；Retry 创建新 Run 并记录父 Run。Workflow 对 start、pause、resume、cancel、approval 和 input 按严格递增 `command_seq` 仲裁；相同 `request_id` 返回原结果。API 的 202 只表示命令已耐久接受，不表示已经执行。

### 5.3 Outbox、事件和副作用

- Run/RunCommand 与 destination=temporal 的 Outbox 同事务写入；Dispatcher 按单 Run 顺序投递并无限重试暂时故障。
- 状态投影、RunEvent 与 destination=nats 的 Outbox 同事务写入；Publisher 取得 PubAck 后标记完成。
- PostgreSQL 对外部查询和审计权威，Temporal 对实时调度权威；Reconciler 修复停滞投影。
- 单 Run 的 `event_seq` 严格递增；`transition_id`、`event_id`、Attempt `producer_seq` 和 Tool `effect_id` 分别负责重放幂等。
- Outbox 与 ToolEffect 的可接管租约必须携带 owner 和单调递增 generation；续租、完成、失败和重试均校验 fencing identity，旧副本不得覆盖新持有者状态。
- 文档处理 start/cancel 与 RunCommand 一样按数据库 partition 顺序领取；进程内集合不承担跨副本互斥。
- 模型预算预约携带过期时间；Gateway 崩溃留下的预约在 TTL 后惰性回收，已提交的 ModelUsageRecord 仍是防重放事实。
- Agent 内只允许无副作用 Tool；有副作用 Tool 展开为显式节点，必须声明幂等、补偿或人工恢复策略。
- Workflow 关闭前必须等待终态投影成功；NATS、Trace 和 Cache 均不是最终事实源。

### 5.4 Artifact 与大型数据

运行前输入使用 BlobObject，Run 输出使用 Artifact，二者复用对象存储、扫描、OPA、Capability Token 和保留机制，但保持不同业务契约。文件上传先进入 staging，通过 SHA-256、大小、MIME 和恶意内容检查后提交；Workflow 只传稳定引用和小型结构化数据，不传文件字节或完整模型上下文。

大文件按页/块并行处理并允许分片重试；Activity 内联结果默认不超过 256 KiB，超限写 Artifact。向量行必须带 tenant_id、project_id、source_id、embedding_model 和 embedding_version；模型变化写新版本，不原地覆盖。

## 6. 业务能力扩展

### 6.1 通用模型

产品入口是 **Business Work（业务工作）**：用户按业务目标进入配置、准备资料、办理案件并发起 Assessment。Capability Pack 仍是不可变的内部执行定义，组合 WorkItem/Input/Output Schema、Strategy、Agent、Tool、Rule、Report、权限、事件和 View Definition；产品路由与文案不再把 Capability Pack 暴露为业务入口。`BusinessWorkService` 维护一对一的稳定 `workKey` 到内部 Pack 映射，并投影运行资格、生产准入资格、阻塞项、冻结模型依赖与配置摘要；REST/MCP 的 `/business-works` 与兼容 `/capability-packs` 复用同一套应用服务。10 个产品入口均有独立执行身份，不得以语义相近但目标不同的 Pack 作为别名。

| 业务工作 | 内部 Pack | 主要事实源 | 模型 / 智能体边界 | 确定性门禁与输出 |
|---|---|---|---|---|
| 基础 AI 能力集成与质量评测 | `ai-foundation-quality` | 冻结基准样本、期望值、实际值、权重 | v1 不调用模型；只评测调用方提交的冻结输出 | 样本哈希、加权通过率、关键样本失败、角色复核、JSON/PDF |
| 文件结构化 | `document-structuring` | 不可变文档版本、解析/OCR/表格/切片 | Agent 只做分类和字段候选，不能改原文与证据 | 格式质量、一致性、最多一次重处理、人工确认、结构化产物 |
| 文件完整性 | `contract-integrity` | 已冻结文档、规则集、附件清单 | 分类与抽取 Agent 提供候选 | 规则与跨文件一致性并行、例外审批、完整性报告 |
| 履约计划与执行采集 | `contract-performance` | 合同义务、计划、执行证据、已批准变更 | Agent 提取条款与证据候选 | 幂等增量采集、预算审批、状态/付款门禁、计划与报告 |
| 发票一致性校验 | `invoice-assurance` | 发票、合同/订单、验收、供应商、应付台账 | Agent 仅规范低置信字段和候选匹配 | 官方/人工查验、重复/算术/主体/付款硬门禁、JSON/PDF |
| 偏差分析 | `deviation-analysis` | 当前事实、同 Subject 上游履约评价、历史快照 | Agent 解释根因和提出待确认责任建议 | 时间/内容/成本计算、趋势、审批快照、偏差报告 |
| 报告生成 | `report-generation` | 已成功且无需复核的来源 Evaluation | v1 不重新调用模型或重算业务结论 | tenant/project 范围校验、按来源评价与格式幂等复用 JSON/PDF |
| 合同后评价 | `contract-post-evaluation` | 文件、履约、发票、偏差、供应商风险上游评价 | 领域 Agent 只补充有证据的结构化候选与叙述 | 七维评分、直接引用门禁、正式报告质量门、JSON/PDF |
| GitHub 工程问题调度校准 | `swarm-calibration` | 公开 GitHub Issue/讨论/PR/固定提交、沙箱结果 | 主备诊断与质量 Agent 只给建议 | Runtime 路由、一次修订、沙箱未验证不得通过、角色复核 |
| 招采与供应商风控 | `procurement-supplier-risk` | 招标/投标/中标/合同、公开或授权风险源、绩效 | Agent 只做条款和证据解释 | BLOCKER、禁入与严重行政/税务风险硬门禁、职责分离审批、JSON/PDF |

业务工作状态与资格证据分离：`runnable` 只表示当前配置可发起；`unverified`、`local_verified`、`production_verified` 表示逐级资格。至少要有已启用 Pack、无依赖阻塞以及冻结的 StrategyVersion/SpecHash/PlanHash 才能成为本地验证；生产验证还必须关联成功 Run，并且结果通过质量门且无需复核。

Capability Pack Manifest 不允许 `module`、`script`、`classPath`、`componentUrl` 等代码入口；项目显式绑定不可变版本。项目可编辑绑定级 `configuration`，更新配置只更新当前项目的绑定参数，不修改已发布 Manifest、内容哈希或历史评估快照。受信加载器只自动发布每个 Pack 的当前版本；历史版本继续按数据库快照读取，不重新对照当前源码发布。相同名称和版本的内容哈希发生变化时必须拒绝，调用方只能提升版本。未启用且无历史评估引用的版本可删除；已删除的可信清单版本不会被再次自动发布到该项目。仍启用或仍被评估引用的版本不可删除。

业务上下文遵循 `BusinessObject != Case != Assessment != Run`。BusinessObject 及其不可变 Version 保存长期业务事实；Case/CaseRevision 继续复用 WorkItem/WorkItemRevision 兼容存储，并通过 Subject 冻结一个或多个对象版本；WorkItem 另存稳定 `business_work_key`，不得从可碰撞的 Pack、Strategy 或 Case type 反推产品身份。Assessment 继续复用 Evaluation，Run 只表示一次技术执行。已有 `/work-items`、`/evaluations` 和事件契约保持可用，新增 `/cases`、`/assessments` 与 `/business-works` 是同一事实和应用服务上的产品语义投影。业务办理成功后优先进入 Assessment 结果页，Run 作为技术执行详情可下钻查看。

DecisionAsset/DecisionVersion 复用 RuleSet/RuleSetVersion 存储，支持 Checklist、Decision Table、Expression 和 Threshold。发布时必须通过确定性测试；项目绑定必须匹配 Capability Pack v2 的 Decision Slot 类型与输入/输出 Schema；每次调用追加 DecisionExecution，不覆盖原始结果。条件仍使用受限表达式解释器，禁止 `eval`。

SwarmCore 的业务资料库只管理用户文件及其业务绑定，不承担 ERP、数据库、外部 API 或其他业务系统的数据连接。对象存储、本地磁盘和 S3 只作为 Blob/Artifact 的部署级 Storage Adapter，不是用户需要创建的业务 Connection。

业务资料库以 BusinessDocument 表示可管理的文件记录，以 BusinessDocumentVersion 表示指向既有 BlobObject 的不可变文件版本，并保存版本号、SHA-256、大小、MIME 和上传时间。UploadBatch 表达一次多文件上传会话；DocumentProcessingRun 记录某个文件版本的一次处理执行（解析、OCR、分类、抽取、质量检查）；DocumentProcessingResult 以追加版本保存统一处理信封与人工确认，不得覆盖 machineValue。DocumentBusinessObjectLink 关联 BusinessObject，DocumentWorkBinding 关联一个或多个业务工作；创建 Case 时由用户显式选择本次资料，并在同一事务中把资料绑定到 Case Subject，Assessment/Run 只能在 tenant/project、业务工作和 Subject 三重范围内选择资料，禁止 Subject 无结果时回退到项目级工作绑定。DocumentUsageSnapshot 冻结 document version、Blob ID、SHA-256、大小、MIME、分类/处理/确认版本与 provenance。Parser、OCR、Classifier、Extractor 通过 Adapter 注册，按 MIME 与 Processing Profile 选择，不按业务工作名称分支；大解析结果写入 Blob/Artifact 引用，数据库仅保存摘要。Capability Pack 通过 `documents.processingProfile` 与 `documents.requirements` 声明资料要求，也可继续使用旧的 `{category, required}` 列表。

Capability Pack 可声明所需资料分类，不向用户暴露 Resource Slot 或 Manifest Slot。无法自动匹配时，产品只提示选择所需业务资料。Connection、ConnectionVersion、ConnectorDefinition、ResourceDefinition、ResourceBinding 和 ResourceSnapshot 仅作为既有数据库与旧 API 的弃用兼容结构保留；新资料上传、业务绑定、Assessment/Run 和 Tool 执行链不得依赖它们。Capability Pack v1 与 v2 可并存，旧历史评估继续按原快照读取。

Capability Pack 发布时必须把 `strategy://...@version` 解析为项目内不可变 `StrategyVersion`，编译后要求 ExecutionPlan 的注册 Agent、Tool 依赖与 Manifest 声明完全一致，并把 StrategyVersion、Spec/Plan Hash、Registry Snapshot、模型和依赖引用写入版本快照。Workbench 运行只能使用该 StrategyVersion 创建标准 Run；绑定级 `configuration` 作为运行输入传入，并连同哈希冻结到 Evaluation provenance。项目保存的 Agent、Tool 和 Model 配置只有合并进 SwarmSpec 并发布后才具有运行语义。

项目管理员可从可信能力包版本复用 WorkItem/Input/Output Schema、Report 和 View 等业务资产契约，并选择策略管理中已发布的不可变 StrategyVersion 后发布新的能力包版本。服务端从该 StrategyVersion 的冻结 ExecutionPlan 读取预算、Agent、Model 和 Tool 依赖，校验 Manifest 声明完全一致，不接受浏览器生成的依赖快照。需要调整运行策略、Agent 或 Tool 时，必须先在策略管理中修改草稿并发布新版本；密钥继续由 Secret/Capability Token 注入，不得进入 Manifest 或项目绑定配置。

Business Workbench 通用实体：

- WorkItem/WorkItemRevision：业务状态和不可变输入快照；
- BlobObject/WorkItemAttachment：运行前文件和附件清单；
- Evaluation：一次业务评估，关联 WorkItemRevision、Run 和全部版本快照；
- Finding/FindingAction：问题、确认、分派、豁免、解决和重新打开；
- Report：结构化 JSON 结果和 HTML/PDF Artifact；
- RuleSet/Draft/Version：可编辑草稿与不可变发布版本。

WorkItem 保存业务状态，Run 保存执行状态，二者不能互相覆盖。通用表只保存 Schema 校验后的通用 payload；强关系、高频聚合数据使用以 work_item_id 关联的领域扩展表，不持续向通用表增加业务列。

兼容边界：业务扩展只新增业务能力，不改变 Run、Artifact、Strategy、RunEvent 和控制命令语义；禁用 Pack 只阻止新执行，历史数据按快照读取；数据库变更只新增 migration；REST/MCP 复用同一 Workbench 服务；业务事件使用独立命名空间，不修改 `run.*`。

### 6.2 文档、知识与证据

文档能力共享 BlobObject、BusinessDocument、BusinessDocumentVersion、Page、Chunk、Table、Extraction 和 Evidence 语义，不建立第二套二进制存储。Evidence 至少包含来源 Blob 与文件版本、页码、可选归一化坐标、文本片段、哈希和生成能力版本。

OCR、分类和字段抽取先通过版本化 JSON Schema，再进入确定性规则或跨文件 Tool。低置信度或缺失证据固定进入失败、降级或 `REVIEW_REQUIRED`，不得自动形成合规结论。抽取按 tenant/project、Blob SHA-256、Provider/Agent/Schema 版本去重。

### 6.3 AI 质量评测

AI 结果统一包含 `data`、`evidence`、`confidence`、`qualityFlags`、`schemaVersion`，provenance 冻结模型、Prompt、Provider、Agent、Tool 和规则版本。`confidence` 必须基于任务样本校准，不直接使用模型自报概率。

质量控制分三阶段：

1. 离线评测：版本化脱敏样本集，按任务记录分类、OCR、字段/表格抽取、检索、引用和复核指标；
2. 运行时质量门：Schema、证据完整度、置信度、确定性规则和跨文件检查；
3. 生产反馈：记录人工改判、漏检、豁免和漂移，确认脱敏后才能进入新评测集或训练流程。

业务 `Evaluation` 不复用为 AI 评测记录。AI 评测使用 BenchmarkSuite、QualityEvaluationRun、SampleCase、MetricResult 和 ReviewDecision 语义；产品事实保存在 PostgreSQL，Phoenix 只用于 Trace、实验和诊断。

### 6.4 目标业务落位

以下表格固定业务扩展边界；是否已经实现以开发计划的证据索引为准：

| 能力 | 落位 |
|---|---|
| 基础 AI 与质量评测 | Provider、原子 Tool 和质量平面，不建设成业务 Agent；产品入口复用 `swarm-calibration` 的证据冻结、确定性评分、主备路由、人工复核与审计链 |
| 文件结构化 | 共享 Document Intelligence，由解析/OCR、文档 Tool 和分类/抽取 Agent 组成 |
| 文件完整性 | `contract-integrity` Pack，确定性 RuleSet 为主 |
| 履约计划与采集 | `contract-performance` Pack，沉淀义务、里程碑和执行证据 |
| 发票一致性 | `invoice-assurance` Pack，抽取后执行确定性规则 |
| 偏差分析 | 时间/内容/成本计算 Tool 加根因解释 Agent |
| 报告生成 | 结构化结果聚合、版本化模板和 AI 叙述，JSON 为事实 |
| 调度校准 | Runtime 决策加质量监督 Agent 建议 |
| 招采与供应商风险 | `procurement-supplier-risk` Pack；共享冻结文档与业务事实，确定性条款/风控/绩效规则，监控快照、预警和工单复用统一应用服务 |

### 6.5 合同七维后评价能力包

`contract-post-evaluation@1.6.0` 复用 Capability Pack v2、BusinessObject/Case、业务资料库、
StrategyVersion、Tool Gateway、Evaluation 和 Report 闭环，不建立独立业务服务。合同作为
`PRIMARY` Subject，供应商可作为 `RELATED` Subject；业务资料库中的文件可绑定到合同后评价等
一个或多个业务工作。运行前由 Workbench 按资料分类与 Subject 关联选择可用文件，缺少必需资料时
提示用户补充或选择，不要求创建 Connection、登记 Resource 或配置资源槽位。

运行时不会直接信任案件中的聚合结果。Workbench 在创建 Assessment/Run 时写入
DocumentUsageSnapshot，冻结文件版本、Blob ID、SHA-256、大小、类型和已有处理证据；Temporal 通过
`tool://document/read-versions@1` Activity 只读取这些冻结版本。业务能力包配置页继续展示已冻结的
Strategy、Agent、Tool、模型解析方式和权限依赖，但资料准备统一在业务资料库完成。工作台复用
Workbench/Case 应用服务创建业务对象或工作项并发起评价，提交后进入统一 Run 详情，不在前端建立
第二套执行逻辑。

`agent://contract/post-evaluation-analyst@1` 只消费已冻结的文档描述符与已有结构化处理结果，再进入
确定性七维评分与 PDF 生成。共享 Document Intelligence 已由
`document-structuring@1.0.0` 补齐 ODF/OOXML/PDF/文本/图像解析、逐页 OCR 路由、表格与切片、
Schema 抽取候选、质量门、人工确认和 Artifact 发布。大文件使用独立 Temporal Workflow，
页组结果写 Artifact，运行历史只保留引用、哈希和计数。真实 OCR/NLP Provider 的生产资格仍以
开发计划 DS-E1 的开放项为准，未通过资格时不得回退到 Fake 结果。
模型调用继续经过 Model Gateway；本地真实 Agent 可通过 LiteLLM
代理，或使用 `SWARMCORE_MODEL_PROVIDER_URL` 和 `SWARMCORE_MODEL_PROVIDER_API_KEY` 直连
OpenAI 兼容 Provider。生产环境禁止直配 Provider 凭据，仍必须通过 Secret Manager 完成资格验证。

七个评价维度和默认权重如下：

| 维度 | 默认权重 | 确定性口径 |
|---|---:|---|
| 文件完整性 | 10% | 必备文件有效率；缺少必备文件清单时进入人工复核 |
| 进度履约 | 20% | 到期义务按期完成，逾期完成按 50% 计分，未到期义务不纳入分母 |
| 质量履约 | 15% | 验收通过、条件通过、拒收和待验收按固定分值聚合 |
| 成本控制 | 15% | 合同金额与实际成本的超支率；缺少成本事实时进入人工复核 |
| 发票合规 | 15% | 按金额校验合同匹配、验收匹配、税务有效和重复发票 |
| 偏差治理 | 10% | 偏差关闭率与未关闭偏差严重度加权 |
| 风险治理 | 15% | 风险关闭率、风险级别和整改措施逾期情况加权 |

七维权重允许在项目绑定配置中调整，但总和必须为 100。评分、等级、风险级别和关注项均由
确定性 Tool 生成；无登记发票、偏差或风险按“评价期内无记录”处理，缺少文件、履约、验收或
成本证据则输出 `DATA_INSUFFICIENT` 并要求复核，禁止模型补造事实。结构化 JSON 是报告事实源，
PDF 和页面展示只消费同一结果；后续如增加 AI 叙述，只能解释冻结结果，不能改写分数和证据。

`contract-post-evaluation@2.0.5` 在上述边界内扩展为证据域并行策略。资料要求覆盖主合同、验收、
履约、发票、偏差、风险、招采和补充结构化事实，单次 Assessment 最多冻结 100 份文件，并按每类
`maxCount` 进行稳定截断。运行先读取冻结版本，再分别生成合同、履约质量、财务发票、偏差风险四类
证据视图；四个领域 Agent 并行输出带文档版本证据引用的结构化事实，证据复核 Agent 只判断是否需要
人工确认，报告叙述 Agent 只解释已冻结评分。领域事实经确定性合并、进度、金额、发票、偏差、风险
和一致性 Tool 校验后，仍由 `tool://contract/post-evaluation@1` 计算七维分数。

策略 `strategy://contract-post-evaluation/generate@13` 包含 26 个节点、6 个 Agent、14 个 Tool；
四个领域 Agent 均等待四类证据检索和资料覆盖检查完成后再作为同一批次并行执行，
`maxParallelism=4`、`maxTokens=500000`、`maxCostUsd=3`、`maxDuration=PT45M`。证据检索扫描全部
冻结文件，但每个领域仅向 Agent 注入 Top 6 命中；单次结构化输出上限为 8192 tokens，模型调用
超时为 300 秒。6 个 Agent 均使用 `node_only` 上下文，只接收节点已选证据和诊断，不重复注入
完整 Run 输入或其他领域依赖输出，避免多领域长上下文和 JSON 在旧边界处失败。资料缺失、不可读、
事实冲突或低置信度会经过 Router 进入 Approval；无阻塞时自动继续。最终
`schema://contract/post-evaluation-result@2` 在原七维结果上追加资料覆盖、冲突、人工复核、
诊断、叙述和版本来源，JSON、PDF 和 Evaluation 持久化仍使用同一冻结结果。PDF 节点固定引用
`tool://report/render-post-evaluation@3`，采用确定性 ReportLab 渲染和 CJK 字体，保证中文标题、
等级、复核结论及改进建议在持久化报告中可显示、可换行和可复现。

合同后评价在同一 Subject 上查找各业务工作最近一次成功且有结构化结果的 Assessment，按 `evaluationId + outputSchemaVersion + resultHash` 冻结上游引用。只有能通过后评价强类型 payload 校验的义务、偏差、发票和风险字段可以覆盖模型重算候选；不兼容结果保留冲突记录并回退到当前证据链，最终报告 provenance 必须列出实际复用字段。

### 6.6 偏差分析能力包

`deviation-analysis@1.0.5` 是独立业务能力包，复用 Business Work、Case、Workbench、
Business Document Library、Temporal、Evaluation、Report、Audit 和 Outbox，不建立业务专用
微服务。分析对象作为 `PRIMARY` Subject；运行输入必须给出分析期、数据截止日和
`TIME/CONTENT/COST` 维度。

Workbench 只从当前 tenant/project、业务工作绑定和 Subject 范围内选择 `AVAILABLE`、未过期且
安全扫描通过的当前文件版本。范围、进度和成本基线出现多个候选时必须由用户给出
`baselineVersionIds`；`includeVersionIds` 用于固定优先文件，`excludeVersionIds` 明确排除文件。
运行前冻结文件版本和 SHA-256，并分别生成 selection、baseline、configuration 和 attachment
哈希。Agent 不拥有文件选择权。

策略 `strategy://deviation-analysis/execute@6` 使用 6 个窄职责 Agent、14 个 Tool、
`maxParallelism=4`、`maxTokens=160000`、`maxCostUsd=2` 和 `node_only` Agent 上下文。
时间、内容、成本和趋势数值只由确定性 Tool 计算：里程碑偏差使用实际日或预测日减当前基线日；
内容状态固定映射为 `1/0.5/0.25/0`，缺少权重时显式标记等权回退；当前 BAC 等于原始 BAC 加批准
变更，EAC 与当前 BAC 比较，AC 和 commitments 分列；PV/EV 不齐时不生成 SPI，跨币种且无冻结
汇率时成本维度为 `CONFLICTED`。各维度独立输出 `OK`、`DATA_INSUFFICIENT`、
`CONFLICTED` 或 `NOT_APPLICABLE`。

AI 只提取证据事实、形成根因假设、责任建议和报告叙述，不得改写确定性指标。责任结果初始状态
固定为 `PROPOSED`，页面与 PDF 明示必须人工确认。基线歧义、重要证据冲突、阻断维度或责任建议
经 Router 进入 Approval。`schema://deviation-analysis/result@1` 是趋势图、结果页和 PDF 的唯一
事实源，JSON/PDF 由同一幂等记录 Tool 持久化并写入审计与 Outbox。

### 6.7 发票一致性校验能力包

`invoice-assurance@1.0.0` 是独立业务能力包，复用 Business Work、Case、Workbench、
Business Document Library、Temporal、Evaluation、Report、Approval、Finding、Audit 和 Outbox，
不建立发票专用微服务。发票作为 `PRIMARY` Subject；资料槽位覆盖发票原件、合同/订单、收货/验收、
供应商主数据、应付台账与预算付款政策。

策略 `strategy://invoice-assurance/assess@2` 使用 3 个窄职责 Agent、15 个 Tool、
`maxParallelism=3`、`maxTokens=80000`、`maxCostUsd=1.5` 和 `node_only` Agent 上下文。
XML/结构化原件优先解析；金额税额、主体、重复、商业匹配和付款门禁由确定性 Tool 计算。
官方查验支持授权连接器与人工协助两种模式，缺失回执时进入 `PENDING_HUMAN`/`UNAVAILABLE`，
禁止伪造成功。Agent 仅做低置信语义规范化、候选匹配和证据复核叙述，不得输出最终
`PAYMENT_READY` 或改写 Tool 规则结果。硬阻断（查验不一致、已付款重复、销售方税号不一致、
未批准收款账户等）只能补正后新建 Assessment。

`schema://invoice-assurance/result@1` 是页面、JSON 与 PDF 的唯一事实源；总体结论为
`PAYMENT_READY`、`REVIEW_REQUIRED` 或 `PAYMENT_BLOCKED`，与 Run 成功状态分离。

P1 的企业公示状态增强检查只消费授权连接器或人工提交的可追溯证据，不抓取 GSXT、
不绕过验证码；证据缺失或身份/来源不完整时返回 `UNKNOWN` 并进入复核。批量提交通过
`InvoiceAssuranceOperationsService` 复用同一 Case/Assessment 服务，每票保持独立状态，
单批最多 100 项且并行度配置限制为 1–10；批次及条目按 tenant/project 持久化并启用 RLS。
P2 趋势读取同一项目的历史发票 Evaluation，按日、周或月聚合总体结论及
`FAIL/WARN/UNKNOWN` 规则命中。REST 与 MCP 均复用该应用服务。

### 6.8 合同履约计划与采集能力包

`contract-performance@1.0.17` 复用 BusinessObject/Case、业务资料库、Temporal、
Model/Tool Gateway、Approval、Finding、Artifact、Audit 和 Outbox。合同是唯一 `PRIMARY`
Subject；组合合同不在当前边界。初始化与增量采集分别由
`strategy://contract-performance/initialize@13` 和
`strategy://contract-performance/collect@10` 编排，只有计划提取和执行证据候选关联使用
窄职责 Agent。日期金额规范化、批准变更应用、依赖拓扑、甘特、证据交叉键、SLA、里程碑、
付款门禁、提醒和最终哈希全部由确定性 Tool 计算。上下文检索从冻结全文 Artifact 取 Top-K
窗口并保留匹配页证据；Agent 不直接调用检索 Tool，避免无界工具循环。

专用持久化模型保存 Case、不可变计划版本、执行证据及链接、结果快照和逐源游标，并通过
`0017_contract_performance` 启用 tenant/project RLS。失败源游标不推进；重复源记录按
`sourceRef/sourceRecordId/contentHash` 去重；同一幂等键不能提交不同采集请求。已批准变更创建
当前基准但不覆盖原始基准，未批准或未生效变更只形成风险。付款证据早于验收、累计金额超过上限、
SLA 不达标、多候选或无稳定合同交叉键均进入人工复核，不能由 Agent 输出最终验收或付款结论。

REST 提供 Case 创建、计划初始化/发布、增量采集、计划、甘特、证据账和快照读取；MCP 提供
初始化、采集、计划和快照四个 Tool，二者调用同一个 `ContractPerformanceService`。结果页、
JSON 和 CJK PDF 以 `schema://contract-performance/result@1` 及 `resultHash` 为共同事实源。
页面展示原始/当前/实际三层日期、证据收件箱、付款门禁、变更历史和追溯哈希。当前实现状态及
未完成的真实数据/生产资格门禁以开发计划为准。

### 6.9 智能体调度校准能力包

`swarm-calibration@1.0.4` 以真实 GitHub Issue 为业务输入，通过 Activity 获取 Issue、评论、
时间线、关联 Pull Request、changed files 和合并提交，冻结 URL、ETag、获取时间、响应哈希及
40 位 commit SHA。调度、主诊断、备用诊断和质量监督四个窄职责 Agent 只提供结构化建议；
Runtime 负责实际路由、重试和主失败后的备用切换，确定性 Tool 负责质量评分与最终状态。

质量阈值为 85；Schema、来源、证据、一致性、沙箱和验收标准共六维评分。沙箱未通过时总分
封顶 79，首次未达标自动修订一次，仍未达标进入人工复核。仓库测试在禁网、只读、去权、
资源受限且 digest 固定的专用 Docker 镜像中执行。REST
`POST /v1/projects/{projectId}/swarm-calibration:run` 与 MCP `run_swarm_calibration`
复用 `BusinessWorkService`。`0018_swarm_calibration` 保存租户隔离的不可变证据、路由、
质量和备用切换记录；Assessment 展示结果、过程、依据及哈希。完整设计与验收边界见
`docs/swarmcore-swarm-calibration-design.md`。

### 6.10 招采一致性与供应商风控能力包

`procurement-supplier-risk@1.0.4`（策略 `strategy://procurement-supplier-risk/assess@5`）
复用 BusinessObject/Case、业务资料库、Assessment、
Temporal 和统一 Gateway。条款 Agent 只从冻结的招标、投标、中标和合同资料提出语义候选，
确定性 Tool 建立四方条款血缘并分级；供应商风险只接受信用代码精确匹配或已确认内部主数据
参与计分和硬门禁，名称命中只能进入人工复核。绩效计算要求至少 3 个订单且可用指标权重不少于
60%。

内置 `CCGP_SERIOUS_ILLEGAL` Adapter 实时查询中国政府采购网；其他商业或授权来源使用
HTTPS allowlist 和 Vault `secretRef`。监控刷新仍创建标准 Case Assessment；Recorder 在同一事务
写入不可变风险快照、预警、Finding、Report、Audit 和 Outbox。预警通过受控状态机生成并处置
风控工单，动作历史不可变。REST 与 MCP 复用 `ProcurementSupplierRiskService`，Web Assessment
展示条款、真实来源、绩效、风险、历史和工单，不建立独立业务逻辑。完整设计和验收边界见
`docs/swarmcore-procurement-supplier-risk-design.md`。

2026-07-28 的真实链 Run `019fa6f0-f69f-701d-bff4-1eec4a9da397` 已通过正式 REST、
Artifact Gateway、PostgreSQL、Temporal、外部 DeepSeek 模型和 Agent/Tool Worker 完成：
结果 `BLOCK`，命中精确信用代码对应的有效政府采购禁入，11 个 Tool effect 成功，JSON/PDF、
快照、预警、工单和审计记录均已落库。公开资料未包含完整投标原件、已签合同和企业 ERP
绩效，系统分别标注证据限制并输出 `INSUFFICIENT_DATA`，未生成替代事实。

## 7. 公共契约

公共契约以 Pydantic/JSON Schema、OpenAPI、数据库 migration 和事件 Schema 为机器可执行事实；本文只固定语义，避免复制完整字段表。

### 7.1 API 与 MCP

- Strategy：草稿、校验、编译、发布和不可变版本；
- Run：创建、查询、结果、事件、pause/resume/cancel/input/approval；
- Capability Center：统一目录、readiness、直接运行和 Preset；
- Workbench：Pack、WorkItem、Attachment、Evaluation、Finding、Report 和 RuleSet；
- Business Context：BusinessObject/Version/Relation、Case/Subject 和 Assessment 历史；
- Decision：DecisionAsset 版本、发布、项目绑定与执行记录；
- Business Document Library：文件登记与上传、不可变版本、业务对象关联、业务工作绑定、处理结果和运行使用快照；
- Governance：Artifact、Audit、Policy、Webhook 和项目设置。

REST 使用 Problem Details；稳定错误至少覆盖 Schema/语义错误、策略拒绝、资料不存在、幂等冲突、版本冲突、非法状态、游标过期、预算超限、Provider 不可用，以及 Pack/Decision/Document/Blob 的业务诊断。MCP 的资料查询、业务对象写入、Case 创建/评估、结果和 Finding 查询只调用与 REST 相同的应用服务。

最终结果使用统一信封：终态、输出 Schema 版本、内联输出或 ArtifactRef、任务摘要、usage、warnings、未解决副作用、错误和 provenance。FAILED、CANCELLED、TIMED_OUT 也返回相同信封；非终态读取结果返回 `RUN_NOT_TERMINAL`。

### 7.2 数据与租户

核心数据域包括 Registry/Strategy、Run/Task/Execution/Attempt、Command/Approval、Event/Outbox、Artifact/Blob、Audit、ToolEffect、Capability Pack/Workbench、Business Context、Decision、Business Document Library 和 Quality Evaluation。具体表、字段、索引和 RLS 以当前 ORM 与 Alembic migration 为准。

所有项目数据同时保留 tenant_id 和 project_id；应用过滤与 PostgreSQL RLS 同时生效。API/Worker 使用无 BYPASSRLS 角色，每个事务设置租户上下文；跨租户维护使用独立受审计角色。业务事务中禁止同步调用 Temporal、NATS、S3 或 Webhook。

### 7.3 事件与订阅

事件信封固定包含 id、seq、type、schemaVersion、tenantId、projectId、runId、可选 taskId/attemptId、occurredAt、trace/causation/correlation 和 data。破坏性变化发布新 schemaVersion；脱敏保留信封和 seq，不能删除事件制造假 gap。

Event Gateway 提供 SSE `after`/`Last-Event-ID`、心跳、背压、历史补读和过期游标 410。Webhook 由独立 Temporal Workflow 签名、重试并记录 delivery；前端和外部调用方不得直连 NATS。

## 8. 安全、治理与可观测

- OIDC JWT 绑定 tenant/project/scope；OPA 处理模型、Tool、数据等级、预算、下载和 obligations。
- Secret 只保存引用，通过 Vault 短租约获取，不进入 Spec、Prompt、Preset、事件、日志和 Artifact 元数据。
- Tool 分 L0 纯计算、L1 只读外部、L2 有副作用、L3 不可信代码；风险决定审批、幂等、补偿和 Sandbox。
- 平台内置受控文件系统工具（`tool://filesystem/read-text@1`、`write-text@1`、`list@1`、`stat@1`）属于 L1/L2：只操作部署配置根下的 `tenant/project/logical-mount` 工作目录，经 Tool Gateway、Capability Token、OPA、EffectJournal 与审计执行。`write-text` 为 HIGH 风险且默认 `create` 不覆盖；生产禁止 `local` executor，必须使用现有 Sandbox/gVisor Job 路径并 fail closed。文件系统工具不是第二套业务资料库：合同、报告等持久化资料仍使用 BlobObject、BusinessDocument 与 Artifact；`connector://fake/files@1` 仅服务开发与测试。
- Capability Token 绑定 tenant/project/run/node/tool/effect/audience/scope/jti，短 TTL、最小权限、可撤销。
- Sandbox 强制非 root、只读根文件系统、drop capabilities、禁 host namespace/hostPath、默认拒绝出网并限制 CPU、内存、PID、磁盘和 wall time。
- Trace 贯穿 HTTP、Run、Workflow、Activity、模型、Tool、Artifact 和 Webhook；Metrics 覆盖队列、执行、成本、预算、Provider、Outbox 和投影；Audit 只追加并记录人工与策略决定。
- 日志必须结构化和脱敏，禁止 Prompt、Secret、Token、原始文件内容和跨租户标识泄露。审计可记录 filesystem 的逻辑 mount、相对路径、大小与哈希，不得记录文件内容或宿主绝对路径。
- Registry 保持只读；项目工具配置只能选择已注册工具并保存默认参数（含逻辑 mount/相对路径），不得新增 executor 或配置宿主物理路径。

## 9. 部署、容量与恢复

生产由无状态 API/Gateway、Dispatcher/Publisher、Control/Agent/Tool/Webhook Worker、Projector/Ingestor、Artifact Gateway 组成；依赖 PostgreSQL、Temporal、NATS、S3、Vault、OPA 和模型 Provider。各 Worker 使用独立 Temporal Task Queue，按队列延迟和 Provider 容量扩缩容。

本地 Compose 提供 PostgreSQL、Temporal、NATS、OPA、Vault dev、Phoenix 及核心服务；Artifact 可使用本地文件 Adapter。生产默认 PostgreSQL PITR、NATS 三副本、S3 Versioning、Vault Audit、Temporal HA/Cloud，并定期恢复演练。

Control/Agent/Tool Worker 显式限制并发 Activity、Workflow Task 与 Poller 数；增加 Worker 副本可扩展队列消费能力。单 Run 仍受冻结 ExecutionPlan 的 `maxParallelism` 约束，当前执行图是编译期静态 DAG，运行中的 Agent 不能动态创建 Team/子任务。Workflow 使用滚动就绪窗口：任一节点完成即补充其已就绪下游，不设置整批屏障。

Dispatcher、Publisher、Webhook Worker 和 Reconciler 使用 PostgreSQL `FOR UPDATE SKIP LOCKED`、租约与 fencing 分片领取，不使用 Server 全局锁。Reconciler 以 `reconciled_at` 轮转扫描，避免多副本重复锁住同一批最旧 Run。生产 Control Worker 的文档处理只接受共享 S3 Artifact Store；本地文件 Store 仅用于 local 模式。

背压顺序：租户配额 → 项目配额 → Strategy 并行度 → Temporal Queue → Provider RPM/TPM → Tool/Sandbox 容量。饱和时保持有界队列和明确状态，不以无限协程或缓存吸收压力。

## 10. 验证与发布门禁

| 变化 | 最低验证 |
|---|---|
| Python | Ruff、mypy strict、相关单元测试 |
| 前端 | lint、Vitest、build；完整交互再运行 Playwright |
| 数据/状态 | migration、RLS、幂等、Outbox、状态机和集成测试 |
| Workflow | Temporal Replay、重试、取消、人工等待和 Continue-As-New |
| 安全/Provider | OPA、Secret、Capability Token、越权、故障和恢复 |
| 发布 | 干净检出、不可变 commit/image、升级回滚、备份恢复、容量和外部调用方复验 |

只有实现完成并通过相应本地测试才能标记 `IMPLEMENTED`；只有生产同构环境证据绑定同一不可变版本后才能标记 `VERIFIED`。未执行、跳过或协议 Mock 的测试必须明确记录。

详细里程碑和当前证据只在 [开发计划](./swarmcore-development-plan.md) 维护；UI 约束只在 [UI 规范](./swarmcore-ui-guidelines.md) 维护。

## 11. 仓库边界

| 位置 | 职责 |
|---|---|
| `apps/` | API、Gateway、Dispatcher、Worker、Web 和运维进程 |
| `packages/domain` | 纯领域类型和状态机，不依赖框架或数据库 |
| `packages/application` | 统一应用服务、命令、查询、Workbench 和能力中心 |
| `packages/spec` / `compiler` | SwarmSpec、条件和不可变 ExecutionPlan |
| `packages/runtime-temporal` | 确定性 Workflow 与 Activity 契约 |
| `packages/registry` | 不可变能力定义、Pack 和 Snapshot |
| `packages/persistence` | ORM、Repository、RLS 和 Alembic |
| `packages/tool-gateway` / Adapter | Provider 和 SDK 隔离边界 |
| `packages/capability-*` | Manifest、Schema、Strategy、规则、报告和 View，不依赖 FastAPI/SQLAlchemy/Temporal |
| `tests/` | unit、integration、fixture 和端到端证据 |
| `agno/`、`agent-ui/` | 上游参考代码，不属于 SwarmCore workspace，不修改 |

## 12. 架构决策

| ID | 决策 |
|---|---|
| ADR-001 | Agno 作为首选 Agent Runtime Adapter |
| ADR-002 | Temporal 是唯一耐久执行引擎 |
| ADR-003 | PostgreSQL 是产品状态事实源 |
| ADR-004 | SwarmSpec 使用声明式 JSON Schema；条件禁止 `eval` |
| ADR-005 | Transactional Outbox 解决数据库与外部系统一致性 |
| ADR-006 | NATS JetStream 只承担事件分发 |
| ADR-007 | REST 与 MCP 是统一应用服务的并列 Adapter |
| ADR-008 | Tool 只能经 GatewayProxyTool 和 Tool Gateway 调用 |
| ADR-009 | 不可信代码使用 Kubernetes Job + gVisor |
| ADR-010 | StrategyDraft 可变，StrategyVersion 和 ExecutionPlan 不可变 |
| ADR-011 | 控制台只调用公开接口，不形成独立执行语义 |
| ADR-012 | Registry、Readiness、Run 三层分离，健康状态不写回 Registry |
| ADR-013 | 业务扩展采用五层三横切，复用 Capability Pack 与 Workbench |
| ADR-014 | 业务 Evaluation 与 AI QualityEvaluation 分离 |
| ADR-015 | BusinessObject、Case、Assessment 与 Run 分离，运行只消费冻结事实 |
| ADR-016 | Case/Assessment/DecisionAsset 分别兼容投影到 WorkItem/Evaluation/RuleSet，不复制状态机或业务逻辑 |
| ADR-017 | 业务资料库只管理用户文件及业务绑定；文件版本不可变，Assessment/Run 冻结实际使用的 Blob 与内容标识 |

参考规范：Temporal Python/Workflow Determinism、MCP 2025-11-25、OpenTelemetry、NATS JetStream、Agno AgentOS、AG-UI。依赖版本以 lockfile 和部署清单为准。
