# SwarmCore 系统设计

| 属性 | 值 |
|---|---|
| 状态 | Baseline / 可实施 |
| 版本 | 2.0 |
| 日期 | 2026-07-20 |
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
    Provider[Model / OCR / External Provider]
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
| 模型与 Provider 层 | LLM、Embedding、Vision、OCR、文档解析、知识库及外部数据接入 | 不直接写业务状态或持有 Run 生命周期 |
| 原子工具能力层 | 解析、切片、抽取、检索、规则、计算和渲染 | 硬规则不写进 Prompt；副作用不绕过 Tool Gateway |
| 领域智能体层 | 分类、语义抽取、归纳、根因解释、评审和报告叙述 | Agent 不等同微服务，不直连数据库、Secret 或外部 Endpoint |
| 业务应用层 | Workbench、Capability Pack、RuleSet、领域状态、问题和报告 | 不复制 Runtime、权限、审计和事件体系 |

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
3. Capability Run Service 把直接运行转换成标准 SwarmSpec/ExecutionPlan，再调用 Run Service。

状态仅为 `READY` 或 `NOT_READY`，后者返回稳定原因码：`EXECUTOR_MISSING`、`ADAPTER_MISSING`、`MODEL_ROUTE_MISSING`、`SECRET_MISSING`、`DEPENDENCY_NOT_READY`、`DEPENDENCY_CYCLE`、`HEALTH_CHECK_FAILED`、`ENVIRONMENT_NOT_ALLOWED`、`CAPABILITY_PACK_DISABLED`、`SCHEMA_INVALID`、`POLICY_DENIED`。

就绪门槛：Tool 必须有合法 Schema、executor、风险/幂等/恢复策略和健康状态；Model 必须有 Route、可租用 Secret 和健康 Endpoint；Agent 的 Adapter、模型和 Tool 依赖必须全部就绪；Strategy 必须已发布并编译；Capability Pack 启用前全部必需依赖必须就绪。

`ProjectConfiguration` 继续使用 `project_configurations` 表和旧 API；用户层称为 Capability Preset。Preset 只保存能力引用和可复用参数，不保存 Secret。能力中心的直接运行和 REST/MCP 均复用同一应用服务，不建立旁路。

## 5. 执行与一致性契约

### 5.1 SwarmSpec 与 ExecutionPlan

当前 Compiler/Runtime 支持 `agent`、`tool`、`router`、`loop`、`parallel`、`join`、`reducer`、`approval`、`input`。Schema 中的 `team`、`transform`、`subflow`、`emit` 在 v1 基线中不可执行，提交时返回 `UNSUPPORTED_NODE_TYPE`；是否实现由后续里程碑决定。

条件表达式使用受限语法/CEL，不使用 Python `eval`。Router 按声明顺序选择首个匹配分支；Loop 必须有 1..20 的确定上限。ExecutionPlan 至少冻结 Spec/Compiler/Runtime 版本、Registry Snapshot、Policy Revision、资源版本、重试/超时/预算和输入输出 Schema；Run 不读取可变 Draft。

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
- Agent 内只允许无副作用 Tool；有副作用 Tool 展开为显式节点，必须声明幂等、补偿或人工恢复策略。
- Workflow 关闭前必须等待终态投影成功；NATS、Trace 和 Cache 均不是最终事实源。

### 5.4 Artifact 与大型数据

运行前输入使用 BlobObject，Run 输出使用 Artifact，二者复用对象存储、扫描、OPA、Capability Token 和保留机制，但保持不同业务契约。文件上传先进入 staging，通过 SHA-256、大小、MIME 和恶意内容检查后提交；Workflow 只传稳定引用和小型结构化数据，不传文件字节或完整模型上下文。

大文件按页/块并行处理并允许分片重试；Activity 内联结果默认不超过 256 KiB，超限写 Artifact。向量行必须带 tenant_id、project_id、source_id、embedding_model 和 embedding_version；模型变化写新版本，不原地覆盖。

## 6. 业务能力扩展

### 6.1 通用模型

Capability Pack 以不可变 Manifest 组合 WorkItem/Input/Output Schema、Strategy、Agent、Tool、Rule、Report、权限、事件和 View Definition。Manifest 不允许 `module`、`script`、`classPath`、`componentUrl` 等代码入口；项目显式绑定不可变版本。项目可编辑绑定级 `configuration`，更新配置只更新当前项目的绑定参数，不修改已发布 Manifest、内容哈希或历史评估快照。

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

兼容边界：业务扩展只新增资源，不改变 Run、Artifact、Strategy、RunEvent 和控制命令语义；禁用 Pack 只阻止新执行，历史数据按快照读取；数据库变更只新增 migration；REST/MCP 复用同一 Workbench 服务；业务事件使用独立命名空间，不修改 `run.*`。

### 6.2 文档、知识与证据

文档能力共享 BlobObject、Document、Page、Chunk、Table、Extraction 和 Evidence 语义；知识库在此基础上管理 KnowledgeDocument、KnowledgeChunk 和向量索引版本。Evidence 至少包含来源 Blob、页码、可选归一化坐标、文本片段、哈希和生成能力版本。

OCR、分类和字段抽取先通过版本化 JSON Schema，再进入确定性规则或跨文件 Tool。低置信度或缺失证据固定进入失败、降级或 `REVIEW_REQUIRED`，不得自动形成合规结论。抽取按 tenant/project、Blob SHA-256、Provider/Agent/Schema 版本去重。

### 6.3 AI 质量评测

AI 结果统一包含 `data`、`evidence`、`confidence`、`qualityFlags`、`schemaVersion`，provenance 冻结模型、Prompt、Provider、Agent、Tool 和规则版本。`confidence` 必须基于任务样本校准，不直接使用模型自报概率。

质量控制分三阶段：

1. 离线评测：版本化脱敏样本集，按任务记录分类、OCR、字段/表格抽取、检索、引用和复核指标；
2. 运行时质量门：Schema、证据完整度、置信度、确定性规则和跨文件检查；
3. 生产反馈：记录人工改判、漏检、豁免和漂移，确认脱敏后才能进入新评测集或训练流程。

业务 `Evaluation` 不复用为 AI 评测记录。AI 评测使用 BenchmarkSuite、QualityEvaluationRun、SampleCase、MetricResult 和 ReviewDecision 语义；产品事实保存在 PostgreSQL，Phoenix 只用于 Trace、实验和诊断。

### 6.4 目标业务落位

以下是后续扩展边界，不表示已经实现或进入当前发布承诺：

| 能力 | 落位 |
|---|---|
| 基础 AI 与质量评测 | Provider、原子 Tool 和质量平面，不建设成业务 Agent |
| 文件结构化 | 共享 Document Intelligence，由解析/OCR、文档 Tool 和分类/抽取 Agent 组成 |
| 文件完整性 | `contract-integrity` Pack，确定性 RuleSet 为主 |
| 履约计划与采集 | `contract-performance` Pack，沉淀义务、里程碑和执行证据 |
| 发票一致性 | `invoice-assurance` Pack，抽取后执行确定性规则 |
| 偏差分析 | 时间/内容/成本计算 Tool 加根因解释 Agent |
| 报告生成 | 结构化结果聚合、版本化模板和 AI 叙述，JSON 为事实 |
| 调度校准 | Runtime 决策加质量监督 Agent 建议 |
| 招采与供应商风险 | `procurement-consistency`、`supplier-risk` Pack，共享主数据和 Provider |

## 7. 公共契约

公共契约以 Pydantic/JSON Schema、OpenAPI、数据库 migration 和事件 Schema 为机器可执行事实；本文只固定语义，避免复制完整字段表。

### 7.1 API 与 MCP

- Strategy：草稿、校验、编译、发布和不可变版本；
- Run：创建、查询、结果、事件、pause/resume/cancel/input/approval；
- Capability Center：统一目录、readiness、直接运行和 Preset；
- Workbench：Pack、WorkItem、Attachment、Evaluation、Finding、Report 和 RuleSet；
- Governance：Artifact、Audit、Policy、Webhook 和项目设置。

REST 使用 Problem Details；稳定错误至少覆盖 Schema/语义错误、策略拒绝、资源不存在、幂等冲突、版本冲突、非法状态、游标过期、预算超限、Provider 不可用，以及 Pack/RuleSet/Blob 的业务诊断。MCP 只暴露调用方所需能力并复用同一应用服务。

最终结果使用统一信封：终态、输出 Schema 版本、内联输出或 ArtifactRef、任务摘要、usage、warnings、未解决副作用、错误和 provenance。FAILED、CANCELLED、TIMED_OUT 也返回相同信封；非终态读取结果返回 `RUN_NOT_TERMINAL`。

### 7.2 数据与租户

核心数据域包括 Registry/Strategy、Run/Task/Execution/Attempt、Command/Approval、Event/Outbox、Artifact/Blob、Audit、ToolEffect、Capability Pack/Workbench 和 Quality Evaluation。具体表、字段、索引和 RLS 以当前 ORM 与 Alembic migration 为准。

所有项目数据同时保留 tenant_id 和 project_id；应用过滤与 PostgreSQL RLS 同时生效。API/Worker 使用无 BYPASSRLS 角色，每个事务设置租户上下文；跨租户维护使用独立受审计角色。业务事务中禁止同步调用 Temporal、NATS、S3 或 Webhook。

### 7.3 事件与订阅

事件信封固定包含 id、seq、type、schemaVersion、tenantId、projectId、runId、可选 taskId/attemptId、occurredAt、trace/causation/correlation 和 data。破坏性变化发布新 schemaVersion；脱敏保留信封和 seq，不能删除事件制造假 gap。

Event Gateway 提供 SSE `after`/`Last-Event-ID`、心跳、背压、历史补读和过期游标 410。Webhook 由独立 Temporal Workflow 签名、重试并记录 delivery；前端和外部调用方不得直连 NATS。

## 8. 安全、治理与可观测

- OIDC JWT 绑定 tenant/project/scope；OPA 处理模型、Tool、数据等级、预算、下载和 obligations。
- Secret 只保存引用，通过 Vault 短租约获取，不进入 Spec、Prompt、Preset、事件、日志和 Artifact 元数据。
- Tool 分 L0 纯计算、L1 只读外部、L2 有副作用、L3 不可信代码；风险决定审批、幂等、补偿和 Sandbox。
- Capability Token 绑定 tenant/project/run/node/tool/effect/audience/scope/jti，短 TTL、最小权限、可撤销。
- Sandbox 强制非 root、只读根文件系统、drop capabilities、禁 host namespace/hostPath、默认拒绝出网并限制 CPU、内存、PID、磁盘和 wall time。
- Trace 贯穿 HTTP、Run、Workflow、Activity、模型、Tool、Artifact 和 Webhook；Metrics 覆盖队列、执行、成本、预算、Provider、Outbox 和投影；Audit 只追加并记录人工与策略决定。
- 日志必须结构化和脱敏，禁止 Prompt、Secret、Token、原始文件内容和跨租户标识泄露。

## 9. 部署、容量与恢复

生产由无状态 API/Gateway、Dispatcher/Publisher、Control/Agent/Tool/Webhook Worker、Projector/Ingestor、Artifact Gateway 组成；依赖 PostgreSQL、Temporal、NATS、S3、Vault、OPA 和模型 Provider。各 Worker 使用独立 Temporal Task Queue，按队列延迟和 Provider 容量扩缩容。

本地 Compose 提供 PostgreSQL、Temporal、NATS、OPA、Vault dev、Phoenix 及核心服务；Artifact 可使用本地文件 Adapter。生产默认 PostgreSQL PITR、NATS 三副本、S3 Versioning、Vault Audit、Temporal HA/Cloud，并定期恢复演练。

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

参考规范：Temporal Python/Workflow Determinism、MCP 2025-11-25、OpenTelemetry、NATS JetStream、Agno AgentOS、AG-UI。依赖版本以 lockfile 和部署清单为准。
