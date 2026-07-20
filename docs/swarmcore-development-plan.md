# SwarmCore 开发计划

| 属性 | 值 |
|---|---|
| 状态 | Living Document |
| 版本 | 3.0 |
| 最近更新 | 2026-07-20 |
| 已提交基线 | `eb75ac3`（受控 Tool 与有界编排） |
| 当前候选 | M3/M4、业务扩展 E0-E4、能力中心统一化位于未提交工作树 |
| 当前焦点 | M5 / G0；B1 剩余 E5 |
| 唯一下一门禁 | G0：形成干净、不可变、CI 可复现的候选基线 |
| 架构事实源 | [SwarmCore 系统设计](./swarmcore-system-design.md) |

## 1. 文档规则

本文只维护当前状态、开放门禁、里程碑和证据，不重复系统设计、API 字段、数据库表或实现步骤。

状态口径：

| 状态 | 含义 |
|---|---|
| PLANNED | 只有范围和验收目标 |
| IN_PROGRESS | 已开始但未满足退出标准 |
| IMPLEMENTED | 代码完成且相关本地检查通过 |
| VERIFIED | 同一不可变版本在目标环境满足全部门禁 |

证据层级：`LOCAL` < `CI` < `STAGING` < `PRODUCTION`。高层级不能自动弥补低层级缺失的契约、单元或静态检查；代码变化后必须重跑受影响门禁。未执行、跳过和 Mock 不得写成通过。

## 2. 当前能力与证据

| 能力域 | 状态 | 证据 | 开放项 |
|---|---|---|---|
| 耐久执行与人工控制 | VERIFIED / LOCAL | `eb75ac3`；Temporal、状态、审批、输入、取消、重试 | 持续回归 |
| REST/MCP 与策略控制台 | IMPLEMENTED / LOCAL | E1 | G0：远端 CI 与 Fake Agent E2E |
| 受控 Tool、Router、Loop | VERIFIED / LOCAL | `eb75ac3`，E2 | 持续回归 |
| 治理、安全和 Provider 候选 | IMPLEMENTED / LOCAL | E3 | G0、真实 K8s/Provider |
| Capability Pack、Workbench、文档智能 E0-E4 | IMPLEMENTED / LOCAL | BA-E4、BA-E4.1 | E5、真实 OCR/模型、环境级人工复核 |
| 能力中心统一化 | IMPLEMENTED / LOCAL | CC-E1 | G0、真实 Provider 资格 |

证据索引：

| ID | 已记录结果 | 边界 |
|---|---|---|
| E1 | 52 单元、8 集成、17 Vitest、21 Playwright、前端 lint/build、Ollama smoke | 本地；无合格远端 CI |
| E2 | Ruff、mypy、69 单元、10 PostgreSQL/Temporal 集成 | 已绑定 `eb75ac3` |
| E3 | Ruff、mypy、105 单元；项目配置集成；前端 lint、26 Vitest、33 Playwright、build | 未绑定提交；真实 Sandbox/ClamAV 未验收 |
| BA-E3 | Ruff、mypy、117 单元、13 PostgreSQL/Temporal/Blob 集成、27 Vitest、33 Playwright、前端 lint/build | 4 项环境依赖测试跳过 |
| BA-E4 | Ruff、mypy strict、130 单元；E4 定向 14 单元 | PostgreSQL/RLS 集成跳过；未接真实 OCR/模型 |
| BA-E4.1 | 能力包真实 StrategyVersion、依赖一致性、绑定配置 provenance；Ruff、mypy、169 单元、41 Vitest、Web lint/build | PostgreSQL 集成因未配置测试数据库跳过；Playwright 30/33，移动端波动用例单独重跑通过，2 项既有运行页截图基线差异未通过；真实 Temporal/模型链未验收 |
| BA-E4.2 | 自定义能力包绑定策略管理中的已发布 StrategyVersion，并预览冻结预算与 Agent/Tool 依赖；Ruff、mypy、170 单元、42 Vitest、Web lint/build、本地浏览器交互验收 | PostgreSQL/RLS 集成因未配置测试数据库跳过；未执行真实 Temporal/Agent/Tool 运行链 |
| CC-E1 | Ruff、mypy、165 单元、18 集成、33 Vitest、33 Playwright、Web lint/build | 未绑定提交/CI；未作真实 Provider 资格 |

以上是历史记录，不表示本次文档更新重新执行了测试。

## 3. 开放门禁

| ID | 优先级 | 缺口 | 关闭条件 | 里程碑 |
|---|---|---|---|---|
| G0 | Release Blocker | 候选实现未形成不可变提交；CI 未覆盖完整后端、前端和 Fake Agent E2E | 干净检出全绿，证据绑定 commit 与 CI run | M5 |
| G1 | P1 | Schema 仍声明 `team/transform/subflow/emit`，但 Runtime 不可执行 | v1 Schema/Catalog/Compiler/Canvas/文档统一表达支持范围或完成实现 | M5 |
| G2A | P1 | SSE 游标、gap、背压、410、断线续传缺少完整契约证据 | CI 契约和客户端重连测试通过 | M5 |
| G2B | P1 | 真实 JetStream、Event Gateway、Ingestor 链路缺少生产同构证据 | Staging 验证发布、重投递、慢消费者和恢复 | M6 |
| G3 | P1 | K8s、Sandbox、ClamAV、工作负载身份、mTLS、Provider 主要是本地/协议证据 | 生产同构环境安全与 Provider E2E | M6 |
| G4 | P1 | Replay、Continue-As-New、故障、备份恢复和 RPO/RTO 证据不足 | 故障与恢复套件、Runbook 演练通过 | M7 |
| G5 | P2 | 无容量、租户公平性、背压、Autoscaling、HA 和 SLO 测量 | 明确负载模型下取得可复现结果 | M8 |
| G6 | P2 | Web 主 Chunk 大于 500 KiB | 先测量；影响体验时再拆分 | 候选优化 |

## 4. 里程碑

依赖顺序：M5 → B1 → M6 → M7 → M8 → M9。除 P0 安全问题外，不跨越前置门禁扩大产品表面积。

### M5：v1 契约与候选基线

状态：`IN_PROGRESS`；目标证据：`CI`。

结果：从干净检出可复现 v1 核心闭环，公共契约不夸大能力。

退出标准：

- G0、G1、G2A 关闭；
- REST/MCP 使用同一应用服务，inline Spec 到 RunResult 完成真实闭环；
- 当前 9 类节点、状态、控制、幂等、Outbox、Tool effect 和租户隔离通过回归；
- migration、OpenAPI、事件和前端类型一致；
- 同一 commit 的 Ruff、mypy、单元、集成、Web lint/test/build、Playwright 与 Fake Agent E2E 通过。

### B1：通用业务智能体扩展

状态：`IN_PROGRESS`；目标证据：`CI`。E0-E4 已本地实现，剩余 E5。

结果：Capability Pack、Workbench、Blob、RuleSet、Evaluation/Finding/Report 和文档智能形成通用闭环，并由非文档类工单分诊能力包证明无核心硬编码。

退出标准：

- 工单分诊不增加 migration、核心 API、Workflow 状态或业务专用通用字段；
- 两个 Pack 可并存、独立升级、禁用后历史可读；
- REST/MCP、幂等、RLS、Outbox、Blob、人工复核和报告通过 CI；
- 真实 OCR/模型资格仍归 M6，不以本地 Fake 代替。

后续合同履约、发票、偏差、报告、招采和供应商风险能力遵循“五层三横切”，默认通过共享 Provider/Tool 和 Capability Pack 扩展，不为每个 Agent 建立独立服务。它们是 Post-v1 候选，不计入 B1 完成范围。

### M6：单集群生产资格

状态：`PLANNED`；目标证据：`STAGING`。

结果：同一候选镜像可在生产同构 Kubernetes 安全部署、升级、观测和回滚。

退出标准：G2B、G3 关闭；PostgreSQL/Temporal/NATS/S3/Vault/OPA/ClamAV/Provider 打通；mTLS、工作负载身份、RLS、Sandbox 和 Secret 轮换通过；Dashboard、告警、升级回滚和最小 HA 验证通过。

### M7：故障、安全与恢复资格

状态：`PLANNED`；目标证据：`STAGING`。

结果：关键故障、安全边界和备份恢复可重复验证。

退出标准：G4 关闭；Workflow Replay/Continue-As-New、Projection/Outbox/Event/Webhook 重放、Provider/Worker/基础设施故障、跨租户与恶意文件场景通过；RPO ≤ 5 min、RTO ≤ 30 min 或以证据修订目标；Runbook 由非实现者复现。

### M8：容量、背压与 SLO 资格

状态：`PLANNED`；目标证据：`STAGING`。

结果：容量边界、部署规格和饱和行为有可复现测量。

退出标准：G5 关闭；租户/项目配额、Task Queue、Provider 限流、Tool/Sandbox 容量、Autoscaling、HA、慢消费者和 Soak Test 通过；饱和时有界排队且不突破预算或租户隔离。

### M9：v1 发布门禁

状态：`PLANNED`；目标证据：`STAGING`。

结果：从 M8 的同一不可变 commit 和镜像产生 Release Candidate，不在本阶段增加能力。

退出标准：M5-B1-M8 均 VERIFIED；无 Release Blocker/P1；外部调用方完成 REST/MCP 复验；版本、镜像 digest、Schema、migration、Release Notes、部署和恢复手册完成签署。

## 5. Post-v1 候选

| 方向 | 候选项 |
|---|---|
| 编排 | `team`、`transform`、`subflow`、`emit`、动态派生、Map/Review/Vote |
| 生态 | A2A RemoteAgent、其他 Agent SDK Adapter、配置/CLI 入站 |
| 数据 | 完整 Knowledge/Memory、必要时 Qdrant |
| 业务 | 履约、发票、偏差、七维报告、招采一致性、供应商风险 Pack |
| 基础设施 | 多区域 Artifact、Kafka 导出、Kata 高风险 Runtime |
| 前端 | 以真实性能数据驱动的拆包和治理体验 |

候选项只有在有明确调用方、不可由现有能力完成、契约稳定、验收可量化且不阻塞开放门禁时才能升级为里程碑。

## 6. 全局门禁与更新规则

每次交付按影响范围检查：行为闭环、公共契约、领域纯净、Workflow 确定性、tenant/project、幂等、状态机、Outbox、审计、测试、证据和文档。

更新规则：

1. 同一时间只保留一个主里程碑为 `IN_PROGRESS`；B1 作为 M5/M6 之间的限定扩展单独跟踪。
2. 页首只写当前焦点和唯一下一门禁；关闭风险从活动列表删除，历史交给 Git。
3. 产品边界或架构变化更新系统设计；实施状态和证据只更新本文；公共接口或配置变化同步 README 与 `.env.example`。
4. 不新增临时实施计划文档；需要展开的工作使用 issue/任务，稳定结论合并回两份事实源。

## 7. 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-07-17 | 2.x | 重构 M5-M9 门禁并纳入业务智能体扩展 B1 |
| 2026-07-20 | 3.0 | 合并业务扩展、兼容性和能力中心计划，压缩为状态、门禁、证据与里程碑事实源 |
