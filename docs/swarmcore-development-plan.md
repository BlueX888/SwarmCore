# SwarmCore 开发计划与里程碑

| 属性 | 值 |
|---|---|
| 文档状态 | Living Document / 持续更新 |
| 版本 | 2.0 |
| 建立日期 | 2026-07-16 |
| 最近更新 | 2026-07-17 |
| 已提交基线 | `eb75ac3`（受控 Tool 与有界编排） |
| 当前候选基线 | M3 维护性收敛与 M4 治理能力位于未提交工作树 |
| 当前焦点 | M5：v1 契约与基线闭合 / G0；B1：业务智能体扩展 E4-E5 |
| 唯一下一门禁 | G0（见第 5 节） |
| 架构事实源 | [SwarmCore 系统设计](./swarmcore-system-design.md) |

## 1. 文档职责

系统设计回答“SwarmCore 是什么以及必须遵守哪些边界”，本文档只回答四个问题：

1. 当前可靠拥有哪些能力；
2. 还有哪些事实、能力或证据缺口；
3. 为什么按当前顺序推进；
4. 用什么可执行证据判定完成。

本文档不再充当开发流水账。已关闭工作合并为能力基线，详细过程由 Git 历史保留；正文只维护当前事实、开放门禁和未来交付结果。

## 2. 第一性原理

### 2.1 价值闭环

SwarmCore 的最小完整价值不是“支持更多节点”，而是让调用方可以信任一次编排执行：

```text
调用方提交声明式方案
  -> SwarmCore 统一校验并冻结执行语义
  -> 在权限、预算和副作用约束下耐久执行
  -> 故障后恢复且不丢失已接受的工作
  -> 返回可追溯、可审计的状态与结果
```

只有同时满足以下条件，能力才产生可交付价值：

- **契约真实**：公开 Schema、Capability Catalog、Compiler、Runtime 和客户端行为一致。
- **执行可靠**：接受、命令、状态、事件和外部副作用在重试或故障下保持一致。
- **边界受控**：租户、权限、Secret、预算、Tool、Artifact 和沙箱约束不可绕过。
- **可被运营**：部署、升级、观测、告警、恢复和容量边界有可执行证据。

### 2.2 不可变约束

1. DeepTalk 和其他调用方负责目标理解与编排决策；SwarmCore 只负责受控、可靠和耐久执行。
2. REST API 与 MCP 复用同一应用服务、权限、编译、命令和结果语义。
3. SwarmSpec 是声明式方案事实源，ExecutionPlan 是运行时不可变输入；控制台不建立第二套语义。
4. Temporal Workflow 保持确定性，网络、数据库、模型和文件 I/O 只进入 Activity。
5. PostgreSQL 是产品状态事实源，不绕过状态机、幂等、Outbox、RLS、审计或补偿机制。
6. Agent SDK、Provider、OPA、Vault、S3 和具体运行环境通过 Adapter、Provider 或 Gateway 接入，不污染领域核心。
7. 所有数据访问保留 tenant/project 边界；条件表达式禁止 Python `eval`。
8. 重构只能由重复逻辑、边界倒置、测试阻塞、性能、安全或故障证据触发，并必须保留外部契约和回归证据。

### 2.3 排序原则

优先级固定为：

1. 关闭不可复现、契约不一致和安全正确性风险；
2. 证明真实生产环境可部署；
3. 证明故障后可恢复；
4. 在已知负载下证明容量和 SLO；
5. 最后扩展非核心节点、生态 Adapter 和可选基础设施。

因此不以文件数、代码量、组件数量或“设计中曾经出现”作为排期依据，也不为未经验证的负载提前扩容。

## 3. 状态与证据

### 3.1 交付状态

| 状态 | 定义 |
|---|---|
| `PLANNED` | 结果、范围、依赖和退出标准已定义，尚未开始实现 |
| `IN_PROGRESS` | 已开始范围内工作，仍有交付项或门禁未关闭 |
| `IMPLEMENTED` | 实现完成且相关本地测试通过，但不可变基线、CI 或目标环境证据仍不完整 |
| `VERIFIED` | 全部退出标准通过，证据已绑定到不可变提交、CI 运行或明确的验收环境 |
| `BLOCKED` | 存在明确外部阻塞，范围内没有可继续推进的工作 |

### 3.2 证据层级

| 层级 | 含义 |
|---|---|
| `LOCAL` | 开发工作树或本机环境通过 |
| `CI` | 从干净检出自动复现 |
| `STAGING` | 在生产同构环境完成部署、联调或故障验收 |
| `PRODUCTION` | 真实负载下形成运行、SLO 或恢复证据 |

交付状态与证据层级必须同时记录。`IMPLEMENTED / LOCAL` 不等于生产可用，较晚里程碑完成也不能替代较早门禁的缺失证据。

## 4. 当前能力基线

### 4.1 当前事实

| 项目 | 当前事实 |
|---|---|
| Git HEAD | `eb75ac3`，已提交 M3 受控 Tool、Router、Loop 和取消语义 |
| 远端分支 | `origin/codex/phase2a-human-control` 停在 `0cbeb9a`；当前分支领先 1 个提交 |
| 候选实现 | M3 维护性收敛与 M4 治理、安全、Provider、Sandbox、Webhook 和补偿代码仍在工作树 |
| 自动化 | 现有 GitHub Actions 只覆盖后端；当前分支及候选实现尚无合格远端 CI 证据 |
| 当前目标 | 不再增加产品表面积，先形成真实、可复现且范围明确的 v1 候选基线 |

### 4.2 现有能力与候选基线

历史 M0 至 M4 不再作为活跃里程碑逐节维护，统一合并为以下能力域：

| 能力域 | 已交付边界 | 状态 | 证据层级 | 基线/证据 | 开放门禁 |
|---|---|---|---|---|---|
| 耐久执行与人工控制 | SwarmSpec、Compiler、Plan Hash；PostgreSQL/RLS/Outbox；Temporal；顺序、并行、DAG、Supervisor、Reducer；Pause/Resume/Cancel/Approval/Input/Retry | `VERIFIED` | `LOCAL` | `eb75ac3`，E2 | 持续回归 |
| 调用方契约与策略控制台 | REST/MCP 共用应用服务；capabilities/validate/compile/create/status/result/control；inline Spec；Strategy Canvas；JSON/YAML；Run 控制台 | `IMPLEMENTED` | `LOCAL` | `0cbeb9a`，E1 | G0：远端 Fake Agent E2E 与完整 CI |
| 受控 Tool 与有界编排 | Registry Snapshot；GatewayProxyTool；Capability Token；effect journal；高风险审批；`tool`、`router`、`loop` Runtime | `VERIFIED` | `LOCAL` | `eb75ac3`，E2 | 持续回归 |
| 治理与安全候选能力 | JWT/OPA、Vault、Artifact/Model Gateway、预算、Webhook/Audit/OTel、Sandbox 契约和补偿 | `IMPLEMENTED` | `LOCAL` | 当前工作树，E3 | G0：不可变基线 |
| 通用业务智能体扩展 E0-E3 | Capability Pack Registry；Workbench；输入 Blob；RuleSet；Evaluation/Finding/Report；文件完整性校验；REST/MCP/UI | `IMPLEMENTED` | `LOCAL` | 当前工作树，BA-E3 | B1：E4 AI 增强与 E5 第二能力包通用性闭合 |

状态只评价表中已经声明的能力边界，证据层级说明已证明到哪个环境；M6 及之后的环境资格不会反向改写基础能力状态。

### 4.3 证据索引

| ID | 基线 | 层级 | 已记录结果 | 证据边界 |
|---|---|---|---|---|
| E1 | `0cbeb9a` | `LOCAL` | 52 项单元测试、8 项集成测试、17 项 Vitest、21 项 Playwright、前端 lint/build 和真实 Ollama smoke 通过 | 合并覆盖耐久执行、人工控制、REST/MCP 本地等价、DeepTalk 模拟和 Strategy Canvas；无合格远端 CI |
| E2 | `eb75ac3` | `LOCAL` | Ruff、mypy、69 项单元测试、10 项 PostgreSQL/Temporal 集成测试通过 | 在 E1 基础上回归 Tool/Router/Loop、审批、effect 幂等和取消语义 |
| E3 | 2026-07-17 工作树 | `LOCAL` | Ruff、mypy、105 项单元测试通过；新增项目配置 PostgreSQL 集成测试通过，既有 15 项 PostgreSQL/Temporal/MinIO/Vault 集成证据保持；前端 lint、26 项 Vitest、33 项 Playwright 和 build 已重跑通过 | 未绑定提交；其余集成测试本轮未全量重跑；真实 Kubernetes、gVisor 与 ClamAV daemon 未验收 |
| BA-E3 | 2026-07-17 工作树 | `LOCAL` | Ruff、mypy、117 项单元测试、13 项 PostgreSQL/Temporal/Blob 集成测试、27 项 Vitest、33 项 Playwright、前端 lint/build 通过 | 未绑定提交；4 项环境依赖集成测试跳过（S3/MinIO、Vault、持久 Temporal 重启恢复），ClamAV daemon 未验收 |

以上是已有验收记录，不表示本次文档重构重新执行了这些测试。新证据必须绑定 commit、CI run 和环境信息，不能只追加孤立的“通过”文本。

## 5. 开放门禁与风险

| ID | 优先级 | 当前缺口 | 关闭条件 | 所属里程碑 |
|---|---|---|---|---|
| G0 | Release Blocker | M3 维护性收敛与 M4 候选实现未形成不可变提交；远端 CI 未覆盖当前分支，且现有 workflow 缺少前端门禁 | 干净检出下后端、前端、集成和 Fake Agent E2E 全绿，证据绑定 commit 与 CI run | M5 |
| G1 | P1 | Spec 声明的 `team/transform/subflow/emit` 不可执行；配置/CLI 入站也未实现，设计承诺与真实 v1 范围不一致 | v1 明确只保留现有 9 类可执行节点和 REST/MCP 入站；Schema、Catalog、Compiler、Canvas、系统设计和文档一致表达延期能力 | M5 |
| G2A | P1 | 当前 SSE 直接读取 PostgreSQL，缺少公开事件语义的 gap、backpressure、410 和断线续传集成证据 | 冻结协议无关的事件查询/订阅契约并在 CI 验证游标、顺序、gap、410 和客户端重连，不建立临时双轨业务逻辑 | M5 |
| G2B | P1 | 无 Runtime Event Ingestor 和独立 Event Gateway；现有集成环境未验证真实 NATS JetStream 发布、重投递和恢复 | 在生产同构环境打通 PostgreSQL/Outbox -> JetStream -> Event Gateway，并验证慢消费者、背压、重连和滚动升级 | M6 |
| G3 | P1 | 只有 Compose；Sandbox、ClamAV、工作负载身份、mTLS 和 Provider 主要停留在本地或协议级证据 | 在真实 Kubernetes 生产同构环境完成端到端安全与 Provider 验收 | M6 |
| G4 | P1 | Temporal Replay/Continue-As-New、基础设施故障、备份恢复、RPO/RTO 和完整安全故障矩阵证据不足 | 故障注入、回放、恢复和安全套件通过，并完成恢复演练 | M7 |
| G5 | P2 | 无容量基线、租户公平性、背压、Autoscaling、HA 和可运营 SLI/SLO 证据 | 在明确负载模型下验证容量、延迟和恢复目标，并具备生产可用性 SLI、告警与 Error Budget | M8 |
| G6 | P2 | Web 主 Chunk 大于 500 KiB | 先测量真实加载影响；只有影响目标体验时才按路由或依赖拆包 | 候选优化 |

## 6. 新里程碑总览

| 里程碑 | 可交付结果 | 前置条件 | 目标证据 | 状态 |
|---|---|---|---|---|
| M5 | v1 契约真实且候选基线可从干净检出复现 | 当前候选实现 | `CI` | `IN_PROGRESS` |
| B1 | 通用业务智能体扩展和两个差异能力包完成代码闭环 | M5 候选基线；E0-E3 已实现 | `CI` | `IN_PROGRESS` |
| M6 | 单集群生产同构环境可安全部署、升级和观测 | M5、B1 `VERIFIED` | `STAGING` | `PLANNED` |
| M7 | 关键故障、安全边界和备份恢复有可重复证据 | M6 `VERIFIED` | `STAGING` | `PLANNED` |
| M8 | 容量、背压、Autoscaling、HA 和 SLO 有测量边界 | M7 `VERIFIED` | `STAGING` | `PLANNED` |
| M9 | 同一不可变候选版本通过独立 v1 发布门禁 | M8 `VERIFIED` | `STAGING` | `PLANNED` |

依赖顺序为“契约 -> 部署 -> 恢复 -> 容量 -> 发布”。上表是里程碑状态的唯一事实源；除非出现已确认的 P0 安全问题，不跨过前置里程碑并行扩大能力表面积。

资格必须累积但不能自动继承：后续里程碑修改代码、Schema、Migration、镜像、部署或配置后，必须在新候选版本上重跑所有受影响的前置门禁。未受影响的外部演练证据可以引用，但必须说明适用版本和未失效理由。

## 7. M5：v1 契约与基线闭合

### 7.1 结果

形成一个不可变、可复现且不夸大能力范围的 v1 代码与集成基线。任何调用方只依赖公开契约即可完成核心闭环，开发工作树和本地手工结果不再是完成依据；Release Candidate 只在 M9 产生。

### 7.2 范围

- 将 M3 维护性收敛和 M4 候选实现整理为可审查提交，不混入无关变更。
- 扩展远端 CI，覆盖 Ruff、mypy、单元测试、完整集成测试、前端 lint/test/build、必要的 Playwright 和 Fake Agent DeepTalk E2E。
- 建立 v1 能力矩阵，逐项冻结节点、入站方式、Model、Tool、Artifact、Webhook 和 Sandbox 的支持边界与触发路径；M6 不得隐式扩展该矩阵。
- 当前路线图默认不在 v1 实现 `team/transform/subflow/emit` 和配置/CLI 入站；M5 通过系统设计更新正式固化延期决定，恢复进 v1 必须先提供明确场景并重新评估范围。
- 冻结 REST/MCP 的编译、幂等、权限、命令、错误、状态和 RunResult 契约。
- 冻结协议无关的事件查询/订阅应用契约，补齐 SSE 游标、顺序、gap、410 和客户端断线续传的 CI 证据；Event Gateway、真实 JetStream 与服务端慢消费者背压留给 M6。
- 由真实 DeepTalk 或一个不链接 SwarmCore 内部应用服务的代表性调用方执行黑盒契约验收；不可用时明确记录外部依赖，不能用内部单元调用冒充。
- 将系统设计第 26 章逐项映射到自动化测试、CI、环境验收或明确的后续门禁。
- 核对 migration `0001 -> 0006`、配置、启动方式和兼容性说明。

### 7.3 固定验收场景

从干净检出和空数据库启动标准测试环境，由 DeepTalk Harness 分别通过 REST 与 MCP：

1. 查询可执行能力并编译同一 inline SwarmSpec；
2. 创建“两路 Agent -> 高风险 Tool 审批 -> Reducer”的 Run；
3. 在执行中重启 Worker，确认 Run 自动恢复；
4. 使用 SSE 断线续传并验证过期游标行为；
5. 获得结构等价的 Plan Hash、状态、事件和 RunResult；
6. 重放相同幂等键与 effect ID，确认不会创建第二个 Run 或重复外部副作用。

### 7.4 退出标准

- [ ] G0、G1 和 G2A 全部关闭。
- [ ] 所有证据绑定同一不可变 commit，远端 CI 从干净检出全绿。
- [ ] 公开可执行节点不存在 Schema/Catalog/Compiler/Runtime 分叉。
- [ ] v1 能力矩阵中的每项均有公开触发路径和契约证据；M6 只生产化该矩阵。
- [ ] 独立黑盒调用方完成 capabilities -> compile -> create -> status/events -> result 闭环，并记录与真实 DeepTalk 的差异。
- [ ] 系统设计第 26 章每项均有责任里程碑和证据位置，不保留“默认认为已通过”。
- [ ] 公共 API、事件、数据库、Plan Hash 和配置变更已记录兼容性；破坏性变更有迁移方案。
- [ ] README、`.env.example`、系统设计和本计划与最终支持范围一致。

### 7.5 非目标

- 不建设 Kubernetes HA、Autoscaling 或多区域拓扑。
- 不实现 `team/transform/subflow/emit`、动态派生或配置/CLI 入站。
- 不引入 A2A、其他 Agent Runtime Adapter、Qdrant、Kafka 或 Kata。

## 7A. B1：通用业务智能体扩展

M5 候选基线之后、M6 生产资格之前完成。E0-E3 已在本地实现：冻结 Capability Pack/Workbench/RuleSet/Blob/REST/MCP 契约，完成不可变 Registry、通用 Workbench 和确定性文件完整性校验。剩余 E4 为 AI 文档理解与人工复核，E5 以无附件、无 RuleSet 的工单分诊能力包验证通用性；B1 未完成前不进入业务扩展的生产资格。

事实来源为 [通用业务智能体扩展实施计划](./swarmcore-business-agent-extension-plan.md)，数据库和事件兼容边界见 [业务智能体扩展 v1 兼容性说明](./swarmcore-business-agent-compatibility.md)。

## 8. M6：单集群生产资格

### 8.1 结果

证明 SwarmCore 可以在一个生产同构 Kubernetes 集群中安全安装、升级、回滚和观测，并完成真实 Provider 参与的核心业务闭环。

### 8.2 范围

- 只生产化 M5 v1 能力矩阵中已确认的触发路径；必要的 Application、Workflow、Activity 或 Adapter 接线必须显式实现，独立 Gateway 存在不等于 Run 已支持该能力。
- 建立版本化 Helm 部署、配置校验、Migration Job、健康检查、资源限制和回滚路径。
- 接入真实 OIDC/JWKS、workload identity、mTLS、OPA、Vault Kubernetes Auth、S3、LiteLLM、ClamAV、NATS 和 OTel Collector。
- 使用真实 Kubernetes Job + gVisor 验证 Sandbox Admission、NetworkPolicy、无 ServiceAccount Token、受控出站和 NodeLost 收敛。
- 完成 Runtime Event Ingestor、Event Gateway 和真实 JetStream 链路；完成 v1 矩阵内 Webhook、Artifact、Model、Tool 和 Sandbox 路径联调。
- 部署 Phoenix、Prometheus/Grafana、Alloy/Loki 以及最小 Dashboard/Alert，使 Trace、Metrics 和 Logs 的查询与告警退出标准可执行。
- 提供安装、升级、回滚、密钥轮换、告警和常见故障 Runbook。

### 8.3 验收矩阵

- 部署：空集群安装、Migration、滚动升级、失败回滚和配置/密钥轮换。
- 核心闭环：通过真实身份运行 Model -> 高风险 Tool 审批 -> Result，并验证 Secret Lease、Trace 和 Audit。
- Gateway：按 M5 能力矩阵分别验证 Artifact/ClamAV、Webhook 和 Sandbox/gVisor；只有存在已冻结 Runtime 触发路径时才纳入综合 Run。
- 事件：真实 JetStream 下验证事件顺序、重连、慢消费者背压和组件滚动升级。
- 安全：跨租户、mTLS、OPA fail-closed、受控出站和无集群凭据。

保留一条跨服务综合闭环用于发布冒烟，但不以单个“超级场景”替代上述可独立定位的验收项。

### 8.4 退出标准

- [ ] G2B 和 G3 关闭，目标生产路径不使用 dry-run 或协议 mock 代替真实环境。
- [ ] 干净安装、`0001 -> head` 迁移、滚动升级和回滚可重复执行。
- [ ] tenant/project 隔离、mTLS、OPA fail-closed、Secret 撤销和出站限制在集群中通过。
- [ ] 核心 Trace、Metrics、JSON Logs 和 Audit 可查询，并有最小告警集。
- [ ] 关闭控制台后 REST/MCP/Worker/Event 链路仍完整运行。
- [ ] M6 候选 commit 与镜像集重新通过 M5 的 CI 和契约回归。

### 8.5 非目标

- 不在本里程碑承诺最终容量、跨区域灾备或完整 HA 指标。
- 不扩展新的编排节点和生态 Adapter。

## 9. M7：故障、安全与恢复资格

### 9.1 结果

证明已接受的工作在关键组件故障下不会静默丢失、越权或重复产生已确认副作用，并能在声明的 RPO/RTO 内恢复。

### 9.2 范围

- Temporal Replay、Continue-As-New 和 Workflow 版本兼容门禁。
- 在固定参考负载下验证 Worker/Node 丢失，PostgreSQL、Temporal、NATS、Provider、Vault、S3 和网络短暂故障。
- Dispatcher、Event Publisher、Projection Reconciler 的提交成功/响应丢失、PubAck 丢失和重复投递。
- Event Gateway 与 NATS 故障恢复；PostgreSQL/Event/Outbox 是重建依据，NATS 不作为业务事实备份源。
- Run Cancel 与 Approval/Input/补偿并发，effect 幂等与逆序补偿。
- 跨租户、JWT Scope、RLS 连接污染、SSRF/DNS Rebinding、Secret 泄漏、Sandbox 提权和 Artifact 攻击矩阵。
- PostgreSQL、Temporal、Vault 和 S3 的备份恢复；JetStream Stream 可重建，并能从 PostgreSQL Event/Outbox 重放和对账。

### 9.3 验收矩阵

按 Worker、数据存储、事件链、Provider、控制命令、补偿和安全边界拆分故障用例，使每项可独立重复和定位。另保留一条包含审批、模型、外部副作用、Artifact 和补偿的长 Run 综合演练；最终确认状态和审计可重建、已成功 effect 不重复、未完成 effect 可恢复或补偿、跨租户读取始终失败。

### 9.4 退出标准

- [ ] G4 关闭，系统设计第 22.2 至 22.5 节的适用高风险场景均有自动化或演练证据。
- [ ] Workflow Replay 阻止不兼容发布，长历史能按设计安全 Continue-As-New。
- [ ] Projection、Outbox、Event 和 Webhook 重放不改变最终事实。
- [ ] 备份恢复达到 RPO ≤ 5 min、RTO ≤ 30 min，或以测量数据修订系统设计目标。
- [ ] 故障与安全 Runbook 由非实现者按文档复现。
- [ ] M7 候选版本重新通过受影响的 M5 CI 与 M6 部署、安全和综合冒烟门禁。

### 9.5 非目标

- 不以故障测试结果替代容量压测。
- 不同时引入多区域主动-主动架构。

## 10. M8：容量、背压与 SLO 资格

### 10.1 结果

给出可复现的负载模型、容量边界和部署规格，证明系统在饱和时排队或降级，而不是丢失工作、突破预算或拖垮其他租户。

### 10.2 范围

- 定义代表性 Spec、Run 时长、模型/Tool 延迟、事件量、租户分布和峰谷负载。
- 验证租户/项目配额、maxParallelism、Temporal Task Queue、Provider 限流和 Tool/Sandbox 容量背压。
- 建立 Worker Autoscaling、HPA、PDB、队列延迟和租户公平性策略。
- 验证 API、Event Gateway、Dispatcher、Publisher、Worker、PostgreSQL、Temporal、NATS、Vault 和 S3 的 HA 行为。
- 建立 SLI/SLO Dashboard、告警阈值、Error Budget、容量报告和版本间性能回归门禁。
- 执行持续负载、峰值、突发、慢消费者和 Soak Test。

### 10.3 退出标准

- [ ] G5 关闭，测试数据、脚本、部署规格和结果可复现。
- [ ] 达到系统设计第 3.1 和第 21 章中可在 Staging 压测的延迟、吞吐、恢复和容量目标，或基于证据修订不合理目标。
- [ ] 月度 99.9% 可用性不以 Staging 压测冒充通过；发布前只验收 SLI、Dashboard、告警和 Error Budget 就绪，真实可用性在发布后以 `PRODUCTION` 证据持续记录。
- [ ] 饱和时保持有界队列和明确错误/状态，不以无限协程或无界缓存吸收压力。
- [ ] 单一租户或 Provider 退化不会无限挤占其他租户容量。
- [ ] Autoscaling、HA 切换和告警在目标负载下通过。
- [ ] M8 候选版本重新通过受影响的 M5-M7 门禁；在新副本、队列和扩缩容策略下，M7 的关键恢复与 RPO/RTO 场景重新通过。

### 10.4 非目标

- 不为没有测量证据的热点做预先重构。
- 不把多区域、额外数据库或消息系统作为默认解法。

## 11. M9：v1 发布门禁

### 11.1 结果

从 M8 已验证的同一不可变 commit 和镜像 digest 产生 Release Candidate，独立复验、汇总并签署 v1 发布证据；本阶段不再实现或重新定义能力。

### 11.2 范围

- 冻结同一 commit、镜像 digest、Schema、Migration 和配置基线；任何代码变化都使受影响资格失效并退回对应里程碑。
- 对系统设计第 26 章做独立最终审计，只引用 M5-M8 已形成的安装、升级、恢复、容量和安全证据。
- 在 Release Candidate 上复跑最小发布套件、Soak 和最终安全检查，确认汇总证据未因最后变更失效。
- 由真实 DeepTalk 或指定外部调用方完成最终 REST/MCP 复验和发布签署，不把内部 Harness 冒充真实联调。
- 固化版本策略、镜像与依赖清单、Release Notes、部署/恢复手册和已知限制。

### 11.3 退出标准

- [ ] M5 至 M8 均为 `VERIFIED`，无开放 Release Blocker 或未处置 P1。
- [ ] 第 26 章发布验收矩阵全部通过，且每项引用同一候选版本的有效证据。
- [ ] 独立发布套件和外部调用方复验通过，发布签署不包含条件性“以后补测”。
- [ ] commit、镜像 digest、版本、证据索引、Runbook、已知限制和后续候选项完成评审。

### 11.4 非目标

- 不在发布资格阶段补做未经排期的新节点、Adapter 或基础设施。
- 不把未执行的测试、计划中的演练或协议级 mock 视为通过。

## 12. Post-v1 候选项

以下内容不是已承诺里程碑：

| 候选方向 | 当前候选 |
|---|---|
| 编排表达力 | `team`、`transform`、`subflow`、`emit`、动态派生、Map/Review/Vote 的完整 Runtime 与 Canvas 支持 |
| 生态接入 | A2A RemoteAgent、LangGraph、MAF、CrewAI、PydanticAI Adapter |
| 入站方式 | 配置文件与 CLI Adapter |
| 数据与记忆 | pgvector Knowledge/Memory、可选 Qdrant 后端 |
| 基础设施扩展 | 多区域 Artifact、Kafka Audit/Data Export、Kata 高风险 Runtime |
| 控制台优化 | 基于真实性能数据的路由拆包、离线/冲突体验和更完整的治理页面 |

候选项只有同时满足以下条件才升级为里程碑：

1. 有明确调用方和不可由现有能力完成的场景；
2. 有可量化目标和可执行验收；
3. 依赖的公共契约已经稳定；
4. 不阻塞当前 Release Blocker、P1 或前置里程碑；
5. 产品边界变化已同步系统设计。

## 13. 全局质量门禁

每个里程碑退出时按影响范围检查：

| 维度 | 最低要求 |
|---|---|
| 行为 | 固定端到端场景证明用户或系统结果，不以实现清单代替 |
| 契约 | REST、MCP、Schema、事件、数据库、Plan Hash 和错误语义兼容或有迁移说明 |
| 架构 | 领域纯净、应用服务复用、Workflow 确定性、I/O Activity 边界保持 |
| 一致性 | tenant/project、幂等、状态机、Outbox、审计、effect 和补偿不可绕过 |
| 测试 | 新行为有测试；执行相关静态、单元、集成、前端、故障或安全检查 |
| 证据 | 记录命令、结果、commit、CI run、环境和未执行项；变更后重跑受影响的前置资格 |
| 文档 | 产品/架构更新系统设计，实施状态更新本计划，公共接口/配置更新 README 和示例 |
| 收敛 | 删除确认无引用的旧路径；技术债进入开放门禁或候选项，不保留无限期双轨实现 |

## 14. 更新规则

1. 同一时间只允许一个主里程碑为 `IN_PROGRESS`。
2. 每次更新页首基线、当前焦点、唯一下一门禁和受影响的开放门禁。
3. `IMPLEMENTED` 必须有相关本地测试；`VERIFIED` 必须满足里程碑全部退出标准并绑定不可变证据。
4. 未执行、环境不具备或只做协议 mock 的测试必须明确记录，不能视为通过。
5. 已完成里程碑在下一次结构性更新时合并进能力基线，不在正文累积过程日志。
6. 关闭风险直接删除或并入能力证据；历史状态由 Git 保留。
7. 产品目标、系统边界或架构决策变化时同步系统设计；公共 API、配置和启动方式变化时同步 README 与 `.env.example`。
8. 下一步只写一个最高优先门禁；其他工作按依赖留在对应里程碑，避免“并行推进”掩盖阻塞。

## 15. 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-07-17 | 2.0 | 从第一性原理重构：将旧 M0-M4 合并为能力与候选基线，按不可变证据重置状态口径；默认延期 4 类未执行节点和配置/CLI；按契约、部署、恢复、容量、发布重新规划 M5-M9 |
| 2026-07-17 | 2.1 | 纳入业务智能体扩展 B1；记录 E0-E3 的 Capability Pack、Workbench、Blob、RuleSet 和确定性文件完整性校验本地实现证据，并将 E4-E5 置于 M6 生产资格之前 |
