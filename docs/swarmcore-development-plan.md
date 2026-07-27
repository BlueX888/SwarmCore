# SwarmCore 开发计划

| 属性 | 值 |
|---|---|
| 状态 | Living Document |
| 版本 | 3.1 |
| 最近更新 | 2026-07-27 |
| 已提交基线 | `eb75ac3`（受控 Tool 与有界编排） |
| 当前候选 | M3/M4、业务扩展 E0-E4、业务上下文/决策、业务资料库、能力中心统一化、发票一致性位于工作树 |
| 当前焦点 | M5 / G0；发票一致性 IA-E1 本地实现 |
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
| REST/MCP 与策略控制台 | IMPLEMENTED / LOCAL | E1、STRAT-DEL-1 | G0：远端 CI 与 Fake Agent E2E |
| 受控 Tool、Router、Loop | VERIFIED / LOCAL | `eb75ac3`，E2 | 持续回归 |
| 治理、安全和 Provider 候选 | IMPLEMENTED / LOCAL | E3 | G0、真实 K8s/Provider |
| Capability Pack、Workbench、文档智能 E0-E4 | IMPLEMENTED / LOCAL | BA-E4、BA-E4.1、WB-E1 | E5、真实 OCR/模型、环境级人工复核 |
| 能力中心统一化 | IMPLEMENTED / LOCAL | CC-E1 | G0、真实 Provider 资格 |
| 业务上下文与决策资产 | IMPLEMENTED / LOCAL | BCRP-E1 | G0；真实 OPA/Temporal 资格 |
| 业务资料库与运行文件快照 | IN_PROGRESS / LOCAL | DLIB-E1 | 完整本地回归、PostgreSQL/RLS/API 集成和 G0 |
| 合同七维后评价能力包 | IN_PROGRESS / LOCAL | CPE-E1、CPE-E2、CPE-E3、DLIB-E1 | 文件链替换后的完整回归；有效模型 Provider 凭据、二进制文档 OCR 与生产环境资格验收 |
| 独立偏差分析能力包 | VERIFIED / LOCAL | DA-E1、DA-E2 | 已完成 PostgreSQL、真实 Temporal/Agno/Kimi、人工审批、报告持久化与中文 PDF 页面渲染验收；图像型资料未配置 OCR，按策略归档且不进入计算选择 |
| 发票一致性校验能力包 | IMPLEMENTED / LOCAL | IA-E1 | 真实授权发票、官方查验人工/授权连接、Temporal/模型资格与 PostgreSQL 集成未验收 |
| 业务工作信息架构与九项规划扩展 | IMPLEMENTED / LOCAL | BW-E1、DA-E1、IA-E1 | 除文件完整性、偏差分析和发票一致性外，其余规划业务的真实执行链尚未实现 |
| 业务工作唯一入口与 Assessment 结果页 | IMPLEMENTED / LOCAL | BW-E2、DA-E1 | 其余七项规划业务仍为“规划中”；未执行 Playwright 与 PostgreSQL 集成 |
| 受控本地文件系统工具 | IMPLEMENTED / LOCAL | FS-E1 | 生产 Sandbox/gVisor 同构执行与卷同步仍属 G3；默认 fail-closed |

证据索引：

| ID | 已记录结果 | 边界 |
|---|---|---|
| E1 | 52 单元、8 集成、17 Vitest、21 Playwright、前端 lint/build、Ollama smoke | 本地；无合格远端 CI |
| FS-E1 | 四个 builtin filesystem 工具、SafePathResolver、共享 `assemble_tool_executors`、local/sandbox 模式边界、HIGH 写审批与 EffectJournal；Ruff、mypy（123 source files）、266 单元（1 skipped）、filesystem 定向 Vitest 1/1、相关文件 ESLint、Web build 通过 | 默认关闭；生产禁止 local；Sandbox 未返回声明结果时 fail closed；未执行真实 K8s/gVisor、Playwright e2e 与 PostgreSQL 集成；全量 `pnpm web:lint` 因工作树中既有无关前端文件失败 |
| E2 | Ruff、mypy、69 单元、10 PostgreSQL/Temporal 集成 | 已绑定 `eb75ac3` |
| E3 | Ruff、mypy、105 单元；项目配置集成；前端 lint、26 Vitest、33 Playwright、build | 未绑定提交；真实 Sandbox/ClamAV 未验收 |
| BA-E3 | Ruff、mypy、117 单元、13 PostgreSQL/Temporal/Blob 集成、27 Vitest、33 Playwright、前端 lint/build | 4 项环境依赖测试跳过 |
| BA-E4 | Ruff、mypy strict、130 单元；E4 定向 14 单元 | PostgreSQL/RLS 集成跳过；未接真实 OCR/模型 |
| BA-E4.1 | 能力包真实 StrategyVersion、依赖一致性、绑定配置 provenance；Ruff、mypy、169 单元、41 Vitest、Web lint/build | PostgreSQL 集成因未配置测试数据库跳过；Playwright 30/33，移动端波动用例单独重跑通过，2 项既有运行页截图基线差异未通过；真实 Temporal/模型链未验收 |
| BA-E4.2 | 自定义能力包绑定策略管理中的已发布 StrategyVersion，并预览冻结预算与 Agent/Tool 依赖；Ruff、mypy、170 单元、42 Vitest、Web lint/build、本地浏览器交互验收 | PostgreSQL/RLS 集成因未配置测试数据库跳过；未执行真实 Temporal/Agent/Tool 运行链 |
| CC-E1 | Ruff、mypy、165 单元、18 集成、33 Vitest、33 Playwright、Web lint/build | 未绑定提交/CI；未作真实 Provider 资格 |
| BCRP-E1 | Capability Pack v1/v2、BusinessObject/Case/Assessment、DecisionAsset、Connection/Resource/Snapshot 纵向闭环；Ruff、mypy、186 单元、5 项定向 PostgreSQL/RLS/API 集成、47 Vitest、33 Playwright、Web lint/build | 本地 Compose 与确定性 Fake Connector；未绑定提交/CI，未作真实 Vault/OPA/Temporal、外部连接器和生产健康投影资格 |
| CPE-E1 | `contract-post-evaluation@1.0.0`、五类资源绑定、七维确定性评分、关注项和 JSON/PDF 报告；Ruff、mypy、192 单元 | 2 项 PostgreSQL/API 集成因未配置测试数据库跳过；未执行 Temporal、外部文件/履约/偏差/发票/风险数据源和真实 Tool Worker 链 |
| CPE-E2 | `contract-post-evaluation@1.2.0`：五类绑定资源由 Tool Activity 真实读取并追加内容哈希快照、标准化合并后评分；业务能力包新增一键创建资源/绑定/合同对象/案件、执行轮询、七维结果与 PDF 下载工作台；Ruff、mypy、196 单元、49 Vitest、Web lint/build、本地 Temporal/Tool Worker 浏览器闭环 | 本地 Fake Connector 接收标准化 JSON；3 项 PostgreSQL 集成因未配置 `TEST_DATABASE_URL` 跳过；生产文件库、ERP、发票、风险系统连接器及真实 Secret/Vault 仍待资格验收 |
| CPE-E3 | `contract-post-evaluation@1.5.0`：工作台收敛为上传文本文件、自然语言定义流程、执行 Agent；新增后评价分析 Agent，后台自动创建一个上传资源并绑定五类槽位；浏览器验证完成文件选择、资源读取、Temporal Agent 节点提交 | 本地模型代理已启动，但现有 Provider 凭据返回 401，真实 Agent 最终输出未通过；PDF/Word/Excel OCR 尚未接入，不标记 VERIFIED |
| CPE-E4 | 业务能力包页面调整为项目配置面：统一呈现编排策略、Agent、工具、模型解析、权限和资源槽位，支持项目运行参数及资源绑定；移除上传文件、自然语言流程和直接执行入口，并取消侧栏硬编码具体业务 | VERIFIED：Web lint、54 Vitest、build 通过；本地浏览器确认能力包配置路由、真实绑定回显及页面无横向溢出；未重跑 Python 与集成测试（未修改后端） |
| WB-E1 | 已启用业务能力包新增独立工作台入口；v1 复用 WorkItem 执行，v2 自动建立 Manifest 必需 Subject、检查必需资源槽位并复用 Case Assessment，提交后进入统一 Run 详情 | Web lint、63 Vitest、build、工作台定向 Playwright 3/3 通过；全量 Playwright 27/33，6 项既有运行/能力中心用例因本地 API `127.0.0.1:8000` 未启动超时；未修改 Python，未重跑后端测试或真实 Kimi/Temporal/Tool Worker 链 |
| CC-E2 | Agent 项目配置投影为版本化 `agent://project/{id}@{revision}` 能力，进入统一 Readiness、REST/MCP 能力目录、直接运行和画布链路；项目 Agent 复用系统能力就绪投影，避免重复探测全部依赖；Agno Adapter 在任务执行时实例化 | VERIFIED：Ruff、mypy、221 单元、Agent 配置/能力中心定向 Vitest 24/24、Web lint/build 通过；全量 Vitest 74/75，1 项既有模型连接表单在并发执行时初始化时序失败（单文件重跑 12/12）；本地浏览器完成创建、目录可见、编辑保存、刷新后字段持久化验收；E2E 32/36，3 项既有能力中心脚本未关闭模态框而超时，1 项既有移动端画布拖拽位于视口外；PostgreSQL/API 集成因未配置 `SWARMCORE_TEST_DATABASE_URL` 跳过，未执行真实模型/Temporal 链 |
| BW-E1 | “业务工作”作为侧栏分类，保留工作总览并新增基础 AI 与评测、文件结构化、文件完整性、履约计划与采集、发票一致性、偏差分析、报告生成、调度校准、招采与供应商风控九项独立规划入口和详情骨架 | Web lint、84 Vitest、build 通过；九项统一标记“规划中”；未执行 Playwright、Python 或集成测试，未接入任何真实业务功能 |
| BW-E2 | 产品层移除“业务能力包”入口；BusinessWorkService 集中映射 `document-integrity→contract-integrity`、`contract-post-evaluation→contract-post-evaluation`；新增独立业务工作“合同后评价”，`report-generation` 保持规划中；新增 `/business-works`、`/settings`、`/workbench`、`/assessments/:id` 与旧 `/capability-packs*` 兼容重定向；办理成功优先进入 Assessment | Ruff、mypy、单元与 Web lint/test/build 通过；未执行 Playwright 与 PostgreSQL 集成；其余规划业务仍为“规划中” |
| DLIB-E1 | 业务资料库替换新产品调用链中的 Connection/Resource：复用 BlobObject/Artifact Gateway，新增不可变文件版本、业务对象关联、业务工作绑定、处理结果与 Assessment/Run 使用快照；`/documents` 为主路由，`/resources` 仅前端兼容重定向；REST/MCP 复用 DocumentLibraryService | Ruff、mypy（114 source files）、229 单元、80 Vitest、Web lint/build 通过，Alembic head 为 `0013_business_document_library`；5 项相关 PostgreSQL/RLS/API 集成因未配置 `SWARMCORE_TEST_DATABASE_URL` 跳过。只完成资料绑定和执行读取骨架，真实解析、OCR、抽取和人工确认能力未实现；旧 Connection/Resource ORM、migration 与 REST API 暂保留历史兼容 |
| DLIB-E2 | 通用业务资料接入与处理：UploadBatch、ProcessingRun/Profile、Parser/OCR/Classifier/Extractor Adapter、Schema 驱动人工确认、资料要求契约；资料库与业务工作台复用同一前端组件；`contract-integrity@2.1.0` 与 `contract-post-evaluation@1.7.0` 通过不同 Pack 配置接入，公共模块无业务 work key 硬编码 | 见本轮验证记录；PostgreSQL/RLS/Temporal 集成仍依赖环境 |
| CPE-E4 | `contract-post-evaluation@2.0.5`、策略 `generate@13`：8 类资料要求、最多 100 份冻结文件、4 个领域分析 Agent、证据复核与报告叙述 Agent、14 个 Tool、4 路并行、全量扫描后每域 Top 6 注入、Agent `node_only` 上下文隔离、资料覆盖/一致性/金额/发票/偏差/风险诊断、条件人工审批、v2 结果与 CJK PDF/JSON 持久化；配置页展示冻结 Agent/Tool 与分类数量 | VERIFIED / LOCAL：真实模型 Run `019f93dd-58a1-747b-bd46-c462917d9677` 冻结 35 份文件，6 个 Agent、25 个执行节点成功并完成人工审批；Evaluation `019f93dd-5892-7b8d-aafd-15a464b3ea64` 得分 84.55，七维结果及 JSON/PDF 已持久化，PDF 哈希 `1b05e8c5f42e70c52e9bde1b8b5e44c59cd851d9dc4ffe747e9835a3768084f1` 经文本提取与页面渲染核验。Ruff、mypy（129 个源文件）、304 单元、121 Vitest、Web lint/build 通过。PostgreSQL/Temporal 由本地真实运行覆盖，独立 pytest 集成套件仍依赖隔离测试数据库 |
| DA-E1 | `deviation-analysis@1.0.5`、策略 `execute@6`：10 类资料要求、确定性文件/基线选择与四类冻结哈希、6 个窄职责 Agent、14 个 Tool、时间/内容/成本计算、同口径历史趋势、AI 根因、仅 `PROPOSED` 的责任建议、条件人工审批、结构化 JSON/CJK PDF 幂等持久化；统一 REST/MCP/Workbench 和专用 Assessment 指标/趋势/责任视图 | VERIFIED / LOCAL：Crossrail 公开案例 2018、2019、2021、2022 四期真实 PostgreSQL/Temporal/Agno/Kimi 运行均为 `SUCCEEDED`，每期冻结 24 个不可变文件版本并完成人工审批、Finding、Audit、Outbox 和 JSON/PDF 持久化；最终趋势为 4 点，2022 时间偏差 1,262 天、成本偏差 £4.1bn（27.70%），责任输出保持 `PROPOSED / PENDING_CONFIRMATION`。中文 PDF 通过文本提取和 3 页渲染检查。验收清单见 `.tmp/business-data/deviation-analysis/crossrail-public-case/08-run-evidence/2026-07-26-real-runtime/final-verification.json`；本结果仅为公开案例本地运行验收，不构成法律责任认定 |
| DA-E2 | Crossrail 真实资料接入与四期历史回填：复核 21 份官方来源，上传 25 个版本，选择 24 个可解析版本；同一显式基线、配置和文件选择贯穿四期运行；原件、派生 Markdown、事实包、来源 URL、SHA-256 与派生关系留档 | VERIFIED / LOCAL：四期 `baselineHash=6fe0e0b724f0b789478720841f6e904b6fc688418834030a928cc7721fb8f1bc`、`configurationHash=808a5168ca05ad02b8cd4adcac95461dd7fbc197d18b8d67d0fb7a7f7d7540ad`；图像型完工跟踪表保留归档但未进入计算。Kimi token 用量已持久化；当前价格表缺少该 Provider 定价，因此美元成本记录为 0，但每期 `maxCostUsd=2` 预算门禁仍生效 |
| IA-E1 | `invoice-assurance@1.0.0`、策略 `assess@1`：8 类资料槽位、XML 优先解析、官方查验人工/授权两种模式（不伪造成功）、算术/主体/重复/商业匹配/付款门禁确定性 Tool、3 个窄职责 Agent、条件人工审批、结构化 JSON/CJK PDF 幂等持久化；BusinessWork 映射与 Assessment 结果分栏视图 | IMPLEMENTED / LOCAL：定向单元 `test_invoice_assurance*` 与 `test_business_work_service` 相关断言通过；Capability Pack 引用与策略编译通过。未执行全量 `uv run pytest`、Ruff/mypy、Vitest（本机 Application Control 阻断 grpc/rollup 原生库）、Playwright、PostgreSQL/Temporal 真实发票验收与官方查验资格 |
| STRAT-DEL-1 | 策略管理支持安全物理删除：仅 `ACTIVE` 且无 StrategyVersion/Run/Evaluation/能力包依赖快照的草稿策略可删；`GET delete-impact` + `DELETE` 返回稳定 blockers；列表/详情 Radix 确认对话框 | Ruff、mypy（115 source files）、247 单元、策略删除定向 Vitest 8/8、相关能力包 Vitest 12/12、Web lint/build 通过；`tests/integration/test_strategy_api_postgres.py::test_strategy_delete_impact_and_conservative_delete` 因未配置 `SWARMCORE_TEST_DATABASE_URL` 未执行；未执行 Playwright |

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
| 业务 | 合同七维后评价与独立偏差分析 Pack 已 IMPLEMENTED / LOCAL；招采一致性、供应商风险 Pack 仍为候选 |
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
| 2026-07-21 | 3.1 | 完成业务上下文、DecisionAsset、资源连接平面和 contract-integrity v2 的本地实现与定向验收；保留生产资格门禁 |
| 2026-07-22 | 3.1 | 能力中心模型页：未在 `SWARMCORE_MODEL_ROUTES` 登记的逻辑模型从目录隐藏（Registry 内置定义保留） |
| 2026-07-22 | 3.2 | 项目智能体成为可发现、可检查、可直接运行的版本化能力，REST/MCP 保持同一投影 |
| 2026-07-26 | 3.3 | 实现独立偏差分析能力包、确定性三维偏差/趋势、证据与责任复核、统一 Workbench 和结果视图 |
