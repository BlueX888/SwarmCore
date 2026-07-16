# SwarmCore 多 Agent 编排执行运行时系统设计

| 属性 | 值 |
|---|---|
| 文档状态 | Baseline / 可实施 |
| 版本 | 1.1 |
| 日期 | 2026-07-16 |
| 目标版本 | SwarmCore v1 |
| 维护者 | SwarmCore Team |
| 适用范围 | DeepTalk 及其他调用方通过 API、MCP 或配置驱动的多 Agent 编排与耐久执行 |

## 1. 摘要

SwarmCore 是一个协议无关的多 Agent 编排执行运行时。DeepTalk 根据用户目标自主选择 Agent、工具和编排方式，可通过 MCP 或 REST API 提交执行方案；其他系统也可通过 REST API 或配置/CLI 接入。所有入口共享同一套应用服务和 SwarmSpec 语义：系统将方案规范化为 SwarmSpec，编译成不可变 ExecutionPlan，由 Temporal 耐久工作流解释执行，并将结构化结果、Artifact 和执行状态返回调用方。Agno 负责具体 Agent、Team、模型和工具调用；SwarmCore 负责方案校验、实例生命周期、调度、状态、可靠性、安全、事件和结果交付。

DeepTalk 是目标理解和编排决策方，SwarmCore 是受控执行方。REST API 是公开扩展与系统集成接口，MCP 是适合智能体调用的协议适配器，两者不存在主从关系；控制台是基于同一 REST API 的人工测试与观测客户端，不建立独立执行链路。多租户能力作为部署隔离和安全边界保留，不作为产品核心定位。

本设计固定以下边界：

1. Agno 是 Agent 能力层，不是系统级调度状态源。
2. Temporal 是唯一耐久执行引擎，不同时引入 Celery、Dramatiq 或第二套工作流状态机。
3. PostgreSQL 是产品状态、权限、审计和查询的唯一事实源。
4. Temporal Event History 是执行引擎内部数据，不直接暴露给调用方或前端。
5. NATS JetStream 只承担事件分发和旁路异步处理，不保存最终业务状态。
6. 用户编排默认使用声明式 SwarmSpec、CEL 和受限模板，不允许上传任意 Python 作为策略。
7. 不可信代码只能通过 Sandbox Manager 进入隔离运行环境。
8. 前端采用 React 19 + Vite + TailAdmin × Radix 设计系统，不继续扩展现有 Next.js Agent UI 壳。
9. REST、MCP、配置/CLI 和控制台不得形成不同执行语义，统一复用应用服务、权限、编译、命令和结果契约。

## 2. 目标与非目标

### 2.1 目标

- 建立协议无关的编排执行内核，统一接收 REST API、MCP 和配置/CLI 输入。
- 支持 DeepTalk 自主生成并提交 SwarmSpec，同时允许其他系统通过公开 API 扩展接入。
- 支持顺序、并行、DAG、路由、循环、主管、评审、投票和子蜂群。
- 支持长时间运行、进程重启恢复、暂停、继续、取消、超时、重试和人工审批。
- 支持运行中动态派生任务，但所有动态操作必须经过权限、预算和结构校验。
- 提供 Run、Task、Attempt、AgentInstance、Event、Artifact 的统一状态模型。
- 提供结构化结果、实时事件流、Webhook 和历史回放。
- 提供租户隔离、权限控制、Secret 管理、工具策略和代码沙箱。
- 提供完整 Trace、指标、日志、成本和审计。
- 支持单机开发以及 Kubernetes 生产部署。

### 2.2 非目标

- 不自研基础大模型推理引擎。
- 不把 SwarmCore 设计成 Prompt/Agent Marketplace。
- v1 不支持调用方上传并在控制面进程内执行任意编排代码。
- v1 不承诺外部副作用的 exactly-once；系统提供 at-least-once 执行、幂等键和补偿机制。
- v1 不把 Kafka、Qdrant、Kata Containers 设为强制基础设施。
- v1 不提供面向普通终端用户的通用聊天产品；终端用户交互由 DeepTalk 负责。
- 控制台只面向人工测试、执行观测和问题诊断，不承载 DeepTalk 产品逻辑或独立执行语义。

## 3. 质量目标与默认限制

### 3.1 SLO

| 指标 | 目标 |
|---|---|
| 控制面 API 可用性 | 月度 99.9% |
| POST /runs 接受延迟 | p95 小于 300 ms，不含首次大型 Spec 编译 |
| 已编译策略提交延迟 | p95 小于 150 ms |
| durable event 到 SSE 可见延迟 | p95 小于 1 s |
| 有空闲 Worker 时排队到开始 | p95 小于 5 s |
| Worker 故障后的任务恢复 | 60 s 内重新认领或进入重试 |
| 状态投影一致性延迟 | p95 小于 1 s，p99 小于 5 s |
| 生产备份 RPO | 小于等于 5 min |
| 生产恢复 RTO | 小于等于 30 min |

LLM Provider 自身延迟和外部工具延迟不计入控制面 API SLO，但计入 Run 端到端耗时。

### 3.2 默认运行限制

以下值为部署默认值。租户策略可以降低，只有平台管理员可以提高。

| 限制 | 默认值 |
|---|---|
| 单 Run 最大 AgentInstance | 32 |
| 单 Run 最大并行节点 | 8 |
| 最大子蜂群深度 | 4 |
| 单 Loop 最大迭代 | 20 |
| 单 Run 最大持续时间 | 60 min |
| 单 Task 最大持续时间 | 15 min |
| 单模型调用超时 | 120 s |
| 单工具调用超时 | 300 s |
| 默认最大 Token | 1,000,000 |
| 默认最大成本 | 25 USD |
| 单 Artifact 默认最大值 | 100 MiB |
| 单 Run Artifact 总量 | 1 GiB |
| 单 Spec 最大值 | 1 MiB |
| 编译后 ExecutionPlan 最大值 | 512 KiB |
| Temporal Activity 内联结果最大值 | 256 KiB |
| 单 Run durable event | 100,000 |

## 4. 技术基线

| 层 | 固定选型 | 说明 |
|---|---|---|
| 语言 | Python 3.12 | 控制面、Worker 和 Adapter |
| Agent SDK | Agno 2.7 系列 | Agent、Team、模型、工具、Session |
| API | FastAPI + Pydantic v2 | 基于 AgentOS 扩展 |
| Durable Execution | Temporal Python SDK | Workflow、Activity、Signal、Update、Query |
| Spec | JSON Schema 2020-12 | Pydantic 生成并进行跨端校验 |
| 条件表达式 | CEL | 禁止 Python eval |
| 模板 | Jinja2 SandboxedEnvironment | StrictUndefined + 过滤器白名单 |
| 主数据库 | PostgreSQL 17 | 产品状态和审计事实源 |
| ORM/迁移 | SQLAlchemy 2.0 + Alembic | asyncio 会话 |
| 事件总线 | NATS JetStream | 生产集群 3 副本 |
| 临时缓存 | Valkey | 可选；缓存、限流和短期信号 |
| Artifact | S3 API | 云 S3 或 Ceph RGW；开发环境文件系统 |
| 向量 | pgvector | v1 与 PostgreSQL 共存 |
| 模型网关 | LiteLLM Proxy | Provider 路由、预算、限流和成本 |
| 本地模型 | vLLM | OpenAI 兼容接口 |
| 策略引擎 | OPA | RBAC 之外的运行时授权和 obligations |
| Secret | Vault Provider | 生产默认；接口支持云 Secret Manager |
| 沙箱 | Kubernetes Job + gVisor | L3 风险可切换 Kata |
| Telemetry | OpenTelemetry | Trace 和 Metrics |
| AI Observability | Arize Phoenix | OpenInference Trace、评测和实验 |
| Metrics | Prometheus + Grafana | 系统指标与告警 |
| Logs | Python logging + Alloy + Loki | 结构化日志 |
| Web | React 19 + TypeScript + Vite | 测试与观测控制台 |
| Router | React Router v7 Data Mode | 固定 v7 最新 minor |
| Design System | shadcn/ui + Radix + Tailwind CSS v4 | 依赖 b-design-system-tailadmin-radix |
| Graph | React Flow 12 | 策略编辑和运行拓扑 |
| Server State | TanStack Query v5 | API 查询与 Mutation |
| Client State | Zustand 5 | 画布、选择、草稿和偏好 |
| Forms | React Hook Form + Zod | 配置表单 |
| Testing | pytest、Vitest、Playwright | 后端、前端和视觉回归 |

所有依赖在 lockfile 或部署清单中固定完整版本。升级先通过兼容测试，不使用浮动 latest 镜像。

## 5. 系统上下文

~~~mermaid
flowchart LR
    DeepTalk[DeepTalk Agent]
    External[其他系统 / 扩展调用方]
    CLI[配置 / CLI]
    UI[SwarmCore 测试控制台]
    Rest[REST API Adapter]
    MCPIn[MCP Server Adapter]
    App[统一应用服务]
    IdP[OIDC Identity Provider]
    Models[Cloud LLM / vLLM]
    Tools[MCP / HTTP / Internal Tools]
    Store[S3 Artifact Store]

    DeepTalk --> MCPIn
    DeepTalk --> Rest
    External --> Rest
    CLI --> Rest
    UI --> Rest
    MCPIn --> App
    Rest --> App
    MCPIn --> IdP
    Rest --> IdP
    App --> PG[(PostgreSQL)]
    PG --> Dispatcher[Outbox Dispatcher]
    Dispatcher --> Temporal[Temporal Cluster]
    Temporal --> Worker[Swarm Workers]
    Worker --> ModelGateway[LiteLLM]
    ModelGateway --> Models
    Worker --> ToolGateway[Tool / A2A Gateway]
    ToolGateway --> Tools
    Worker --> ArtifactGateway[Artifact Gateway]
    ArtifactGateway --> Store
    Worker --> Ingestor[Runtime Event Ingestor]
    Ingestor --> PG
    PG --> Publisher[Event Outbox Publisher]
    Publisher --> NATS[NATS JetStream]
    NATS --> Events[Event Gateway]
    Events --> Rest
    Events --> MCPIn
~~~

## 6. 逻辑架构

~~~mermaid
flowchart TB
    subgraph ControlPlane[控制面]
        RestAdapter[REST API Adapter]
        MCPAdapter[MCP Server Adapter]
        ConfigAdapter[Config / CLI Adapter]
        Application[统一应用服务]
        Strategy[Strategy Registry]
        Compiler[Spec Compiler]
        RunService[Run Command Service]
        Dispatcher[Outbox Dispatcher]
        EventPublisher[Event Outbox Publisher]
        WebhookScheduler[Webhook Scheduler]
        Approval[Approval Service]
        Query[Run Query Service]
        EventGateway[SSE / AG-UI Gateway]
        Projector[State Projector]
        Ingestor[Runtime Event Ingestor]
        ArtifactGateway[Artifact Gateway]
    end

    subgraph DurablePlane[耐久执行面]
        Temporal[Temporal]
        ControlWorker[Control Worker]
        AgentWorker[Agent Worker]
        ToolWorker[Trusted Tool Worker]
        SandboxManager[Sandbox Manager]
    end

    subgraph CapabilityPlane[能力层]
        Agno[Agno Adapter]
        LiteLLM[LiteLLM Proxy]
        ProxyTool[Deferred GatewayProxyTool]
        OutboundMCP[Outbound MCP Connector]
        Sandbox[gVisor / Kata Sandbox]
    end

    subgraph DataPlane[数据面]
        PG[(PostgreSQL)]
        NATS[NATS JetStream]
        S3[(S3 Artifact)]
        Vector[(pgvector)]
        Vault[Vault]
    end

    RestAdapter --> Application
    MCPAdapter --> Application
    ConfigAdapter --> Application
    Application --> Strategy
    Strategy --> Compiler
    Application --> RunService
    Application --> Query
    Application --> Approval
    Application --> EventGateway
    RunService --> PG
    PG --> Dispatcher
    Dispatcher --> Temporal
    Temporal --> ControlWorker
    ControlWorker --> AgentWorker
    ControlWorker --> ToolWorker
    ControlWorker --> SandboxManager
    ControlWorker --> Projector
    AgentWorker --> Agno
    Agno --> LiteLLM
    Agno --> ProxyTool
    ProxyTool --> ControlWorker
    ToolWorker --> OutboundMCP
    SandboxManager --> Sandbox
    AgentWorker --> Ingestor
    ToolWorker --> Ingestor
    Ingestor --> PG
    AgentWorker --> ArtifactGateway
    ToolWorker --> ArtifactGateway
    ArtifactGateway --> S3
    AgentWorker --> Vault
    ToolWorker --> Vault
    PG --> Vector
    PG --> EventPublisher
    EventPublisher --> NATS
    NATS --> EventGateway
    NATS --> WebhookScheduler
    WebhookScheduler --> PG
    Approval --> PG
    Query --> PG
~~~

## 7. 服务与组件

### 7.1 接口适配层与统一应用服务

职责：

- REST API Adapter 提供公开扩展和系统集成接口，接收机器调用、控制台请求和 CLI 请求。
- MCP Server Adapter 为 DeepTalk 等智能体调用方提供能力发现、方案提交、运行控制和结果读取。
- Config / CLI Adapter 将 YAML/JSON 导入转换为与 REST 相同的资源和命令，不直接启动执行。
- 统一应用服务验证 OIDC JWT、租户、项目和 Scope，并执行速率限制、大小限制和 Schema 校验。
- 各适配器将写操作交给 Strategy Registry 或 Run Command Service，将查询交给 Run Query Service，并共享 Idempotency、Correlation ID、错误码和结果 DTO。
- 控制台只调用 REST API，不直连 PostgreSQL、Temporal、NATS、Worker 或内部应用服务。
- 创建和控制操作返回 202 RunHandle/CommandHandle 或结构化错误；协议适配器只负责协议映射，不复制业务规则。

接口适配层和应用服务无本地持久状态，可以水平扩展。任何入口都不直接执行 Agent。

### 7.2 Strategy Registry

职责：

- 管理 StrategyDefinition、可变 StrategyDraft 与不可变 StrategyVersion。
- 保存原始 Spec、规范化 Spec、ExecutionPlan、Schema 版本、运行时版本和 SHA-256。
- Draft 使用 revision/ETag 乐观并发；发布时编译快照并原子创建不可变 Version。
- Strategy 支持 active、archived，Version 支持 published、deprecated 生命周期。
- Published 版本不可修改；任何变更产生新版本。
- Inline Spec 提交时自动创建类型为 ephemeral 的不可变版本。

### 7.3 Spec Compiler

编译阶段固定为：

1. Parse：解析 JSON 或 YAML，拒绝重复 Key 和未知文档类型。
2. Structural Validate：使用 JSON Schema 2020-12。
3. Normalize：填充默认值、展开简写并生成 canonical JSON。
4. Reference Resolve：解析 Agent、Tool、Model、Knowledge 和 Subflow 引用。
5. Semantic Validate：检查环、端口类型、Join、循环边界、输出 Schema 和终止条件。
6. Policy Validate：调用 OPA 检查能力、预算、模型、工具、数据等级和沙箱等级。
7. Compile：生成不可变 ExecutionPlan。
8. Hash：对 canonical ExecutionPlan 计算 SHA-256。
9. Persist：保存编译结果和诊断信息。

编译器是纯函数组件：相同 Spec、Registry Snapshot、Policy Revision 和 Compiler Version 必须得到相同 Plan Hash。

### 7.4 Run Command Service

职责：

- 创建 Run、控制命令和 Idempotency 记录。
- 在 PostgreSQL 同一事务写入 Run/RunCommand 与 Outbox。
- 所有 start、pause、resume、cancel、approval 和 external input 都由 Outbox Dispatcher 可靠送达 Temporal。
- 接收 pause、resume、cancel、approval 和 external input。
- 不直接写 Temporal Event History 外的执行结果。

Run Command Service 只返回“命令已耐久接受”。命令最终执行或拒绝的结果通过 run_commands 状态和 command.* 事件返回。

### 7.5 Outbox Dispatcher

职责：

- 使用 FOR UPDATE SKIP LOCKED 领取 destination=temporal 的 outbox_events。
- 根据消息类型启动 Run/Webhook Workflow 或发送 Run Temporal Update。
- Start 也是 command_seq=1 的 RunCommand；创建命令时锁定 runs 行分配严格递增 command_seq。
- 对 RunCommand，每个 Run 只领取最小未完成 command_seq，使用 update_id=request_id；Workflow 保存 last_applied_command_seq 并返回历史结果以去重。Webhook Start 按确定性 Workflow ID 去重，不参与 Run command_seq。
- Workflow 尚未启动时只交付 Start；相同 Workflow ID 的 WorkflowAlreadyStarted 视为成功。超前命令不越过前序命令。
- 采用上限 5 min 的指数退避；Temporal 暂时不可用无限重试并告警，不因次数耗尽丢命令。
- 成功后标记 delivered_at；只有不可解析 payload、未知命令类型等永久错误才转入 DEAD，保留人工 redrive。

Dispatcher 不执行业务节点，不直接修改 Run 最终状态。

### 7.6 Event Outbox Publisher

职责：

- 只领取 destination=nats 的 outbox_events，与 Temporal Command Dispatcher 分开扩缩容和告警。
- 以 run_id 为 partition_key，每次只领取该 Run 最小未发布 event_seq；多实例通过行锁/租约避免同 Run 并发发布。
- 使用 event_id 作为 Nats-Msg-Id 发布到 JetStream；收到 PubAck 后才标记 delivered。
- NATS 暂时失败无限指数退避；只有 Schema/序列化永久错误进入 DEAD 并告警，不跳过 DEAD 事件伪造同 Run 顺序。
- NATS Consumer 仍按 event_id 幂等，不能把 PubAck 当作业务处理完成。

Webhook Scheduler 是 SWARM_EVENTS 的 durable consumer。它按已注册订阅匹配事件，在同一 PostgreSQL 事务插入 webhook_delivery 和 destination=temporal 的 outbox 后才 ACK；Dispatcher 以 webhook:{endpoint_id}:{event_id} 作为 Workflow ID 启动 WebhookDeliveryWorkflow，AlreadyStarted 视为成功。Scheduler 持久化消费 Cursor，若 NATS Consumer 状态或保留窗口丢失，则从 run_events 补扫。WebhookDeliveryWorkflow 唯一负责签名、重试和 delivery 状态，Event Gateway 不直接交付 Webhook。

### 7.7 Temporal Control Worker

职责：

- 运行稳定版本的 SwarmRunWorkflow 解释器。
- 根据 ExecutionPlan 计算 ready nodes。
- 调度 Agent、Tool、Transform、Approval 和 Reducer Activity。
- 管理依赖、并发、循环、子工作流、暂停和预算。
- 使用 Signal/Update 接收控制命令。
- 使用 Query 返回引擎内部轻量状态，仅用于运维诊断。

Workflow 中禁止：

- 直接调用 LLM、HTTP、数据库、文件系统或当前时间 API。
- 读取未记录的外部状态。
- 写入产品数据库。
- 产生逐 Token Temporal Event。

### 7.8 Agent Worker

职责：

- 将 AgentSpec 转换为 Agno Agent、Team 或 RemoteAgent。
- 注入 RunContext、租户、Session、模型、工具、知识和 Secret 引用。
- 调用 LiteLLM 或配置的模型 Provider。
- 只向 Agno 注入 GatewayProxyTool；原始 Function、MCP Connection 和外部 Endpoint 禁止绕过 Tool Gateway。
- 处理结构化输出、Deferred Tool Call 和 Agent Handoff。
- 发送心跳、使用量和内容增量。
- 将大型输出转为 Artifact。
- 在 Activity 结束前执行输出 Schema 校验。

Agent Worker 按模型或数据等级划分 Temporal Task Queue，避免一个 Provider 故障阻塞全部任务。

### 7.9 Tool Gateway

职责：

- 维护 ToolDefinition 和 MCP Connection Registry。
- 对每次工具调用执行 OPA 决策。
- 获取短时 Secret，不把 Secret 传回 Agent 消息。
- 校验输入输出 Schema、大小、超时和内容类型。
- 对有副作用的工具执行 idempotency_key 传递。
- 实施域名、IP、方法、文件路径和数据等级限制。
- 将高风险工具转为 ApprovalRequirement 或 Sandbox Job。

### 7.10 Sandbox Manager

职责：

- 根据风险等级创建 Kubernetes Job。
- 为 Attempt 生成一次性 Capability Token。
- 选择 RuntimeClass：runc、gVisor 或 Kata。
- 设置只读根文件系统、tmpfs、CPU、内存、PID、磁盘和 wall-time。
- 默认拒绝出网，只开放批准的目标。
- 采集 stdout、stderr、退出码和 Artifact。
- 完成后撤销 Secret、Token 并清理 Job。

Sandbox 不直接获得 PostgreSQL、Vault、S3 或 Kubernetes 管理凭据。

生产 Admission 必须强制：Restricted Pod Security、runAsNonRoot、capabilities.drop=ALL、allowPrivilegeEscalation=false、seccompProfile=RuntimeDefault、只读 rootfs；禁止 privileged、hostPID/IPC/network、hostPath、device 和 Docker/K8s Socket。Pod 设置 automountServiceAccountToken=false，使用无 RBAC 的专用 ServiceAccount；镜像以 digest 固定并通过签名白名单验证，RuntimeClass 不允许任务覆盖。

Capability Token 绑定 tenant_id、run_id、attempt_id、audience、scope、jti 和小于等于 5 min TTL，只能消费一次。出网必须经过 L7 Egress Proxy；NetworkPolicy 只负责基础隔离，Proxy 在 DNS 解析和实际连接时重复校验目标。stdout/stderr 各限制 10 MiB，Workspace 限制 1 GiB，Job ttlSecondsAfterFinished 默认 300。

### 7.11 State Projector

职责：

- 将执行事件幂等投影到 Run、Task、Attempt 和 AgentInstance 表。
- 为每个 Run 分配严格递增 event_seq。
- 同一事务插入 run_events 和 outbox_events。
- 拒绝非法状态迁移。
- 提供小于 1 秒的产品查询投影。

Temporal 决定“下一步执行什么”；State Projector 决定“产品如何查询和展示已发生的事情”。

### 7.12 Runtime Event Ingestor

职责：

- 接收 Agent、Tool 和 Sandbox Worker 产生的内容增量、usage、heartbeat 和 Artifact 事件。
- 验证 Attempt Lease Token，防止失效 Worker 继续写事件。
- 合并逐 Token 内容，每 200 ms 或 2 KiB 形成 durable content.delta。
- 调用统一 Event Repository 分配 event_seq、写 run_events 和 outbox_events。
- 对 event_id、attempt_id 和 producer_seq 幂等。
- 限制单事件 256 KiB；更大的数据先写 Artifact。

Worker 不直接对 run_events 执行任意 INSERT，所有运行时事件经 Ingestor 或同一受控 Repository 写入。

### 7.13 Event Gateway

职责：

- 从 NATS JetStream 消费 durable event。
- 提供 SSE 订阅、断点续传、心跳和背压控制。
- 对 SSE 和 AG-UI 逐资源执行 OPA，并按 obligations 做字段级脱敏。
- 前端和外部调用方禁止直连 NATS；Event Gateway 是查询/订阅的唯一出口，Webhook 推送只由 WebhookDeliveryWorkflow 执行。
- 当 NATS 中不存在旧事件时，从 PostgreSQL run_events 补读。
- 不改变 Run 状态。

## 8. 核心领域模型

### 8.1 标识

- 所有公共实体 ID 使用应用生成的 UUIDv7。
- Temporal Workflow ID：swarm:{tenant_id}:{run_id}。
- ExecutionPlan node_key 在策略版本中稳定；RunTask 是运行时 TaskInstance，task_instance_key 包含 loop iteration、fan-out key 或动态路径。
- TaskExecution 表示 TaskInstance 的一次逻辑执行 generation，持有稳定 effect_id；Temporal 自动重试不会更换它。
- Attempt ID 标识一次物理 Activity 尝试，每次 Temporal attempt 重新生成。
- Artifact ID 与对象键解耦。
- Event ID 全局唯一，event_seq 在单个 Run 内严格递增。

### 8.2 实体关系

~~~mermaid
erDiagram
    TENANT ||--o{ PROJECT : owns
    PROJECT ||--o{ STRATEGY : owns
    STRATEGY ||--o{ STRATEGY_VERSION : versions
    STRATEGY_VERSION ||--o{ RUN : executes
    RUN ||--o{ RUN_TASK : contains
    RUN_TASK ||--o{ TASK_EXECUTION : generations
    TASK_EXECUTION ||--o{ ATTEMPT : physical_attempts
    RUN ||--o{ AGENT_INSTANCE : instantiates
    RUN ||--o{ APPROVAL : waits
    RUN ||--o{ RUN_EVENT : emits
    RUN ||--o{ ARTIFACT : produces
    RUN ||--o{ MESSAGE : communicates
    RUN_EVENT ||--o{ OUTBOX_EVENT : publishes
~~~

### 8.3 状态事实源

| 数据 | 事实源 | 说明 |
|---|---|---|
| 调度进度和 durable wait | Temporal | 引擎内部 |
| 产品 Run/Task 状态 | PostgreSQL | API、UI、审计；Temporal 状态的有界延迟投影 |
| Artifact 字节 | S3 | 数据库保存元数据 |
| 事件投递 | NATS | 可重放传输，不是永久审计 |
| Trace | Phoenix | 诊断用途，不参与业务判断 |
| Cache/Rate Limit | Valkey | 可以丢失和重建 |

Temporal 对实时调度决策权威；PostgreSQL 对“命令已耐久接收”、对外查询和审计权威。查询返回 projectionSeq、projectionUpdatedAt 和 stale；控制命令的最终合法性由 Workflow 仲裁，API 不能只凭可能滞后的投影作最终拒绝。Workflow 关闭前必须等待终态投影成功。Reconciler 持续扫描 Temporal 已关闭但 PostgreSQL 未终态、长期 ACCEPTED 或投影停滞的 Run，并按 transition_id 幂等修复；永久 Schema/状态错误进入隔离队列并告警。

## 9. SwarmSpec v1

### 9.1 顶层结构

~~~yaml
apiVersion: swarmcore.io/v1
kind: SwarmStrategy
metadata:
  name: research-review
  labels:
    domain: research
spec:
  inputSchema:
    type: object
    required: [topic]
    properties:
      topic:
        type: string
  outputSchema:
    type: object
    required: [report]
    properties:
      report:
        type: string

  defaults:
    model: model://general
    timeout: PT15M
    retryPolicy: standard

  budget:
    maxDuration: PT60M
    maxTokens: 1000000
    maxCostUsd: 25
    maxAgents: 8
    maxParallelism: 4

  agents:
    researcher:
      role: researcher
      instructions: "检索并形成事实列表"
      model: model://research
      tools: [tool://web-search]
      outputSchemaRef: "#/$defs/researchResult"
    reviewer:
      role: reviewer
      instructions: "检查证据和冲突"
      model: model://general

  graph:
    entrypoint: research
    nodes:
      research:
        type: agent
        agent: researcher
        input:
          topic: "{{ input.topic }}"
      review:
        type: agent
        agent: reviewer
        dependsOn: [research]
        input:
          result: "{{ tasks.research.output }}"
      final:
        type: reducer
        dependsOn: [research, review]
        reducer: merge_object
    output:
      report: "{{ tasks.final.output.report }}"
~~~

### 9.2 支持的节点类型

| 类型 | 用途 |
|---|---|
| agent | 调用 Agno Agent |
| team | 调用预定义或内联 Agno Team |
| tool | 直接调用受控 Tool/MCP |
| transform | CEL 或内置纯函数转换 |
| router | CEL 条件或 Agent Router |
| parallel | 扇出子节点 |
| join | all、any、quorum、first_success |
| loop | 有界循环 |
| approval | 人工或管理员审批 |
| reducer | 合并多个输出 |
| subflow | 启动 Child Workflow |
| emit | 生成业务事件或通知 |

### 9.3 内置编排模板

- sequential
- parallel
- dag
- supervisor
- router
- planner_executor
- debate_review
- vote_judge
- bounded_loop

模板只生成 SwarmSpec，不绕过编译和策略检查。

### 9.4 动态执行

Agent 可以返回受限 SwarmCommand：

~~~json
{
  "type": "spawn",
  "template": "agent://researcher",
  "taskKey": "subtask-3",
  "input": {},
  "dependsOn": ["plan"],
  "reason": "需要补充证据"
}
~~~

运行时接受动态命令前必须检查：

- command Schema。
- task_instance_key 唯一性；同一静态 node_key 可产生多个 loop/fan-out 实例。
- 最大 Agent 数、深度、并行度和预算。
- 被引用 Agent/Tool 是否在 Strategy 能力清单。
- OPA 是否允许。
- 是否会形成无终止条件的循环。

v1 不允许动态命令创建新的任意模型、Secret 或未注册 Tool。

### 9.5 ExecutionPlan

ExecutionPlan 至少包含：

- plan_version
- compiler_version
- runtime_version
- spec_hash
- registry_snapshot
- policy_revision
- typed nodes and edges
- resolved resources
- retry/timeout/budget policies
- input/output schemas
- result reducer
- static diagnostics

Run 始终引用不可变 ExecutionPlan，不在运行中读取 Strategy Draft。

## 10. 执行设计

### 10.1 Workflow 类型

| Workflow | Workflow ID | 用途 |
|---|---|---|
| SwarmRunWorkflow | swarm:{tenant}:{run} | 单个 Run 主工作流 |
| SubSwarmWorkflow | swarm:{tenant}:{run}:sub:{task} | 大型或隔离子蜂群 |
| WebhookDeliveryWorkflow | webhook:{delivery} | 可恢复 Webhook |
| ArtifactCleanupWorkflow | artifact-cleanup:{date} | 保留策略清理 |

### 10.2 Activity 类型

| Activity | Task Queue | 说明 |
|---|---|---|
| load_execution_plan | swarm-control | 读取不可变 Plan |
| project_transition | swarm-control | 更新产品状态和事件 |
| evaluate_policy | swarm-control | OPA 决策 |
| execute_agent | agent-general | Agno Agent 执行 |
| execute_team | agent-general | Agno Team 执行 |
| execute_tool | tool-trusted | 可信 Tool/MCP |
| create_sandbox_job | sandbox-control | 创建隔离 Job |
| wait_sandbox_job | sandbox-control | 心跳等待并收集结果 |
| persist_artifact | artifact | 上传并保存元数据 |
| validate_output | swarm-control | JSON Schema 校验 |
| aggregate_result | swarm-control | 内置或 Agent Reducer |
| publish_webhook | webhook | Webhook 交付 |

Agno Tool/HITL 使用 Deferred Tool 协议，避免在 Activity 内等待 Workflow Update：

1. execute_agent 遇到 Tool Call 时先耐久保存 Agent continuation、canonical tool input 和稳定 tool_call_id。
2. 无需审批时返回 AgentSuspended{continuationRef, toolCallId, toolRequestRef}；Workflow 调度 execute_tool。
3. 需要审批时同时返回 ApprovalRequirement；Workflow 投影 Approval 并等待 Update，批准后才调度 execute_tool。
4. Tool 完成后 Workflow 以 continuationRef + toolResultRef 再次调用 execute_agent；拒绝则以结构化 denial 恢复 Agent。
5. continuation 必须在 Activity 返回前写入 Artifact/Session Store，且与 task_execution_id、agent_instance_id 和版本绑定。

v1 禁用 Agno Workflow、Agno 自身 durable scheduler 和整轮自动重试。Agno Team 默认是一个不透明原子节点，其内部成员不承诺独立恢复；需要独立 Task/审批/重试的 Team 必须由 Compiler 展开为 SwarmCore 节点。

### 10.3 Run 状态机

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
    QUEUED --> PAUSING
    WAITING_INPUT --> PAUSING
    WAITING_APPROVAL --> PAUSING
    PAUSING --> PAUSED
    PAUSED --> RUNNING
    WAITING_INPUT --> RUNNING
    WAITING_APPROVAL --> RUNNING
    RUNNING --> CANCELLING
    WAITING_INPUT --> CANCELLING
    WAITING_APPROVAL --> CANCELLING
    PAUSED --> CANCELLING
    PAUSING --> CANCELLING
    ACCEPTED --> CANCELLING
    VALIDATING --> CANCELLING
    QUEUED --> CANCELLING
    CANCELLING --> CANCELLED
    CANCELLING --> COMPENSATING
    COMPENSATING --> CANCELLED
    COMPENSATING --> FAILED
    RUNNING --> SUCCEEDED
    RUNNING --> FAILED
    RUNNING --> TIMED_OUT
    ACCEPTED --> FAILED
    REJECTED --> [*]
    CANCELLED --> [*]
    SUCCEEDED --> [*]
    FAILED --> [*]
    TIMED_OUT --> [*]
~~~

终态不可逆。Retry Run 创建新 Run，并记录 parent_run_id 和 retry_from_task_id。

Workflow 内部不使用单一 status 决策，而保存 lifecycle、control_state、in_flight_count、ready_count 和 wait_reasons 集合。产品 status 是确定性派生投影，优先级为 CANCELLING/COMPENSATING > PAUSING/PAUSED > RUNNING > WAITING_APPROVAL > WAITING_INPUT > QUEUED：

- in_flight_count 或 ready_count 大于 0 时，即使某分支等待审批，仍显示 RUNNING。
- 只有没有在途/就绪节点且存在未决 Approval/Input 时，才显示对应 WAITING 状态。
- 解决一个等待项后重新计算，不硬编码 WAITING_APPROVAL 到 RUNNING。

控制合法矩阵：

| 命令 | 可接受状态 | 结果 |
|---|---|---|
| pause | QUEUED、RUNNING、WAITING_INPUT、WAITING_APPROVAL | 停止新调度并 drain；最终 PAUSED 或 REJECTED |
| resume | PAUSED、PAUSING | 清除 pause request；若仍有等待则回到对应派生状态 |
| cancel | ACCEPTED、VALIDATING、QUEUED、RUNNING、WAITING_INPUT、WAITING_APPROVAL、PAUSING、PAUSED | 撤销执行并进入 CANCELLING |
| input | WAITING_INPUT 且 request_id/schema_version 匹配 | 消费一次等待请求 |
| approval | 对应 Approval 为 PENDING/DECISION_SUBMITTED | 由 Workflow Timer/Update 仲裁 |

### 10.4 Task 与 Attempt

Task 状态：

PENDING、BLOCKED、READY、SCHEDULED、RUNNING、WAITING_APPROVAL、RETRYING、SUCCEEDED、FAILED、SKIPPED、CANCELLED、TIMED_OUT。

Attempt 状态：

CREATED、STARTED、HEARTBEATING、SUCCEEDED、FAILED、CANCELLED、TIMED_OUT、LOST。

Task 是逻辑节点，Attempt 是一次物理执行。重试只新增 Attempt。

RunTask 是 TaskInstance；同一 node_key 在 loop/fan-out 中可有多个 task_instance_key。TaskExecution 是一次逻辑 generation，Workflow 创建稳定 effect_id；Temporal Activity retry 只新增 Attempt，不新增 TaskExecution。Retry Run 或显式 retry-from-task 才产生新的 execution_generation。

### 10.5 提交时序

~~~mermaid
sequenceDiagram
    participant C as DeepTalk / Caller
    participant I as REST / MCP Adapter
    participant A as Unified Application Service
    participant DB as PostgreSQL
    participant D as Outbox Dispatcher
    participant T as Temporal
    participant W as Control Worker
    participant P as State Projector

    C->>I: Submit plan / create run
    I->>A: Canonical CreateRunCommand
    A->>A: Auth + Schema + Policy + Idempotency
    A->>DB: TX insert run + start RunCommand(seq=1) + outbox
    DB-->>A: committed
    A-->>I: RunHandle
    I-->>C: 202 / structured RunHandle
    D->>DB: claim start_run_requested
    D->>T: start SwarmRunWorkflow
    T-->>D: workflow accepted
    D->>DB: mark outbox delivered
    T->>W: workflow task
    W->>P: project QUEUED/RUNNING
    P->>DB: TX state + run_event + event outbox
~~~

REST 和 MCP 提交都映射为同一个 CreateRunCommand；控制台和 CLI 通过 REST 进入该链路。如果 Temporal 暂时不可用，Run 保持 ACCEPTED，Outbox Dispatcher 继续退避重试，系统不丢失已接受的请求。

### 10.6 人工审批时序

~~~mermaid
sequenceDiagram
    participant W as SwarmRunWorkflow
    participant P as State Projector
    participant E as Event Gateway
    participant U as User
    participant A as Approval API
    participant DB as PostgreSQL
    participant D as Outbox Dispatcher

    W->>P: create approval + WAITING_APPROVAL
    P->>E: approval.required
    E-->>U: SSE
    U->>A: POST approval decision
    A->>A: Auth + OPA + optimistic version
    A->>DB: TX append candidate decision + command + outbox
    A-->>U: 202 CommandHandle
    D->>DB: claim approval command
    D->>W: Temporal Update resolve_approval(request_id)
    W->>P: timer/update 仲裁最终 decision + 重算 Run 状态
    W->>P: command.applied
~~~

Approval 状态为 PENDING、DECISION_SUBMITTED、APPROVED、REJECTED、EXPIRED、CANCELLED，并包含 expires_at、required_scope、required_decisions/quorum、input_schema、risk_summary 和 optimistic version。API 只追加唯一 actor 的候选 ApprovalDecision，并可把聚合标为 DECISION_SUBMITTED；APPROVED、REJECTED、EXPIRED 只能由 Workflow 的 Update/Timer 按 quorum 仲裁后投影。API 仅对已投影终态返回 409，其余并发请求返回 202。Workflow 按 request_id 去重；状态已变化导致命令失效时，将 Command 标记为 REJECTED 并记录原因。

### 10.7 暂停、继续和取消

- Pause、Resume、Cancel、Input 和 Approval 都先创建 RunCommand，API 返回 202 CommandHandle；Dispatcher 使用 Temporal Update 交付。
- Command 状态为 ACCEPTED、DELIVERING、APPLIED、REJECTED 或 DEAD，调用方通过 /commands/{command_id} 查询最终受理结果。
- Pause Update 将 pause_requested 设为 true；Workflow 按 request_id 幂等应用。Pause 是 drain：立即停止新调度，等待 in-flight 归零；默认 pause_deadline 为 5 min，超时后 Command REJECTED 且 Run 恢复派生状态。
- Workflow 不强杀正在执行的外部副作用。模型调用使用 TRY_CANCEL；有副作用 Tool 使用 WAIT_CANCELLATION_COMPLETED；禁止对有副作用 Activity 使用 ABANDON。
- Agent 和 Sandbox Activity 每 30 秒心跳并检查取消。
- Pause 完成后 Run 进入 PAUSED，新节点不再调度。
- Resume 使用 Update 清除 pause 标记。
- Cancel 先撤销 Attempt Lease/Capability Token 并发出合作式取消；30 秒后仍未停止的 Sandbox Job 被删除，失效 Worker 的迟到写入由 Ingestor 拒绝。
- 对已产生外部副作用的节点，Workflow 保存 compensation stack，并按确定性的逆完成序调度 Compensation Attempt。
- 有补偿时进入 COMPENSATING。补偿失败记录 unresolvedEffects 并告警；最终仍可进入 CANCELLED，但结果明确 cancellation 不等于外部事务回滚。

### 10.8 重试策略

错误分类：

| 类别 | 示例 | 策略 |
|---|---|---|
| TRANSIENT | 429、网络中断、Provider 5xx | 指数退避重试 |
| RESOURCE_EXHAUSTED | Token/并发不足 | 延迟或降级 |
| INVALID_INPUT | Schema 不合法 | 不重试 |
| POLICY_DENIED | OPA 拒绝 | 不重试 |
| MODEL_OUTPUT_INVALID | 结构化输出不合法 | 最多一次修复重试 |
| TOOL_SIDE_EFFECT_UNKNOWN | 超时但外部状态未知 | 转人工处理 |
| SANDBOX_VIOLATION | 越权、资源违规 | 立即失败并审计 |
| INTERNAL | 代码缺陷 | 有界重试后失败 |

RetryPolicy 按 Activity 固定，不能套用一个全局默认：

| Activity 类别 | attempts | timeout/heartbeat | 规则 |
|---|---:|---|---|
| load_execution_plan | 5 | StartToClose 30 s | 只读，可安全重试 |
| project_transition | unlimited infra retry | StartToClose 15 s | Schema/非法迁移为 non-retryable；transition_id 去重 |
| execute_agent/model | 2 | StartToClose 15 min；Heartbeat 45 s | 受 TaskExecution Journal 保护；Agno 不整轮重试 |
| execute_tool | 1；声明 safe/idempotent 时 3 | Tool 定义上限；Heartbeat 30 s | 副作用未知立即人工恢复 |
| create_sandbox_job | 5 | StartToClose 60 s | 按 job id 幂等创建 |
| wait_sandbox_job | 1 | ScheduleToClose=Task timeout；Heartbeat 30 s | 依赖 heartbeat 恢复，不重复建 Job |
| persist_artifact | 3 | StartToClose 5 min | artifact_id + sha256 幂等 |
| publish_webhook | 1/Workflow iteration | StartToClose 30 s | 8 次业务退避由 Webhook Workflow 管理 |

基础退避为 1 s、系数 2、最大 30 s；429 可读取 Retry-After，但不得超过 5 min。只允许一层拥有重试：Temporal 重试 Activity，LiteLLM 只对尚未收到响应的无副作用请求做最多一次传输重试，Agno 不再重试整轮，Tool Gateway 按 ToolDefinition 决定。

有副作用的工具必须声明 idempotency、compensation 或 manual_recovery 三者之一，否则不能被自动重试。

### 10.9 幂等和一致性

- POST 写接口要求 Idempotency-Key；默认保留 24 小时。
- Run 创建幂等维度为 tenant_id + project_id + operation + idempotency_key。
- Activity 执行日志键为 task_execution_id + operation；跨 Temporal retry 保持不变，attempt_no 不参与外部幂等。
- project_transition 使用 transition_id 唯一约束。
- Tool 外部幂等键为 effect_id + tool_call_id；tool_call_id 由 Agent continuation 固定，重放不得重新生成。
- State + run_event + outbox_event 必须在一个 PostgreSQL 事务中提交。
- 所有 NATS Consumer 按 event_id 幂等。
- 所有 Webhook 带 delivery_id，接收方可据此去重。

系统语义是 durable at-least-once + idempotent effect，不宣称任意外部系统 exactly-once。

Activity 启动先查 TaskExecution Journal；已有 SUCCEEDED result_ref 时直接返回。完成业务操作后先耐久写 result_ref/effect 状态，再向 Temporal 返回，覆盖“副作用成功但 Activity completion 丢失”。不具备 Provider 幂等能力的模型请求在 Worker 崩溃时仍可能重复并计费，系统只去重已成功持久化的结果，不宣称模型 exactly-once。

### 10.10 Temporal 历史控制

- Workflow 初始输入只包含 run_id、strategy_version_id、plan_hash 和 runtime_version；不放原始 Spec、消息正文或二进制。
- load_execution_plan 读取不可变 Plan；Plan 编译后不得超过 512 KiB，且 plan_hash 必须与 Run 固定值一致。
- Activity 返回值最多内联 256 KiB；更大内容先持久化为 Artifact，Temporal 只保存 ArtifactRef、摘要和 SHA-256。
- 逐 Token 内容不写 Temporal History。
- 内容增量在 Activity 内每 200 ms 或 2 KiB 聚合一次。
- 完整对话、Prompt、工具载荷和文件不通过 Workflow 参数在 Activity 之间传递，只传稳定资源引用。
- Workflow 依据 SDK continue-as-new 建议或自身确定性 Event 计数达到 10,000 时触发，禁止读取外部估算值参与 Workflow 分支。
- 只在无未完成 Update Handler、无尚未登记 completion、所有当前状态已投影的安全点 Continue-As-New。
- Continue-As-New 携带版本化 WorkflowCheckpoint：动态 TaskInstance/依赖计数、loop/fan-out 计数、in-flight 摘要、未决 Approval/Input、Timer deadline、预算使用/预留、last_applied_command_seq 与去重结果、pause/cancel flags、compensation stack、子 Workflow 引用、运行时版本。
- 发布新 Workflow 代码使用 Temporal Worker Versioning；运行中的 Run 保持绑定原版本。

## 11. 数据设计

### 11.1 核心表

| 表 | 关键字段 | 关键约束/索引 |
|---|---|---|
| tenants | id, name, status, policy_ref | name unique |
| projects | id, tenant_id, name, settings | tenant_id + name unique |
| agent_definitions | id, tenant_id, project_id, name, version, spec | project_id + name + version unique |
| tool_definitions | id, tenant_id, project_id, name, version, schema, risk | project_id + name + version unique |
| strategies | id, tenant_id, project_id, name, lifecycle | project_id + name unique |
| strategy_drafts | id, tenant_id, strategy_id, base_version_id, revision, raw_spec, diagnostics, updated_by, updated_at | strategy_id + id unique；revision 乐观锁 |
| strategy_versions | id, tenant_id, strategy_id, version, raw_spec, normalized_spec, plan, plan_hash | strategy_id + version unique；plan_hash index |
| runs | id, tenant_id, project_id, strategy_version_id, status, input, output_ref, budgets, usage, plan_hash, runtime_version, temporal_workflow_id, temporal_run_id, next_event_seq, version, projection_updated_at, parent_run_id, started_at, completed_at | tenant_id + created_at；project_id + status |
| run_tasks | id, tenant_id, run_id, node_key, task_instance_key, node_type, status, parent_task_id, iteration_no, fanout_key, subflow_depth, spawn_command_id, dependencies, output_ref, version | run_id + task_instance_key unique；run_id + status |
| task_executions | id, tenant_id, task_id, generation, effect_id, status, result_ref, journal_version | task_id + generation unique；effect_id unique |
| attempts | id, tenant_id, task_execution_id, temporal_activity_id, temporal_attempt, status, worker, lease_token_hash, producer_seq, effect_id, result_ref, started_at, heartbeat_at, finished_at, error_category, error | task_execution_id + temporal_activity_id + temporal_attempt unique |
| agent_instances | id, tenant_id, run_id, agent_definition_id, status, session_ref, model_ref, version | run_id + status |
| task_agent_instances | tenant_id, task_id, agent_instance_id, role | task_id + agent_instance_id unique |
| agent_continuations | id, tenant_id, task_execution_id, agent_instance_id, tool_call_id, continuation_ref, request_ref, status | task_execution_id + tool_call_id unique |
| approvals | id, tenant_id, run_id, task_id, tool_version, input_hash, status, required_decisions, quorum, decision, resolved_by, resolved_at, policy_revision, expires_at, resolution_reason, version | run_id + status；expires_at |
| approval_decisions | id, tenant_id, approval_id, actor_id, decision, reason, command_id, submitted_at | approval_id + actor_id unique |
| messages | id, tenant_id, run_id, task_id, sender, recipient, kind, content_ref, correlation_id | run_id + created_at |
| artifacts | id, tenant_id, run_id, task_id, object_uri, sha256, size, mime, sensitivity, retention_until | run_id；sha256 |
| run_events | id, tenant_id, project_id, run_id, task_id, attempt_id, event_seq, transition_id, type, schema_version, producer_seq, payload, occurred_at, trace_id | run_id + event_seq unique；run_id + transition_id unique；attempt_id + producer_seq unique where present |
| outbox_events | id, tenant_id, aggregate_id, destination, partition_key, source_id, type, payload, status, attempts, available_at, locked_by, locked_until, delivered_at, last_error | destination + status + available_at |
| run_commands | id, tenant_id, run_id, command_seq, type, request_id, payload, status, version, result, error, created_at, delivering_at, applied_at, rejected_at | run_id + request_id unique；run_id + command_seq unique；status + created_at |
| idempotency_keys | tenant_id, project_id, operation, key, request_hash, response_ref, expires_at | composite primary key |
| webhook_deliveries | id, tenant_id, run_id, endpoint_ref, event_id, status, attempt, next_attempt_at | endpoint_ref + event_id unique |
| webhook_schedule_cursors | tenant_id, project_id, consumer, last_event_id, updated_at | project_id + consumer unique |
| audit_logs | id, tenant_id, actor, action, resource, decision, metadata, occurred_at | tenant_id + occurred_at |

所有 RLS 保护的多租户表都物理冗余 tenant_id，并用复合外键保证它与父资源一致；不依赖跨表推导 Tenant 才能执行安全过滤。

### 11.2 PostgreSQL 规则

- 所有时间使用 timestamptz 和 UTC。
- JSON 字段使用 jsonb，但高频过滤字段必须提升为普通列。
- 状态更新使用 version 做乐观锁。
- Temporal Command Dispatcher 和 Event Outbox Publisher 按 destination 使用 FOR UPDATE SKIP LOCKED 分别领取记录。
- RunCommand 与对应 Outbox 必须同事务写入；Dispatcher 使用稳定 request_id 调用 Temporal，投影成功后更新 APPLIED/REJECTED。
- 多租户访问同时使用应用层过滤和 PostgreSQL RLS。
- API/Worker 使用无 BYPASSRLS 角色；每个事务 SET LOCAL app.tenant_id/app.project_id，事务结束由连接池强制 reset。跨租户维护使用独立受审计角色。
- 业务事务中禁止同步调用 NATS、S3、Temporal 或 Webhook。
- 审计日志只追加，不允许普通业务角色更新或删除。

### 11.3 Event 表和顺序

State Projector 在 runs 行上维护 next_event_seq：

1. 锁定目标 Run 行。
2. 按 run_id + transition_id 查询；已存在且 payload hash 相同则返回原 event_id/event_seq，不重复投影，不同则报一致性错误。
3. 校验状态迁移，再将 next_event_seq 加一。
4. 更新投影表。
5. 插入 run_events。
6. 插入 outbox_events。
7. 提交事务。

该设计保证单 Run 的 durable event 顺序；不同 Run 之间不承诺全局顺序。

project_transition 是业务 Activity 的 barrier：task/attempt.started 成功投影并取得 Lease 后，Workflow 才启动 execute_*；终态 run.completed/failed/cancelled 投影成功后 Workflow 才关闭。execute_* 每次物理启动调用 begin_attempt(activity_id, temporal_attempt) 原子创建/获取 Attempt 和 Lease，完成时先写 TaskExecution Journal/result_ref 再返回 Temporal。Heartbeat 只限频 upsert attempts.heartbeat_at，不每 30 秒生成 durable Event。

event_seq 表示 PostgreSQL 提交顺序，不等于 Worker 发生时间。UI 只按 event_seq 应用；occurred_at 仅用于展示。同一 Attempt 的 producer_seq 必须递增，跨 Producer 不承诺时间或因果顺序，因果链使用 causation_id。

v1 AgentInstance 归属 Run，可通过 task_agent_instances 参与多个 Task；有状态 session 默认同一时刻只允许一个 TaskExecution 持锁访问。需要并行时创建独立 AgentInstance；Run 终态后执行 dispose 并按保留策略保存只读 Session 引用。

### 11.4 Artifact

对象键格式：

tenant/{tenant_id}/project/{project_id}/run/{run_id}/{artifact_id}/{version}

规则：

- bucket 默认私有。
- 下载通过 Artifact Gateway 或 5 分钟预签名 URL。
- 上传先进入 staging，完成 SHA-256、大小、MIME 和恶意内容检查后提交。
- 数据库只存 object_uri，不接受用户自定义对象键。
- Artifact 默认不可变；更新产生新 version。
- 敏感 Artifact 使用独立 KMS Key 或租户 Key。

### 11.5 向量数据

v1 使用 pgvector，并保持业务行级权限：

- knowledge_documents
- knowledge_chunks
- memory_items
- artifact_chunks

每个向量行必须带 tenant_id、project_id、source_id、embedding_model 和 embedding_version。Embedding 模型改变时写入新版本，不原地覆盖。

只有在向量容量或吞吐压测证明 PostgreSQL 成为瓶颈后才迁移 Qdrant；迁移使用 Outbox 双写和校验，不改变产品事实源。

### 11.6 保留策略

| 数据 | 默认保留 |
|---|---|
| Run/Task/Attempt 元数据 | 365 天 |
| durable run_events | 90 天 |
| 原始内容增量 | 30 天 |
| Artifact | 30 天，可按项目覆盖 |
| Trace | 30 天 |
| Audit Log | 365 天 |
| Idempotency Key | 24 小时 |
| Temporal 已关闭历史 | 30 天 |

content.delta 的信封行与 seq 保留 90 天；30 天后只清空 payload/payload_ref 并标记 redacted/tombstone，不删除中间 seq。Run 维护 earliestAvailableSeq；整段 Event 到期裁剪后，旧游标按 410 协议重置。Legal Hold 可以覆盖删除计划。删除流程先写 tombstone，再异步清理 S3、向量、消息和 Trace 引用。

## 12. 事件设计

### 12.1 事件信封

~~~json
{
  "id": "019...",
  "seq": 42,
  "type": "task.completed",
  "schemaVersion": "run-event.v1",
  "tenantId": "019...",
  "projectId": "019...",
  "runId": "019...",
  "taskId": "019...",
  "attemptId": "019...",
  "occurredAt": "2026-07-15T10:20:30.000Z",
  "traceId": "4bf92f...",
  "causationId": "019...",
  "correlationId": "019...",
  "redacted": false,
  "data": {}
}
~~~

Event 是以 type 为判别字段的单一 discriminated union；每种 type 的 data 都有独立 JSON Schema。后端从 Pydantic 生成 JSON Schema、AsyncAPI 和 TypeScript Reducer 类型。脱敏必须保留信封和 seq，设置 redacted=true 并替换 data，不能删除事件造成假 gap。

### 12.2 事件类型

Run：

- run.accepted
- run.validating
- run.queued
- run.started
- run.waiting_input
- run.waiting_approval
- run.paused
- run.resumed
- run.cancelling
- run.cancelled
- run.completed
- run.failed
- run.timed_out
- run.rejected
- run.pausing
- run.compensating

Command：

- command.accepted
- command.delivering
- command.applied
- command.rejected
- command.dead

Task/Attempt：

- task.ready
- task.scheduled
- task.started
- task.retrying
- task.completed
- task.failed
- task.skipped
- task.cancelled
- attempt.started
- attempt.completed
- attempt.failed
- attempt.cancelled
- attempt.timed_out
- attempt.lost

Agent/Tool：

- agent.created
- agent.handoff
- agent.message
- model.started
- model.usage
- model.completed
- tool.requested
- tool.approval_required
- tool.started
- tool.completed
- tool.failed

Content/Artifact：

- content.delta
- content.snapshot
- artifact.created
- artifact.deleted

Approval/Policy：

- approval.required
- approval.resolved
- approval.expired
- policy.denied
- budget.warning
- budget.exhausted

### 12.3 NATS

Streams：

| Stream | Subject | Retention | Replicas |
|---|---|---|---|
| SWARM_EVENTS | swarm.events.*.* | LimitsPolicy，24 h | 3 |
| SWARM_AUDIT_EXPORT | swarm.audit.* | LimitsPolicy，7 d | 3 |

Subject 中只放 tenant_id 与 run_id，不放用户输入、Secret 或高基数业务字段。

## 13. API 设计

REST API 是 SwarmCore 的公开扩展与系统集成契约，能力覆盖方案校验、编译、执行、控制、查询和结果获取。它与 MCP 共享应用服务和领域契约，不是 MCP 的内部实现或附属接口；控制台、官方 CLI 和不使用 MCP 的 DeepTalk 集成都通过该 API 接入。

### 13.1 通用规则

- 基础路径：/v1。
- 机器调用身份：OIDC/OAuth 2.0 Authorization: Bearer JWT，校验 issuer、audience、expiry 和 scope。
- 控制台身份：OIDC Authorization Code + PKCE；API 持有 Refresh Token，并设置 __Host-swarm_session（HttpOnly、Secure、SameSite=Lax）同源会话 Cookie。Token 禁止进入 localStorage/sessionStorage。
- Cookie 会话的所有写请求必须携带 X-CSRF-Token，服务端校验 Origin 和双提交 Token；SSE fetch 使用同源 Cookie。
- 幂等：所有创建和控制 POST 强制要求 Idempotency-Key（1–128 个可打印 ASCII）；缺失返回 400。
- Trace：接受并返回 traceparent。
- 错误格式：application/problem+json。
- 时间：RFC 3339 UTC。
- 分页：cursor + limit，默认 50，最大 200。
- 乐观并发：更新接口使用 If-Match 或 version。
- tenant_id 从 JWT Claim 获取，不信任请求体内租户字段。
- 强 ETag 格式为 "{resourceType}:{id}:v{version}:s{snapshotSeq}"；If-Match 必须完整匹配，不接受弱校验器。

OpenAPI 3.1 是 REST 契约事实源，CI 生成并校验 Pydantic Server Stub、TypeScript 类型和客户端。破坏性变更只能进入新的 API 大版本。

### 13.2 Strategy API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /projects/{project_id}/strategies/validate | 结构和语义校验 |
| POST | /projects/{project_id}/strategies/compile | 返回 ExecutionPlan 摘要和诊断 |
| POST | /projects/{project_id}/strategies | 创建 Strategy |
| GET | /projects/{project_id}/strategies | 查询列表 |
| GET | /strategies/{strategy_id} | 查询 Strategy |
| POST | /strategies/{strategy_id}/drafts | 从空白或 Version 创建 Draft |
| GET/PATCH | /strategy-drafts/{draft_id} | 读取/保存 Draft，PATCH 要求 If-Match |
| POST | /strategy-drafts/{draft_id}:validate | 校验指定 revision，返回 typed diagnostics |
| POST | /strategy-drafts/{draft_id}:compile | 编译指定 revision，返回 Plan 摘要/hash |
| POST | /strategy-drafts/{draft_id}:publish | 编译 Draft 并原子创建不可变 Version |
| POST | /strategies/{strategy_id}/versions | 创建不可变版本 |
| GET | /strategy-versions/{version_id} | 查询版本和 Plan 摘要 |
| POST | /strategy-versions/{version_id}/publish | 发布版本 |
| POST | /strategy-versions/{version_id}/deprecate | 标记弃用 |

### 13.3 Run API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /projects/{project_id}/runs | 创建 Run |
| GET | /runs/{run_id} | Run 快照 |
| GET | /runs/{run_id}/result | 终态结果；未完成返回 409 |
| GET | /runs/{run_id}/tasks | Task 列表 |
| GET | /runs/{run_id}/events | SSE |
| GET | /runs/{run_id}/event-history | 分页 durable event 历史 |
| GET | /runs/{run_id}/artifacts | Artifact 列表 |
| POST | /runs/{run_id}:pause | 暂停 |
| POST | /runs/{run_id}:resume | 继续 |
| POST | /runs/{run_id}:cancel | 取消 |
| POST | /runs/{run_id}:retry | 创建 Retry Run |
| POST | /runs/{run_id}/inputs | 提供外部输入 |
| POST | /approvals/{approval_id}:resolve | 处理审批 |
| GET | /commands/{command_id} | 查询控制命令交付结果 |

GET /runs/{run_id} 必须返回 snapshotSeq。控制 POST 统一返回 202 CommandHandle；202 仅表示命令已耐久接收，不表示 Workflow 已应用。Run 页面保持“命令处理中”，直到 command APPLIED/REJECTED 事件或查询结果到达，不做终态乐观更新。

~~~json
{
  "commandId": "019...",
  "runId": "019...",
  "commandSeq": 4,
  "type": "pause",
  "status": "ACCEPTED",
  "statusUrl": "/v1/commands/019..."
}
~~~

### 13.4 查询与治理 API

| 方法 | 路径 | Scope | 说明 |
|---|---|---|---|
| GET | /projects/{project_id}/runs | swarm.run.read | Run 分页；支持 status、strategyVersionId、createdFrom/To、q |
| GET | /runs/{run_id}/tasks/{task_id} | swarm.run.read | TaskInstance 详情 |
| GET | /tasks/{task_id}/attempts | swarm.run.read | Attempt 分页及错误摘要 |
| GET | /runs/{run_id}/messages | swarm.run.content.read | 脱敏 Message 分页 |
| GET | /runs/{run_id}/logs | swarm.run.logs.read | Loki Gateway 分页代理，不返回 Secret |
| GET | /runs/{run_id}/metrics | swarm.run.read | 成本、Token、时延的聚合 DTO |
| GET | /projects/{project_id}/approvals | swarm.approval.read | 支持 pendingOnly、risk、assignee、expiresBefore |
| GET | /projects/{project_id}/agents | swarm.registry.read | AgentDefinition 分页/版本 |
| GET | /projects/{project_id}/tools | swarm.registry.read | ToolDefinition/MCP 分页/风险 |
| GET | /projects/{project_id}/models | swarm.registry.read | 逻辑模型与可用能力，不返回凭据 |
| GET | /projects/{project_id}/artifacts | swarm.artifact.read | 元数据分页；支持 runId、kind、sensitivity |
| POST | /artifacts/{artifact_id}:download | swarm.artifact.read | OPA 后返回 5 min 单次下载引用 |
| GET | /projects/{project_id}/audit-logs | swarm.audit.read | 只读审计分页/导出 Job |
| GET/PATCH | /projects/{project_id}/settings | swarm.project.admin | ETag/If-Match 项目设置 |
| GET/POST | /projects/{project_id}/webhooks | swarm.webhook.admin | 查询/注册 WebhookRef |
| PATCH/DELETE | /webhooks/{webhook_id} | swarm.webhook.admin | 轮换、禁用或删除 Endpoint |
| GET | /projects/{project_id}/policy | swarm.policy.read | 当前 Bundle Revision、能力和 emergency deny |
| GET | /projects/{project_id}/capabilities | swarm.project.read | Agent、Tool、Model、节点类型和调用方可用能力清单 |

RunSnapshot 至少包含 run、snapshotSeq、earliestAvailableSeq、projectionUpdatedAt、stale、taskCounts、usage、pendingWaits、allowedActions 和链接。allowedActions 由当前身份 + OPA + Run 状态计算，前端不自行推导权限。列表页 v1 使用 5 s 可见/30 s 后台轮询，不为每行创建 SSE；只有 Run Detail 建立 per-Run stream。

上述分页响应统一为 items、nextCursor 和可选 totalEstimate。未获得对应 capability 的路由从导航隐藏，但服务端仍必须独立鉴权。

### 13.5 创建 Run

请求：

~~~json
{
  "strategyVersionId": "019...",
  "input": {
    "topic": "..."
  },
  "overrides": {
    "budget": {
      "maxCostUsd": 10
    }
  },
  "callback": {
    "webhookRef": "webhook://default"
  },
  "metadata": {
    "externalOrderId": "..."
  }
}
~~~

也可以使用 inlineStrategy，但服务端会将其保存为 ephemeral StrategyVersion。

响应：

~~~json
{
  "runId": "019...",
  "status": "ACCEPTED",
  "snapshotSeq": 0,
  "statusUrl": "/v1/runs/019...",
  "eventsUrl": "/v1/runs/019.../events",
  "createdAt": "2026-07-15T10:20:30Z"
}
~~~

返回 202 表示系统已耐久接受请求，不表示 Temporal 已经开始执行。

RunHandle 增加 snapshotSeq，初始值通常为 0。查询快照的 ETag 由 run.version 和 snapshotSeq 生成。

### 13.6 最终结果契约

GET /runs/{run_id}/result 返回：

~~~json
{
  "runId": "019...",
  "status": "SUCCEEDED",
  "completionQuality": "COMPLETE",
  "outputSchemaVersion": "result.v1",
  "output": {"summary": "..."},
  "artifacts": [{"artifactId": "019...", "sha256": "...", "mimeType": "text/markdown"}],
  "tasksSummary": {"total": 8, "succeeded": 8, "failed": 0, "skipped": 0},
  "usage": {"inputTokens": 1200, "outputTokens": 430, "costUsd": 0.18},
  "warnings": [],
  "unresolvedEffects": [],
  "error": null,
  "provenance": {
    "strategyVersionId": "019...",
    "planHash": "sha256:...",
    "runtimeVersion": "1.0.0",
    "policyRevision": "sha256:..."
  }
}
~~~

output 只有在 JSON 编码后不超过 256 KiB 时内联，否则为 null，并在 artifacts 中返回 kind=result 的 ArtifactRef。FAILED、CANCELLED 和 TIMED_OUT 也返回同一信封，error 使用稳定 code，保留已完成 Task 和 Artifact；非终态返回 RUN_NOT_TERMINAL。

### 13.7 错误码

| code | HTTP | 说明 |
|---|---|---|
| SPEC_SCHEMA_INVALID | 422 | JSON Schema 失败 |
| SPEC_SEMANTIC_INVALID | 422 | 图或引用不合法 |
| POLICY_DENIED | 403 | OPA 拒绝 |
| RESOURCE_NOT_FOUND | 404 | 资源不存在或不可见 |
| IDEMPOTENCY_CONFLICT | 409 | 相同 Key 不同请求 |
| INVALID_STATE_TRANSITION | 409 | 当前状态不允许操作 |
| VERSION_CONFLICT | 412 | If-Match/version 不匹配 |
| RUN_NOT_TERMINAL | 409 | Run 尚未产生终态结果 |
| CURSOR_EXPIRED | 410 | SSE/Event 历史游标已超出保留窗口 |
| BUDGET_EXCEEDED | 409 | 提交预算超过策略 |
| RATE_LIMITED | 429 | 配额或速率限制 |
| PROVIDER_UNAVAILABLE | 503 | 外部依赖不可用 |
| INTERNAL_ERROR | 500 | 未分类内部错误 |

错误 response 遵循 Problem Details，必须包含 type、title、status、detail、instance、code、traceId 和可选 errors 数组，不向调用方返回堆栈。

POST /runs/{run_id}/inputs 必须包含 waitingRequestId、inputSchemaVersion、value 和 Idempotency-Key，并以 If-Match 绑定 Run Version；迟到、重复或指向新等待节点的输入由 Workflow 拒绝。

### 13.8 SSE

请求：

GET /v1/runs/{run_id}/events?after=41

after 是客户端最后成功应用的 event_seq，优先级高于 Last-Event-ID。服务端行为：

1. 完成资源级 Auth/OPA 和字段脱敏后，先建立 NATS 临时订阅并缓冲该 Run 的实时事件。
2. 在 PostgreSQL 读取当前 snapshotSeq，并发送 (after, snapshotSeq] 的 durable event。
3. 将缓冲中 seq 大于 snapshotSeq 的事件排序、去重后发送，再进入实时模式。
4. 发现 NATS seq gap 时，从 PostgreSQL Event History 补齐，不能推测缺失事件。
5. 每 15 秒发送 ping comment；所有 Event 信封都包含 schemaVersion，Run 快照单独包含 snapshotSeq。
6. 服务端待发送缓冲超过 1 MiB 时，尽力发送 stream.backpressure（含 lastDeliveredSeq）后关闭；客户端从 lastAppliedSeq 重连。
7. after 小于最早保留 seq 时，在建流前返回 410 CURSOR_EXPIRED，并给出 minAvailableSeq 和 snapshotUrl；客户端必须重新获取快照。

SSE 的 id 字段等于 event_seq，event 字段等于事件 type，data 字段是事件信封 JSON。

GET /event-history?after={seq}&limit={n} 返回 application/json 分页历史，用于 gap 修复、审计和测试。前端使用 fetch + ReadableStream 解析 SSE，以支持 Bearer Header、Cookie/CSRF 会话、AbortController 和明确错误码；不使用原生 EventSource。

### 13.9 Webhook

- Webhook 只接收 durable event。
- 只允许引用预注册 webhookRef；Endpoint 必须为 HTTPS，注册时和每次连接时都校验 DNS、实际 IP、Redirect，拒绝私网、Link-local、Metadata 和非白名单端口。
- 签名为 v1=hex(HMAC-SHA256(secret, timestamp + "." + rawBody))；Header 包含 Swarm-Delivery-Id、Swarm-Event-Id、Swarm-Key-Id、Swarm-Signature、Swarm-Timestamp。
- 接收方校验 5 min 重放窗口和 delivery_id 去重；Key 轮换期间 current/previous 双 Key 最多并存 24 h，Secret 值只在 Vault。
- Payload 在发送前逐 Endpoint 执行 OPA 和字段脱敏，响应体最多读取 64 KiB 且不得写入普通日志。
- 默认重试 8 次：10 s、30 s、1 min、5 min、15 min、1 h、6 h、24 h。
- 2xx 为成功；409 只有在 Problem code=DELIVERY_ALREADY_PROCESSED 时视为成功，其他状态重试。
- Endpoint 连续失败进入 disabled，产生治理告警。

### 13.10 配置文件与 CLI

GitOps/本地配置采用与 REST 相同的 SwarmSpec YAML/JSON，不建立第二套执行语义：

~~~text
swarmcore/
  project.yaml
  agents/*.yaml
  tools/*.yaml
  strategies/*.yaml
  models/*.yaml
~~~

官方 CLI 为 swarmctl：

- swarmctl validate -f：本地 JSON Schema 校验，再可选调用服务端语义校验。
- swarmctl compile -f：调用同一 Compiler API，输出 plan_hash 和诊断。
- swarmctl apply -f：按 metadata.uid、resourceVersion 和内容 SHA-256 幂等创建资源/版本。
- swarmctl run -f strategy.yaml --input input.json：调用 Run API 并输出 RunHandle；--follow 使用同一 SSE 契约。

CI/GitOps 使用最小权限 Service Account 和短期 Bearer Token。服务启动时不扫描目录并直接执行配置；所有配置必须经过 Registry、版本化、OPA 和审计链路。

## 14. MCP、A2A 和 AG-UI

### 14.1 MCP Server

MCP Server 是面向 DeepTalk 等智能体调用方的可选入站适配器，用于能力发现、自主生成方案、提交执行和读取结果。REST API 保持等价且完整的接入能力；MCP Tool/Resource 只映射统一应用服务与稳定 DTO，不维护独立业务状态或执行语义。

生产端固定 MCP 稳定协议 2025-11-25、JSON-RPC 2.0 与 Streamable HTTP，单端点为 POST/GET/DELETE /mcp。客户端通过初始化协商协议版本，后续携带 Mcp-Protocol-Version 和 Mcp-Session-Id。远程访问使用 OAuth 2.0 Bearer Token；stdio 只用于本地开发，不暴露为生产入口。截至本文档日期，2026-07-28 版本仍是 RC，不进入 v1 生产基线；最终发布并得到 SDK 支持后通过 Contract Test 升级。

Tools：

- swarm_get_capabilities
- swarm_validate_strategy
- swarm_compile_strategy
- swarm_create_run
- swarm_get_run
- swarm_get_run_result
- swarm_list_run_tasks
- swarm_pause_run
- swarm_resume_run
- swarm_cancel_run
- swarm_resolve_approval
- swarm_retry_run

| Tool 组 | 必填输入 | outputSchema |
|---|---|---|
| get_capabilities | projectId | CapabilityCatalog |
| validate/compile | projectId、spec、specSchemaVersion | ValidationResult / CompileResult |
| create_run | projectId、strategyVersionId 或 inlineStrategy、input、idempotencyKey | RunHandle |
| get_run/list_tasks | runId、可选 cursor/limit | RunSnapshot / TaskPage |
| get_run_result | runId | RunResult；非终态返回 RUN_NOT_TERMINAL |
| pause/resume/cancel | runId、expectedVersion、idempotencyKey | CommandHandle |
| resolve_approval | approvalId、decision、approvalVersion、idempotencyKey | CommandHandle |
| retry_run | runId、可选 retryFromTaskId、idempotencyKey | RunHandle |

Resources：

- swarm://runs/{run_id}
- swarm://runs/{run_id}/result
- swarm://runs/{run_id}/events?after={seq}&limit={limit}
- swarm://runs/{run_id}/artifacts/{artifact_id}（仅元数据和受控下载引用）
- swarm://strategies/{strategy_id}/versions/{version}

MCP 创建任务默认异步返回 RunHandle。同步等待参数 wait_seconds 最大 30 秒，超时后仍返回 RunHandle，不取消 Run。

每个 Tool 使用 JSON Schema 2020-12 inputSchema/outputSchema，并返回 structuredContent。所有变更型 Tool 的输入必须显式包含 projectId 和 idempotencyKey，不能依赖 MCP Host 能否透传 HTTP Header。鉴权 Scope 与 REST 一一对应，例如 swarm.run.create、swarm.run.control、swarm.approval.resolve；Tool 错误使用 isError=true，并在 structuredContent 中返回与 REST 相同的稳定 code、detail 和 traceId。

Resource 只返回调用方可见且已脱敏的快照/分页内容，不把 NATS 或数据库连接暴露给 Host。MCP Session 不是 Run 生命周期；Session 结束不取消已创建 Run。

### 14.2 A2A

A2A 仅用于把外部独立 Agent 作为 RemoteAgent 接入。内部 Worker 之间不使用 A2A，避免引入额外序列化和状态语义。v1 Adapter 固定 A2A 1.0 的 HTTP+JSON binding，并发送 A2A-Version: 1.0；其他 binding 必须作为独立 Adapter 实现。

RemoteAgent 必须注册：

- Agent Card 与能力。
- 身份和 Endpoint。
- 输入输出 Schema。
- 超时、重试和数据等级。
- 是否支持取消、流式和 Artifact。

所有出站调用经过 A2A Egress Gateway：

- 发布 RemoteAgentDefinition 时获取公开/扩展 Agent Card，校验 JWS、RFC 8785 canonical form、HTTPS Endpoint、协议版本和能力，并固定 card_hash；Hash 改变必须重新审批发布。
- 凭据仅支持 OAuth 2.0 Client Credentials 或 mTLS，来自 SecretProvider；RemoteAgent 不获得 SwarmCore JWT、Vault 或数据库凭据。
- 每次调用执行 OPA、数据等级、域名/IP、DNS Rebinding、Redirect、大小、MIME、超时和预算检查。
- Attempt external_idempotency_key 映射为稳定 A2A Message ID；保存 remote taskId、contextId 和 card_hash。远端未声明幂等能力时，超时归类 TOOL_SIDE_EFFECT_UNKNOWN，不盲目重发。
- SendMessage/SendStreamingMessage 映射 execute_agent；Task 状态/Artifact Update 映射 Attempt Event；输入请求映射 WAITING_INPUT；Cancel 映射 CancelTask。
- 流断开后先 GetTask 对账，再 SubscribeToTask；所有远端更新按 remote taskId + update identity 幂等。Artifact 只能经 Gateway 拉取、扫描、计算 SHA-256 后进入本地 S3。

### 14.3 AG-UI

DeepTalk 负责面向终端用户的对话与交互，SwarmCore 不以 AG-UI 作为主要产品入口。AG-UI 仅作为可选测试适配器，供控制台验证交互式 Agent 节点的消息、Tool Call 和前端状态；运行拓扑、Task 状态、Attempt、成本、审批和治理事件继续使用 Swarm Event API。

前端必须把 AG-UI Message State 与 Run Projection 分开，不能用聊天消息推导 Run 状态。

交互端点固定为 POST /v1/runs/{run_id}/agent-sessions/{agent_instance_id}/ag-ui，响应为 text/event-stream；认证、OPA、字段脱敏和背压规则与 Run SSE 相同。threadId 使用持久 Agent Session ID，runId 使用 Swarm Run ID。允许的标准事件为 RUN_*、STEP_*、TEXT_MESSAGE_*、TOOL_CALL_*、STATE_SNAPSHOT、STATE_DELTA 和 MESSAGES_SNAPSHOT；平台治理信息只能使用带 swarm. 命名空间的 CUSTOM Event。

用户消息、Tool Approval 和前端状态写入都先转为带 idempotencyKey 的 RunCommand；AG-UI 连接关闭不取消 Run。每个持久交互事件附加 swarmEventSeq 扩展；重连先取 MESSAGES_SNAPSHOT/STATE_SNAPSHOT，再用 Run Event History 补齐。AG-UI 适配器版本与事件 Schema 写入 Run provenance，升级必须通过录制流 Contract Test。

## 15. Agent Runtime Adapter

### 15.1 接口

~~~python
class AgentRuntimeAdapter(Protocol):
    name: str

    async def validate(self, spec: AgentSpec) -> list[Diagnostic]: ...

    async def instantiate(
        self,
        spec: AgentSpec,
        context: AgentExecutionContext,
    ) -> AgentHandle: ...

    async def execute(
        self,
        handle: AgentHandle,
        request: AgentRequest,
        emit: EventEmitter,
    ) -> AgentResult: ...

    async def cancel(self, handle: AgentHandle) -> None: ...

    async def dispose(self, handle: AgentHandle) -> None: ...
~~~

v1 只实现 AgnoAdapter。LangGraph、Microsoft Agent Framework、CrewAI 和 PydanticAI 作为后续独立 Adapter，不允许直接访问 SwarmCore 数据表或 Temporal Client。

### 15.2 Agno 映射

| SwarmCore | Agno |
|---|---|
| AgentSpec | Agent |
| TeamSpec | Team |
| model_ref | Agno Model / LiteLLM endpoint |
| tool_ref | Toolkit / Function / MCP Tool |
| knowledge_ref | Knowledge |
| session_ref | Session |
| AgentResult | RunOutput / TeamRunOutput 规范化 |
| ApprovalRequirement | HITL Requirement |

Agno 自身的 Session 和 Checkpoint 可以作为 Agent 内部能力，但不能代替 SwarmCore Run/Task/Attempt。

## 16. 模型与工具治理

### 16.1 模型逻辑名

Spec 只能引用逻辑名，例如：

- model://general
- model://research
- model://reasoning
- model://local-private

逻辑名由 LiteLLM 和 Model Registry 映射到实际 Provider。映射包含：

- Provider 和模型。
- 数据区域。
- 支持能力。
- 最大 Context。
- 单价。
- RPM/TPM。
- Fallback Chain。
- 允许的数据等级。

运行时记录逻辑名、解析后的实际模型、Provider、参数、模型版本和价格版本。

### 16.2 预算

预算检查发生在：

1. Run 提交。
2. 节点调度前。
3. 每次模型调用前。
4. 模型 usage 返回后。
5. 动态 spawn 前。

达到 80% 产生 budget.warning。达到 100% 停止调度新节点，并按 Strategy 配置选择 fail、partial_result 或 wait_for_budget_approval。

### 16.3 Tool 风险

| 风险 | 示例 | 默认动作 |
|---|---|---|
| LOW | 只读搜索、查询 | 自动允许 |
| MEDIUM | 内部写操作 | OPA + 审计 |
| HIGH | 对外消息、删除、支付 | 人工审批 |
| CRITICAL | 任意代码、基础设施管理 | 沙箱 + 管理员审批 |

## 17. 安全设计

### 17.1 身份与角色

JWT 必须包含 sub、tenant_id、project scopes、roles、issuer 和 audience。

JWT 只接受配置白名单中的非对称 alg，严格校验 iss、aud、exp、nbf 和 JWKS kid；JWKS 按 Cache-Control 缓存并支持轮换，未知 kid 触发一次受限刷新。控制台 Session 保存于服务端 Session Store，登录和提权时轮换 Session ID，登出/管理员撤销后立即失效；CORS 只允许控制台 Origin，配置 CSP、frame-ancestors 和 Referrer-Policy。

Run 固定保存 initiated_by、submitted_scopes、auth_context_hash 和 policy revision，不保存用户 JWT。API、Dispatcher、Worker、Gateway 使用 workload identity + mTLS，执行时换取 audience/scope 受限的短期内部 Capability Token，不能沿用已过期用户凭据。

内置角色：

| 角色 | 权限 |
|---|---|
| tenant_admin | 租户级治理、用户和策略 |
| project_admin | 项目资源和预算 |
| strategy_author | 创建、编译和发布 Strategy |
| run_operator | 提交、暂停、继续、取消和重试 |
| approver | 处理符合 Scope 的审批 |
| auditor | 只读 Run、Trace 和 Audit |
| viewer | 只读非敏感运行数据 |

### 17.2 OPA

API、Scheduler、Agent Worker、Tool Gateway、Artifact Gateway、Event Gateway、Webhook Delivery Worker 和 A2A Egress Gateway 都是 Policy Enforcement Point。

OPA 输入示例：

~~~json
{
  "subject": {
    "id": "user-1",
    "tenantId": "tenant-1",
    "roles": ["run_operator"]
  },
  "action": "tool.execute",
  "resource": {
    "tool": "tool://send-email",
    "risk": "HIGH",
    "projectId": "project-1"
  },
  "context": {
    "runId": "run-1",
    "dataClassification": "internal",
    "costUsedUsd": 2.1
  }
}
~~~

OPA 返回：

~~~json
{
  "allow": true,
  "obligations": {
    "requireApproval": true,
    "allowedEgress": ["api.example.com:443"],
    "maxDurationSeconds": 60,
    "redactFields": ["recipientToken"]
  },
  "policyRevision": "sha256:..."
}
~~~

每个 Run 固定记录 Policy Revision。Policy Decision Log 必须脱敏。

编译时 Policy Revision 用于复现，但不是长期授权快照。每次模型、Tool、Artifact、A2A、Secret 和高风险数据访问都使用当前 Runtime Policy，并叠加不可绕过的 emergency deny/kill-switch；记录实际 decision revision。OPA 不可用、返回未知 obligation 或 obligation 无法执行时 fail closed，只有显式列出的 LOW 风险只读健康检查可采用本地短 TTL allow cache。

Tool Approval 必须绑定 tool_version、canonical_input_hash、attempt/task_execution、policy_revision 和 expires_at，只允许消费一次；参数变化必须重新审批。CRITICAL 操作禁止申请者自批，并要求 maker-checker 两个不同主体。Workflow Timer 是过期权威。

### 17.3 Secret

- Spec、Event、Trace、Prompt 和数据库中只允许 secret_ref。
- Worker 使用 Kubernetes ServiceAccount 向 Vault 认证。
- Secret 在 Activity 开始时获取，使用短 Lease。
- Activity 完成、取消或超时后撤销。
- Secret 默认通过内存或 ramfs 文件注入。
- 日志、异常、模型上下文和 Artifact 上传前执行 Secret Scanner。
- 平台 Root Token、云 Admin Key 和共享数据库密码禁止进入 Agent Worker。

### 17.4 多租户

- API 依据 JWT tenant_id 过滤。
- PostgreSQL 启用 RLS。
- S3 使用租户前缀和独立加密上下文。
- NATS Consumer 按租户授权。
- Trace 带 tenant_id，但不把 tenant_id 作为 Prometheus 高基数 Label。
- 沙箱使用独立 Namespace 或受控 Namespace + NetworkPolicy。

### 17.5 网络

- 控制面默认不能访问公网，只能访问 IdP、Temporal、PostgreSQL、NATS、Vault 和 OTel Collector。
- Tool Worker 通过 Egress Gateway 出网。
- Sandbox 默认无网络。
- 禁止访问 Link-local、Metadata Service、集群 Service CIDR 和 RFC1918，除非显式批准。
- DNS 解析结果和实际连接 IP 都要校验，防止 DNS Rebinding。

## 18. 可观测性

### 18.1 Trace

Trace 层级：

~~~text
swarm.run
  swarm.task
    swarm.attempt
      agent.invoke
        llm.request
        tool.call
        retrieval.query
      sandbox.job
~~~

必备 Span Attribute：

- tenant.id
- project.id
- swarm.run.id
- swarm.task.id
- swarm.attempt.id
- swarm.strategy.version
- agent.definition
- model.logical_name
- model.provider
- tool.name
- retry.attempt
- budget.cost_usd
- token.input
- token.output

Prompt、模型输出和 Tool 参数默认不作为普通 Attribute；需要采样保存时进入受控 Event/Artifact，并遵守数据等级。

### 18.2 Metrics

核心指标：

- swarm_runs_total{status,strategy}
- swarm_active_runs
- swarm_run_duration_seconds
- swarm_task_duration_seconds{node_type}
- swarm_activity_retries_total{category}
- swarm_queue_schedule_latency_seconds{queue}
- swarm_model_requests_total{provider,model,status}
- swarm_model_tokens_total{provider,model,direction}
- swarm_model_cost_usd_total{provider,model}
- swarm_tool_calls_total{tool,status}
- swarm_policy_denied_total{action}
- swarm_approval_wait_seconds
- swarm_sse_connections
- swarm_event_projection_lag_seconds
- swarm_outbox_pending
- swarm_webhook_delivery_total{status}

禁止把 run_id、task_id、user_id 或原始 tool 参数作为 Prometheus Label。

### 18.3 Logs

所有日志为 JSON，包含 timestamp、level、service、trace_id、run_id、task_id、event、message。敏感字段在结构化 Logger 层统一脱敏。

### 18.4 Audit

以下操作必须审计：

- Strategy 创建、发布、弃用。
- Run 创建、暂停、继续、取消、重试。
- Approval 决策。
- Secret/Artifact 访问。
- Tool 和 Sandbox 执行。
- Policy Deny。
- 角色、预算和连接配置变更。

## 19. 测试与观测控制台设计

控制台是供开发和测试人员人工验证 SwarmCore 的参考客户端，核心用途是编辑或导入方案、发起测试运行、观察执行过程和诊断问题。控制台只使用公开 REST API、SSE 和可选 AG-UI，不直连内部组件；它不得实现 DeepTalk 的目标理解、自动编排或终端用户产品逻辑，也不得复制服务端编译、权限和状态迁移规则。生产部署可按需要关闭控制台，不影响 API、MCP 和执行运行时。

### 19.1 固定技术栈

- React 19 + TypeScript + Vite。
- React Router v7 Data Mode。
- shadcn/ui Radix 版本，不使用 Base UI。
- Tailwind CSS v4 @theme。
- cn() + class-variance-authority。
- TanStack Query v5。
- Zustand 5。
- React Hook Form + Zod。
- React Flow 12。
- TanStack Table + TanStack Virtual。
- Monaco Editor + Ajv 2020 + yaml。
- ApexCharts，生产发布前完成许可证确认。
- Vitest、Testing Library、MSW、Playwright。
- openapi-typescript + openapi-fetch；类型和客户端只从 OpenAPI 3.1 生成。

### 19.2 路由

| 路由 | 页面模式 | 功能 |
|---|---|---|
| /t/:tenantId/p/:projectId/overview | Dashboard | 测试 Run、成本、成功率、队列和告警 |
| /t/:tenantId/p/:projectId/strategies | Table List | 策略列表、状态和版本 |
| /t/:tenantId/p/:projectId/strategies/new | Form Flow | 创建策略 |
| /t/:tenantId/p/:projectId/strategies/:strategyId | Detail Page | 版本、用量和审计 |
| /t/:tenantId/p/:projectId/strategies/:strategyId/drafts/:draftId/editor | Three-Column Workspace | 明确 Draft 身份、节点面板、画布、属性面板 |
| /t/:tenantId/p/:projectId/runs | Master-Detail Ops | 实时 Run 列表和摘要 |
| /t/:tenantId/p/:projectId/runs/:runId | Detail Page | 拓扑、时间线、日志、消息、Artifact、成本 |
| /t/:tenantId/p/:projectId/approvals | Master-Detail Ops | 待审批列表和风险详情 |
| /t/:tenantId/p/:projectId/agents | Table List | Agent Registry |
| /t/:tenantId/p/:projectId/tools | Table List | Tool/MCP Registry |
| /t/:tenantId/p/:projectId/models | Table List | 模型逻辑名和 Provider |
| /t/:tenantId/p/:projectId/artifacts | Table List | Artifact 查询和保留 |
| /t/:tenantId/p/:projectId/audit | Table List | 审计日志 |
| /t/:tenantId/p/:projectId/settings/* | Hub Tabs | 项目、预算、Webhook、Policy |
| /auth/callback | Auth Callback | OIDC Code + PKCE 回调 |
| /403、/404 | Error Page | 无权访问和资源不存在 |

所有 Loader、Action、Query Key 和 Mutation 必须包含 tenantId + projectId；路由 Scope 与登录 Claim 不匹配时返回 404。切换 Tenant 时先取消请求、关闭 SSE/AG-UI、清除 Query Cache 和 Zustand 项目 Store，再进入新 Scope。

React Router 使用 RootRoute > AuthBoundary > AppLayout > ProjectLayout > Page 的嵌套路由与 Outlet；Loader 通过 queryClient.ensureQueryData 预取，Action 复用 Query Mutation。导航和按钮由服务端 capabilities/allowedActions 控制。

### 19.3 页面壳

- 展开侧栏宽 290 px，收起 90 px。
- 顶栏 sticky。
- 主内容最大宽度使用 --breakpoint-2xl。
- 桌面策略编辑器使用三栏；tablet 将属性栏改为 Sheet；mobile 为只读图 + 分步表单。
- Dialog、Sheet、Dropdown、Popover、Tooltip 和 Tabs 必须使用 Radix/shadcn。
- 所有颜色使用 brand、gray、success、warning、error 等语义 Token。
- 支持 light、dark、keyboard、focus-visible、disabled、loading、empty、error、selected 和 responsive。

### 19.4 状态所有权

| 状态 | 所有者 |
|---|---|
| Run/Task/Approval 服务端快照 | TanStack Query |
| SSE 已应用 seq 和连接状态 | RunEventStore |
| 未完成 CommandHandle | TanStack Query + Command Mutation State |
| 策略画布 nodes/edges/selection | Zustand Editor Store |
| 未提交表单 | React Hook Form |
| URL Filter/Tab/Pagination | React Router Search Params |
| Theme/Sidebar | Design System Context |
| 聊天消息 | AG-UI Client State |

禁止把服务端 Run 快照长期复制到 Zustand。每个 Run 快照都带 snapshotSeq；SSE 从该 seq 开始，Reducer 更新 TanStack Query Cache，并以 event_seq 保证幂等。Refetch 返回 seq=S 时，如果 lastAppliedSeq>S，先把 (S,lastAppliedSeq] 历史事件重放到新快照后再替换 Cache，禁止旧快照覆盖实时状态。

Reducer 只 patch 已存在且字段完整的目标 Query；目标缺失或 Event Schema 版本不支持时 invalidate/refetch，不能用单个事件拼出残缺 DTO。RunEventStore 按 runId 引用计数复用连接，最后一个订阅者卸载后关闭；pending replay 上限 4 MiB，并将 backpressure、replaying、stale 状态暴露到页面。

### 19.5 Strategy Editor

三栏：

1. 左栏：Agent、Tool、Control Flow、Approval、Reducer 节点库。
2. 中栏：React Flow 画布、Minimap、缩放、自动布局、错误标记。
3. 右栏：所选节点的 RHF + Zod 属性表单。

能力：

- 拖拽创建和连线。
- 连接端口类型检查。
- Undo/Redo。
- 自动保存 Draft。
- Visual / YAML 双视图。
- 实时本地 Ajv 校验。
- 服务端 validate/compile。
- 变更 Diff。
- Dry Run。
- Publish 前确认 Dialog。

Visual 与 YAML 共享同一 canonical Spec。切换视图失败时保留原文本并显示诊断，不能静默丢弃用户输入。

编辑器唯一可保存真相源是 DraftDocument 的最后合法 typed AST：React Flow 和 RHF 只生成 typed patch；Monaco 维护独立 text buffer，只有 parse/validate 成功才提交 AST。Undo/Redo 操作 AST patch history。自动保存 debounce 800 ms、同一 Draft 串行、携带 ETag/If-Match，并显示 dirty、saving、saved、conflict、offline；412 提供 reload、diff、merge，不做 last-write-wins。

### 19.6 Run Detail

页面包含：

- 状态 Header 和主要控制操作。
- 控制操作显示 CommandHandle 的 pending/applied/rejected 状态；Command 未 APPLIED 前不把 Run 乐观标为 PAUSED/CANCELLED。
- React Flow 只读执行图。
- 节点颜色来自状态语义 Token。
- 节点详情 Drawer：输入、输出、Attempt、模型、工具、成本、错误。
- 虚拟化 Timeline。
- Log Stream。
- Agent Message 和 Handoff。
- Artifact Table。
- Approval Timeline。
- Metrics Charts。

流事件到达时只更新受影响节点，不重新布局整个图。用户手动调整的视口必须保留。

### 19.7 SSE 客户端

状态机：

CONNECTING、OPEN、RECONNECTING、STALE、CLOSED、ERROR。

规则：

- 保存 lastAppliedSeq。
- 指数退避 1、2、5、10、30 秒并加 jitter。
- 使用 fetch + ReadableStream，重连携带 after=lastAppliedSeq；机器客户端可同时携带 Last-Event-ID。
- 收到重复 seq 时忽略。
- 发现 seq gap 时暂停实时应用，调用历史 API 补齐。
- 收到 410 CURSOR_EXPIRED 时清空该 Run 的事件 Reducer，重新获取带 snapshotSeq 的快照后建流。
- 后台 Tab 可以批量合并 content.delta。
- 页面卸载后释放连接。
- 连接失败不清空已有数据。

浏览器不保存 Access/Refresh Token；请求使用同源 HttpOnly Session Cookie，写请求由 API Client 自动附加 X-CSRF-Token。401 只触发一次同源会话刷新，失败后跳转登录，禁止多个 Query 并发刷新形成风暴。

Agent Message、Tool 输出和 Markdown 均是不可信内容：禁止 raw HTML，Markdown 使用 allowlist sanitizer，URL 只允许 https/mailto 等批准 scheme，外链强制 noopener noreferrer。HTML/SVG/PDF 预览放在独立 Origin 的 sandbox iframe，敏感 Artifact 默认只下载；启用严格 CSP，并对消息、Artifact 名称、Tool 参数和 AG-UI Event 做 XSS 测试。浏览器端 Tool 默认仅展示；只有显式 client-tool 白名单且 OPA 允许时才执行，Pause/Cancel/Approval 始终调用 REST Command API。

### 19.8 前端质量门禁

- TypeScript strict。
- ESLint 无新增 error。
- Vitest 覆盖 Reducer、表单、权限和错误态。
- MSW 覆盖正常、loading、empty、error、partial、stale 和 retry。
- Playwright 覆盖核心业务流。
- desktop、tablet、mobile 的 light/dark 截图验收。
- 策略画布、Run 图、表格、Dialog、Sheet 和 Dropdown 不得裁切或溢出。
- 新组件遵循设计系统组件索引、Token、Radix 和兼容规则。
- Tailwind v4 使用 @theme 和 @custom-variant dark；业务代码禁止硬编码 hex/rgb。
- Radix 浮层统一 z-99999；标准表单控件 h-11 rounded-lg，焦点态 focus-visible:ring-3；根级挂载 TooltipProvider。
- 所有视觉变体使用 cva，类名组合只使用 cn()；禁止 Base UI 和手写 Modal/Popover/Dropdown。
- 截图矩阵必须检查大面积空白、内容列过窄、裁切、重叠、framing 和对比度，而不仅是像素 Diff。
- 专测 SSE reconnect/backpressure/gap/410、partial/retry/stale、Command pending/rejected、Draft conflict/merge/offline。
- 新组件同步 .agent/skills/b-design-system-tailadmin-radix 的 component-index 和可运行 examples。
- CI 执行 tsc --noEmit、ESLint、Vitest、Playwright、设计系统校验脚本，以及硬编码颜色和手写浮层静态扫描。

## 20. 部署设计

### 20.1 生产拓扑

~~~mermaid
flowchart TB
    LB[Ingress / Load Balancer]
    API1[API x3]
    Event1[Event Gateway x2]
    Dispatcher[Outbox Dispatcher x2]
    EventPublisher[Event Outbox Publisher x2]
    WebhookScheduler[Webhook Scheduler x2]
    CW[Control Worker x2]
    AW[Agent Worker autoscale]
    TW[Tool Worker autoscale]
    WW[Webhook Worker x2]
    SW[Sandbox Manager x2]
    Ingestor[Runtime Event Ingestor x2]
    Projector[State Projector x2]
    ArtifactGateway[Artifact Gateway x2]
    OTel[OTel Collector x2]
    Temporal[Temporal HA / Cloud]
    PG[(Managed PostgreSQL)]
    NATS[NATS JetStream x3]
    Vault[Vault HA]
    OPA[OPA x2]
    LiteLLM[LiteLLM Proxy]
    S3[(S3)]
    Phoenix[Phoenix]
    Prom[Prometheus / Grafana / Loki]

    LB --> API1
    LB --> Event1
    API1 --> PG
    Dispatcher --> PG
    Dispatcher --> Temporal
    EventPublisher --> PG
    EventPublisher --> NATS
    Temporal --> CW
    Temporal --> AW
    Temporal --> TW
    Temporal --> WW
    Temporal --> SW
    AW --> Vault
    AW --> LiteLLM
    TW --> Vault
    SW --> Vault
    AW --> Ingestor
    TW --> Ingestor
    Ingestor --> PG
    CW --> Projector
    Projector --> PG
    AW --> ArtifactGateway
    TW --> ArtifactGateway
    ArtifactGateway --> S3
    NATS --> Event1
    NATS --> WebhookScheduler
    WebhookScheduler --> PG
    Event1 --> PG
    API1 --> OPA
    Event1 --> OPA
    AW --> OPA
    TW --> OPA
    WW --> OPA
    ArtifactGateway --> OPA
    API1 --> OTel
    CW --> OTel
    AW --> OTel
    TW --> OTel
    WW --> OTel
    OTel --> Phoenix
    OTel --> Prom
~~~

### 20.2 Worker Pool

| Pool | 隔离 | 扩缩容信号 |
|---|---|---|
| control | 无公网、低 CPU | Temporal backlog |
| agent-general | Provider 出网 | Queue latency、并发 |
| agent-private | 私网模型 | Queue latency、GPU gateway |
| tool-trusted | Egress Gateway | Queue latency |
| sandbox-control | K8s API 最小权限 | pending jobs |
| artifact | S3 权限 | upload backlog |
| webhook | 外网白名单 | Temporal webhook Task Queue backlog |

### 20.3 本地开发

Docker Compose 包含：

- PostgreSQL。
- Temporal Server + UI。
- NATS JetStream。
- OPA。
- Vault dev mode，仅本地。
- Phoenix。
- API、Command Dispatcher、Event Publisher、Event Gateway、Control Worker、Agent Worker。

ArtifactStore 使用本地文件系统 Adapter。Valkey、Kubernetes Sandbox、Grafana 和 Loki 在默认本地 Profile 中可关闭。

### 20.4 配置

使用 Pydantic Settings。配置来源优先级：

1. 命令行。
2. 环境变量。
3. 挂载配置文件。
4. 代码默认值。

Secret 不写入普通配置文件。所有配置在启动时验证，错误时进程 fail-fast。

### 20.5 高可用和灾备

- API、Event/Artifact Gateway、Command Dispatcher、Event Publisher、Webhook Scheduler、Runtime Ingestor、Projector 和 Worker 至少 2 副本。
- PostgreSQL 启用 PITR 和跨可用区副本。
- NATS 使用 3 节点、3 副本 Stream。
- Temporal 使用 Cloud 或官方 HA 部署。
- S3 开启 Versioning 和 Lifecycle。
- Vault 使用 HA 和 Audit Device。
- 每季度执行恢复演练。

## 21. 性能与背压

参考容量目标：

| 指标 | v1 目标 |
|---|---|
| 同时 Active Run | 1,000 |
| 同时模型调用 | 200 |
| 同时 SSE 连接 | 2,000 |
| durable event 写入 | 2,000/s |
| StrategyVersion | 100,000 |
| 日 Run 提交 | 100,000 |

背压顺序：

1. 租户并发配额。
2. 项目并发配额。
3. Strategy maxParallelism。
4. Temporal Task Queue。
5. Provider RPM/TPM。
6. Tool/Sandbox 容量。

系统不能通过无限创建协程绕过队列。达到容量时保持 QUEUED，并输出 queue position 的估算值。

## 22. 测试策略

### 22.1 单元测试

- SwarmSpec Schema。
- Compiler 纯函数和 canonical hash。
- DAG、循环、Join、动态命令验证。
- 状态迁移。
- Retry 分类。
- OPA 输入与 obligations。
- Event Reducer。
- Adapter 规范化。

### 22.2 属性与回放测试

- 使用 Hypothesis 生成合法/非法图。
- 验证任何合法图都有有界终止条件。
- 验证重复 event 不改变最终投影。
- 验证乱序 NATS Delivery 可由 seq 恢复。
- 对 Temporal 历史执行 Replay Test，阻止不兼容 Workflow 发布。
- 对每个 WorkflowCheckpoint 版本做 Continue-As-New Replay，覆盖动态 Task、未决审批、命令游标和补偿栈。
- 验证同一 effect_id 在 Activity completion 丢失后不重复调用副作用 Tool。

### 22.3 集成测试

- PostgreSQL 事务、RLS、Outbox；覆盖每张多租户表、复合 FK 和连接池 Tenant Context 污染。
- Temporal 重启、Worker 丢失和 Activity Retry。
- 多 Dispatcher 并发下 start/pause/resume/cancel 严格按 command_seq 应用。
- NATS 重投递。
- Vault Lease 撤销。
- S3 staging 和孤儿清理。
- MCP Server/Client。
- REST 与 MCP 对同一 SwarmSpec 的命令规范化、Plan Hash、错误码和 RunResult 契约一致性。
- SSE 先订阅/高水位回放、gap、backpressure、410 和陈旧快照重放。
- Webhook 签名和重试。
- MCP 2025-11-25、A2A 1.0 和 AG-UI 录制流 Contract Test。

### 22.4 故障测试

- 执行中杀死 Agent Worker。
- PostgreSQL 短暂故障。
- Temporal 不可用。
- NATS 不可用。
- Provider 429/500/超时。
- Tool 返回未知副作用。
- Sandbox Node 丢失。
- Event Gateway 慢消费者。
- Run 取消与 Approval 同时发生。
- Projector 提交成功但响应丢失、Event Publisher PubAck 丢失和 Reconciler 修复。

### 22.5 安全测试

- 越租户访问。
- JWT Scope 绕过。
- SSRF、DNS Rebinding 和 Metadata Service。
- Prompt/Tool 输出 Secret 泄露。
- YAML Bomb、重复 Key 和超大 Spec。
- 模板逃逸。
- Sandbox privilege escalation。
- Artifact 路径穿越和 MIME 欺骗。
- RLS 连接复用污染、Webhook/A2A Redirect SSRF、Agent Card Hash 漂移。
- Sandbox Admission 逃逸矩阵、Capability Token 重放和 Egress Proxy DNS Rebinding。
- Markdown/AG-UI/Tool 输出 XSS、CSP 和独立 Origin 预览隔离。

## 23. 仓库结构

~~~text
SwarmCore/
  apps/
    api/
    worker-control/
    worker-agent/
    worker-tool/
    worker-webhook/
    event-publisher/
    event-gateway/
    webhook-scheduler/
    a2a-egress-gateway/
    sandbox-manager/
    swarmctl/
    web/
  packages/
    spec/
    compiler/
    domain/
    persistence/
    runtime-temporal/
    adapter-agno/
    tool-gateway/
    policy/
    observability/
    api-client-ts/
  deployments/
    compose/
    helm/
    policies/
  tests/
    contract/
    integration/
    replay/
    e2e/
  docs/
    swarmcore-system-design.md
    adr/
~~~

现有 agno 目录作为上游源码参考，不直接在其中开发 SwarmCore 业务代码。现有 agent-ui 仅用于参考 AgentOS API 和流式交互，新的测试与观测控制台放入 apps/web。

## 24. 实施阶段

### Phase 1：可执行闭环

- 建立 monorepo 目录和开发环境。
- SwarmSpec v1、Pydantic Schema 和 Compiler。
- Strategy Registry。
- PostgreSQL 核心表、Alembic、RLS 和 Outbox。
- Command Dispatcher、Event Outbox Publisher 和 Projection Reconciler。
- Temporal SwarmRunWorkflow。
- AgnoAdapter 和 Agent Worker。
- 统一应用服务、Run REST API、SSE 和 MCP 入站适配器。
- Run/Task/Event 基础测试与观测控制台。
- OpenTelemetry 和 Phoenix。

验收：DeepTalk 或其他调用方可以通过 REST 或 MCP 提交顺序、并行、DAG 和 Supervisor 方案；两种入口均可恢复、取消并取得一致的结构化结果，关闭控制台不影响上述链路。

### Phase 2：交互和治理

- Approval、Pause/Resume、External Input。
- Tool Gateway 和 MCP Registry。
- LiteLLM Model Registry 和预算。
- OPA 与 Vault。
- Webhook。
- Webhook Scheduler + WebhookDeliveryWorkflow。
- Strategy Visual Editor。
- Replay、Retry From Task 和 Artifact。

验收：高风险 Tool 必须审批，断线可恢复，预算和权限可审计。

### Phase 3：隔离和规模化

- Kubernetes Job + gVisor。
- NATS 3 节点生产化。
- Worker Autoscaling。
- pgvector Knowledge/Memory。
- 多区域 Artifact。
- Chaos、恢复演练和性能压测。

验收：达到本设计容量目标，并通过故障、越权和沙箱测试。

### Phase 4：扩展生态

- A2A RemoteAgent。
- LangGraph/MAF/CrewAI/PydanticAI Adapter。
- Qdrant 可选后端。
- Kafka Audit/Data Export。
- Kata 高风险 Runtime。

## 25. 架构决策记录

| ADR | 决策 |
|---|---|
| ADR-001 | Agno 作为首选 Agent Runtime Adapter |
| ADR-002 | Temporal 作为唯一 Durable Execution Engine |
| ADR-003 | PostgreSQL 作为产品状态事实源 |
| ADR-004 | SwarmSpec 为声明式 JSON Schema 2020-12 协议 |
| ADR-005 | CEL 作为条件表达式，禁止 eval |
| ADR-006 | Transactional Outbox 解决数据库与外部系统一致性 |
| ADR-007 | NATS JetStream 作为生产事件分发 |
| ADR-008 | REST API 与 MCP 是统一应用服务的并列入站适配器；A2A 仅用于外部 RemoteAgent |
| ADR-009 | 不可信代码使用 K8s Job + gVisor |
| ADR-010 | 前端重建为 React 19 + Vite + TailAdmin × Radix |
| ADR-011 | Command 按 Run command_seq 经 PostgreSQL Outbox 顺序交付 Temporal |
| ADR-012 | Event Outbox Publisher 是 PostgreSQL 到 NATS 的唯一发布路径 |
| ADR-013 | Agno 只通过 Deferred GatewayProxyTool 调用受控 Tool |
| ADR-014 | StrategyDraft 可变、StrategyVersion 不可变 |
| ADR-015 | 控制台仅作为基于公开接口的测试与观测客户端 |

## 26. 发布验收标准

v1 发布前必须全部满足：

- DeepTalk 可以通过 REST 或 MCP 查询可用能力、提交 inline SwarmSpec 并取得最终 RunResult。
- 同一 SwarmSpec 经 REST 与 MCP 提交时使用相同的编译、权限、命令和结果语义。
- 控制台只调用公开接口，关闭或未部署控制台时不影响 API、MCP 和执行运行时。
- 同一 Idempotency-Key 不会创建两个 Run。
- API 接受后即使 Temporal 不可用，请求也不会丢失。
- Worker 在任意 Agent Task 中被杀死后，Run 能自动恢复。
- 已成功的并行 Task 不会因另一个 Task 重试而重复产生外部副作用。
- Pause、Resume、Cancel 和 Approval 有明确合法状态迁移。
- 同一 Run 的 Start/Pause/Resume/Cancel/Approval 严格按 command_seq 应用，重复 request_id 返回原结果。
- SSE 可以使用 after/Last-Event-ID 完成无竞态断线续传，并正确处理 gap、backpressure 和过期游标。
- Run、Task、Attempt 和 Event 在 UI 与数据库中一致。
- 同一 transition_id 或 producer_seq 重放不会生成第二个 Event；投影故障可由 Reconciler 修复。
- 所有有副作用 Tool 均声明幂等、补偿或人工恢复策略。
- 不可信代码不能访问宿主机、集群凭据、数据库或未批准网络。
- 任意租户不能读取其他租户的 Run、Artifact、Trace 或 Audit。
- Token、成本、模型、工具和审批可以按 Run 审计。
- 前端通过 TypeScript、ESLint、Vitest、Playwright 和多视口 light/dark 截图门禁。
- ApexCharts 商业/OEM 许可已确认，或在设计系统层正式批准替代方案。

## 27. 参考

- Agno AgentOS：https://docs.agno.com/agent-os/introduction
- Temporal Python：https://docs.temporal.io/develop/python
- Temporal Workflow Determinism：https://docs.temporal.io/workflow-definition
- NATS JetStream：https://docs.nats.io/nats-concepts/jetstream
- MCP Specification 2025-11-25（当前稳定基线）：https://modelcontextprotocol.io/specification/2025-11-25
- MCP 2026-07-28 Release Candidate：https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- A2A Specification 1.0：https://a2a-protocol.org/latest/specification/
- AG-UI：https://docs.ag-ui.com/
- OpenTelemetry Python：https://opentelemetry.io/docs/languages/python/
- Arize Phoenix：https://arize.com/docs/phoenix
- React Flow：https://reactflow.dev/
- 本地设计系统：../.agent/skills/b-design-system-tailadmin-radix/SKILL.md
