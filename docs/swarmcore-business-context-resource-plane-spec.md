# SwarmCore 业务上下文、决策资产与资源连接实施 Spec

> 状态：IMPLEMENTED / LOCAL（2026-07-21；生产连接器、真实 Vault/OPA/Temporal 与 CI 资格不在本状态内）
>
> 目标读者：负责实现、评审和验收的 AI/工程师
>
> 事实来源：`docs/swarmcore-system-design.md`、`docs/swarmcore-development-plan.md`、
> `docs/swarmcore-capability-center-implementation-plan.md`、仓库根目录 `AGENTS.md`
>
> 本文同时保留实施契约与本地验收范围；`VERIFIED` 仍要求不可变 commit、CI 和生产同构环境证据。

## 1. 执行命令

实现者必须严格遵守以下顺序：

1. 开始每个 Phase 前重新阅读根目录 `AGENTS.md` 和本文涉及的事实来源。
2. 检查工作区已有修改，保留用户改动，不覆盖正在进行的前端删除和 migration。
3. 每个 Phase 先补契约或失败测试，再实现，再运行该 Phase 的验证命令。
4. 一个 Phase 未通过验收，不得开始依赖它的下一 Phase。
5. 数据库只新增 migration，不修改 `0001`—当前 Alembic head 的历史 migration。
6. REST 与 MCP 必须调用同一套应用服务，不建立平行业务逻辑。
7. Temporal Workflow 只处理确定性控制和稳定引用；网络、数据库、模型、文件与连接器 I/O 必须放入 Activity 或受控 Tool。
8. 不得使用 Python `eval`，不得让 Agent 直接访问数据库、Secret 或外部 Endpoint。
9. 不得把未执行的检查写成已通过；只有实现和对应测试完成后才能更新开发计划状态。

## 2. 背景与问题

SwarmCore 已有以下通用闭环：

- `CapabilityPack/CapabilityPackVersion/ProjectCapabilityBinding`；
- `WorkItem/WorkItemRevision/WorkItemAttachment`；
- `Evaluation/Run/Finding/FindingAction/Report`；
- `RuleSet/RuleSetDraft/RuleSetVersion`；
- Blob、Artifact、文档抽取、Strategy、Registry、Readiness、Runtime、审计和 Outbox。

这些模型已经能够支撑单一业务事项执行，但不足以稳定支撑合同、发票、履约、供应商风险等多个智能体共享长期业务语义：

1. `WorkItem.payload` 同时承担案件输入和业务对象事实，无法清晰区分现实对象与处理过程。
2. 一个案件可能关联多个对象，例如发票校验同时关联合同、订单、发票、到货和付款凭证。
3. `RuleSet` 目前偏向单一规则文档，缺少通用决策资产类型、测试和每次决策执行记录。
4. Capability Pack 只能保存普通 `configuration`，不能声明并校验决策槽位和外部资源槽位。
5. 外部连接缺少“连接定义、项目实例、资源绑定、运行快照、健康状态”的统一模型。
6. Run 是一次技术执行，不能代替长期 Case、业务对象版本和人工处理历史。

## 3. 目标

本 Spec 要实现以下结果：

1. 增加“业务上下文与事实层”，让多个能力包围绕稳定、版本化的业务对象协作。
2. 把现有 WorkItem 产品语义收敛为 Case，把 Evaluation 产品语义收敛为 Assessment，同时保持存储、API 和事件兼容。
3. 把现有 RuleSet 应用语义扩展为 DecisionAsset，支持确定性发布、测试、绑定和执行留痕。
4. 增加“资源与连接平面”，安全管理连接、资源目录、能力包绑定、快照、血缘和就绪状态。
5. 通过 Capability Pack v2 声明 Case、Subject、Decision Slot 和 Resource Slot，不把项目资源、Secret 或可变连接写进不可变 Manifest。
6. 用 `contract-integrity` 完成一个真实纵向闭环，证明对象、Case、决策、资源、评估、问题、复核和报告能够协同。

## 4. 非目标

本次不得实现以下内容：

- 不建设完整知识图谱、图查询语言或用户可编程 Ontology Designer。
- 不使用万能 EAV 表逐字段保存合同、发票和供应商属性。
- 不把 SwarmCore 变成合同、财务、采购或供应商主数据的权威来源系统。
- 不物理重命名或删除 `work_items`、`evaluations`、`rule_sets` 及其现有 API。
- 不将业务 DecisionAsset 与 OPA 安全治理 Policy 合并。
- 不将业务规则退化为 Prompt 或非版本化知识库文本。
- 不建设第二套 Secret、ACL、Artifact、Blob、审计、Outbox 或 Runtime。
- 不让 Capability Pack Manifest 保存 URL、数据库密码、Token、Secret 值或项目连接实例 ID。
- 不为九类业务智能体分别创建独立微服务。

## 5. 固定术语与不变量

### 5.1 术语

| 产品术语 | 当前兼容模型 | 定义 |
|---|---|---|
| BusinessObject | 新增 | 合同、发票、供应商、招标项目等现实业务对象 |
| BusinessObjectVersion | 新增 | 业务对象在某一时点的不可变结构化事实快照 |
| Case | `WorkItem` | 围绕一个或多个业务对象开展的检查、评估或风险事项 |
| CaseRevision | `WorkItemRevision` | Case 输入、Subject 和附件的不可变修订 |
| Assessment | `Evaluation` | 对某一 CaseRevision 使用冻结依赖执行的一次业务评估 |
| Run | `Run` | 实现 Assessment 的一次技术执行 |
| DecisionAsset | `RuleSet` | 检查清单、决策表、表达式或阈值配置等业务决策资产 |
| DecisionVersion | `RuleSetVersion` | 可执行、不可变、带哈希的已发布决策版本 |
| DecisionExecution | 新增 | 一次决策调用的输入、输出、命中规则和版本留痕 |
| ConnectorDefinition | Registry 新增契约 | 平台支持的连接器类型和能力，不包含项目凭据 |
| Connection | 新增 | 某 tenant/project 对连接器的配置实例 |
| ResourceDefinition | 新增 | 连接下可绑定的逻辑资源，例如目录、API、表或知识库 |
| ResourceBinding | 新增 | 项目能力包的 Resource Slot 与逻辑资源之间的绑定 |
| ResourceSnapshot | 新增 | 某次 Assessment 实际读取或写入的资源版本与证据 |

### 5.2 必须保持的不变量

1. `BusinessObject != Case != Assessment != Run`。
2. 一个 Case 可以关联多个 BusinessObject；一个 BusinessObject 可以参与多个 Case。
3. CaseRevision、BusinessObjectVersion、DecisionVersion 和 ResourceSnapshot 均为不可变事实。
4. Report 是 Assessment 结果的投影，不是业务事实的唯一来源。
5. DecisionVersion 发布后不得修改；修改必须发布新版本。
6. Connection 可更新，但每次更新必须产生不可变 ConnectionVersion。
7. Assessment 必须冻结 CaseRevision、Subject ObjectVersion、CapabilityPackVersion、StrategyVersion、DecisionVersion、输入文件哈希和连接版本。
8. 外部资源内容无法合法持久化时，ResourceSnapshot 仍须记录版本、ETag/哈希、获取时间和 `NON_REPLAYABLE` 原因。
9. 人工改判不得覆盖原始 AI/规则输出，只能追加 Review/FindingAction/Resolution 记录。
10. 所有数据访问同时保留 tenant/project 应用过滤与 PostgreSQL RLS。

## 6. 目标架构

```text
业务场景与 Capability Pack
        ↓
业务上下文与事实层
BusinessObject / Version / Relation / Case / Subject / Finding
        ↓
领域智能体与原子工具
        ↓
Model / Provider
        ↓
Runtime / Temporal / Run

横切：资源、连接、数据与证据
横切：质量评测与人工复核
横切：安全治理与可观测
```

该图是职责分层，不是强制调用链。确定性决策、偏差计算和资源读取可以由 Runtime 直接调度 Tool，不必经过 Agent。

## 7. 领域与持久化模型

### 7.1 BusinessObject

新增 `business_objects`：

| 字段 | 类型 | 约束 |
|---|---|---|
| id | UUID | PK |
| tenant_id | UUID | 必填，RLS |
| project_id | UUID | 必填，RLS，FK Project |
| object_type | varchar(128) | 小写 kebab-case，例如 `contract`、`invoice` |
| canonical_key | varchar(256) | 项目内稳定业务键 |
| lifecycle | varchar(32) | `ACTIVE/ARCHIVED` |
| current_version | int | 从 1 开始 |
| created_at/updated_at | timestamptz | 必填 |

约束与索引：

- unique `(project_id, object_type, canonical_key)`；
- unique `(tenant_id, project_id, id)`；
- index `(project_id, object_type, lifecycle, updated_at)`。

`canonical_key` 由调用方或 Capability Pack 生成，不得用可变显示名称代替。不同外部系统的标识保存在版本化数据中的 `externalKeys`，不为每个来源增加核心列。

### 7.2 BusinessObjectVersion

新增 `business_object_versions`：

| 字段 | 类型 | 约束 |
|---|---|---|
| id | UUID | PK |
| tenant_id/project_id | UUID | 必填，RLS |
| business_object_id | UUID | 复合 FK 到 BusinessObject |
| version | int | 对象内递增 |
| schema_ref | varchar(256) | 必须是不可变 `schema://...@version` |
| data | JSONB | 通过 schema_ref 校验后的结构化数据 |
| data_hash | char(64) | canonical JSON SHA-256 |
| provenance | JSONB | 来源、资源快照、模型、Prompt、Agent、Tool、Schema 版本 |
| effective_at | timestamptz | 业务事实生效时间，可空 |
| recorded_by | varchar(256) | 必填 |
| recorded_at | timestamptz | 必填 |

约束与行为：

- unique `(business_object_id, version)` 和 `(business_object_id, data_hash)`；
- 表级 immutability trigger，禁止 UPDATE/DELETE；
- 创建新版本与更新 `business_objects.current_version` 必须在同一事务中完成；
- 相同 `data_hash` 的幂等更新返回已有版本，不产生重复版本；
- `data` 默认不得超过 256 KiB，超限内容进入 Artifact，`data` 只保存结构化摘要和 ArtifactRef。

不得创建通用 `facts(name, value)` EAV 表。合同义务、里程碑、发票明细等需要强约束或高频聚合的数据，由对应 Capability Pack 后续新增领域扩展表，并通过 `business_object_id` 关联。

### 7.3 BusinessObjectRelation

新增不可变 `business_object_relations`：

| 字段 | 定义 |
|---|---|
| source_object_id/target_object_id | 两端对象，必须处于相同 tenant/project |
| source_version_id/target_version_id | 形成关系时使用的对象版本 |
| relation_type | 例如 `contract-has-invoice`、`invoice-evidenced-by-delivery` |
| assertion_state | `ACTIVE/RETRACTED`，用于追加式修正或撤销 |
| valid_from/valid_to | 业务有效时间，可空 |
| evidence | 符合 EvidenceRef Schema 的数组 |
| supersedes_relation_id | 修正旧关系时指向旧断言，可空 |
| content_hash | 规范化关系内容哈希 |
| created_by/created_at | 创建人和时间 |

关系只追加，不原地修改。撤销或修正关系时新增一条带 `supersedes_relation_id` 的断言；撤销记录使用 `RETRACTED`。应用服务查询默认返回每条关系链最新且状态为 `ACTIVE` 的有效断言。

### 7.4 EvidenceRef

第一阶段不新增多态 Evidence 表。Registry 中新增并复用版本化 `EvidenceRef` JSON Schema：

```json
{
  "source": {
    "kind": "BLOB | ARTIFACT | RESOURCE_SNAPSHOT",
    "ref": "blob://... | artifact://... | resource-snapshot://...",
    "contentHash": "sha256"
  },
  "locator": {
    "page": 1,
    "bbox": [0.1, 0.2, 0.3, 0.4],
    "chunkId": "optional",
    "table": "optional",
    "row": 1,
    "column": 2
  },
  "excerptHash": "optional-sha256",
  "observedAt": "RFC3339"
}
```

原文片段包含敏感内容时不得写入事件、日志或审计；需要展示时通过受权 Artifact/Blob 读取。

### 7.5 Case 与 Subject

现有 `WorkItem/WorkItemRevision` 继续作为 Case/CaseRevision 的兼容存储，不重命名表。

新增不可变 `work_item_subjects`，每条记录绑定到一个 CaseRevision：

| 字段 | 定义 |
|---|---|
| work_item_id/work_item_revision_id | Case 及其修订 |
| business_object_id/business_object_version_id | 冻结的 Subject 与版本 |
| role | `PRIMARY/COMPARISON/EVIDENCE/RELATED` |
| subject_key | Pack 内稳定名称，例如 `contract`、`invoice` |
| created_at | 创建时间 |

约束：

- unique `(work_item_revision_id, subject_key, business_object_id)`；
- 至少一个 `PRIMARY` Subject，除非 Capability Pack v2 明确声明 `subjectsRequired=false`；
- 更新 Case payload、owner、附件或 Subjects 时必须创建新的 WorkItemRevision；
- 复制修订附件时同时复制 Subject 绑定并默认保留原对象版本；只有请求明确更新 Subject 时才冻结新版本；
- Assessment 始终使用 WorkItemRevision 上的对象版本，不读取对象的后来版本。

### 7.6 ReviewTask 兼容投影

第一阶段不再建立一套与 Finding 重复的人工任务状态机。产品层的 ReviewTask 由现有事实投影：

- `Finding` 表示需要处理的问题及当前状态；
- `FindingAction` 表示确认、分派、豁免、解决、重新打开和人工改判历史；
- 当前 assignee、期限和最后处理意见由最新有效 FindingAction 投影；
- `qualityFlags` 包含 `REVIEW_REQUIRED` 或决策结果要求人工处理时创建/重开 Finding；
- 待办中心查询该投影，不复制 Finding 状态。

只有后续出现“不依赖 Finding 的独立人工任务”并有真实查询需求时，才允许通过新 ADR 引入独立 `review_tasks` 表。

### 7.7 DecisionAsset 兼容模型

第一阶段不新建与 RuleSet 重复的主表：

- `RuleSet` 作为 DecisionAsset 存储；
- `RuleSetDraft` 作为 DecisionDraft；
- `RuleSetVersion` 作为 DecisionVersion；
- 新应用服务和 API 使用 Decision 术语；旧 RuleSet API 保留兼容。

Decision Draft/Version 的 `rules` 接受以下规范化信封，同时继续读取 legacy 规则文档：

```json
{
  "apiVersion": "swarmcore.io/decision/v1",
  "kind": "DecisionAsset",
  "type": "CHECKLIST | DECISION_TABLE | EXPRESSION | THRESHOLD",
  "engine": "swarmcore.rules.v1",
  "inputSchema": "schema://contract/integrity-input@1",
  "outputSchema": "schema://contract/integrity-output@1",
  "definition": {},
  "tests": [
    {"name": "missing-required-document", "input": {}, "expected": {}}
  ]
}
```

规则：

- 发布前必须完成 Schema 校验、引擎白名单校验和全部 TestCase；
- `EXPRESSION` 只能使用项目批准的确定性表达式语言，禁止 Python `eval`；
- 规范化、哈希和匹配必须在服务端完成；
- legacy 文档由兼容解析器映射为 `CHECKLIST + swarmcore.rules.v1`，不得批量改写历史版本；
- DecisionVersion 的 input/output schema、engine、definition 和 tests 全部进入 content hash。

### 7.8 Capability Decision Binding

新增 `project_capability_decision_bindings`：

| 字段 | 定义 |
|---|---|
| project_capability_binding_id | 目标项目能力包绑定 |
| slot | Capability Pack v2 声明的决策槽位 |
| rule_set_version_id | 已发布 DecisionVersion |
| content_hash | 绑定版本哈希冗余，用于快速校验 |
| bound_by/bound_at | 操作者和时间 |

同一项目能力包绑定的同一 `slot` 只能有一个当前绑定。重新绑定必须审计；历史 Assessment 通过下述冻结表保持原版本。

新增不可变 `evaluation_decisions`：

- `evaluation_id`；
- `slot`；
- `rule_set_version_id`；
- `decision_content_hash`；
- `input_schema_ref/output_schema_ref/engine`；
- unique `(evaluation_id, slot)`。

### 7.9 DecisionExecution

新增不可变 `decision_executions`：

| 字段 | 定义 |
|---|---|
| evaluation_decision_id | 冻结的 Assessment 决策依赖 |
| run_id/task_id/trace_id | 技术执行关联 |
| execution_key/attempt | 逻辑调用幂等键和实际尝试序号 |
| status | `SUCCEEDED/FAILED` |
| input_snapshot | 小型脱敏 JSON，可空 |
| input_artifact_id | 大型或敏感输入引用，可空 |
| input_hash | 必填 |
| output | 小型结构化 JSON，可空 |
| output_artifact_id | 大型输出引用，可空 |
| output_hash | 成功时必填 |
| matched_rule_ids | JSON 数组 |
| duration_ms | 非负整数 |
| executed_at | 时间 |

输入和输出均遵守 256 KiB 内联上限。失败记录稳定错误码和脱敏摘要，不记录 Secret 或原始文件正文。
unique `(evaluation_decision_id, execution_key, attempt)`；Activity 在写入成功后重试时必须返回已有记录，不能制造重复执行事实。

### 7.10 ConnectorDefinition

`ConnectorDefinition` 是 Registry 中的不可变定义，引用格式：

```text
connector://{namespace}/{name}@{version}
```

至少声明：

- 支持的协议和资源种类；
- `READ/WRITE/SUBSCRIBE` 能力；
- 配置 JSON Schema；
- 所需 Secret 类型，但不包含 Secret 值；
- 健康检查能力；
- 默认 Tool 风险等级、幂等和恢复要求；
- executor 标识和允许环境。

Connector 注册不等于就绪；没有 executor、Secret、策略授权或健康结果时必须返回 `NOT_READY`。

### 7.11 Connection 与 ConnectionVersion

新增 `connections` 和不可变 `connection_versions`。

`connections` 保存：tenant/project、name、connector_ref、lifecycle、current_version、时间戳。

`connection_versions` 保存：

- `connection_id/version`；
- 通过 Connector Schema 校验后的非秘密 `configuration`；
- `credential_ref`，只允许 Vault/Secret Manager 引用；
- `policy_ref`；
- `configuration_hash`；
- `created_by/created_at`。

任何 endpoint、scope、credential_ref 或非秘密配置变化都创建新版本。Secret 实际值永不进入 PostgreSQL、Manifest、事件、日志和 Artifact 元数据。

### 7.12 ResourceDefinition 与 ResourceBinding

新增 `resource_definitions`：

- tenant/project、connection_id；
- `resource_kind`：`DOCUMENT_COLLECTION/API/DATABASE_TABLE/KNOWLEDGE_BASE/EVENT_STREAM/OBJECT_STORE/OUTPUT_TARGET`；
- name、logical locator、media/schema ref、sensitivity、lifecycle；
- locator 是经过 Connector Schema 校验的逻辑路径，不得包含凭据；
- unique `(project_id, connection_id, name)`。

新增 `capability_resource_bindings`：

- `project_capability_binding_id`；
- `slot`；
- `resource_definition_id`；
- `access_mode`：`READ/WRITE/SUBSCRIBE`；
- 非秘密 `mapping_configuration`；
- `bound_by/bound_at`；
- unique `(project_capability_binding_id, slot)`。

绑定不得提升 ConnectorDefinition 声明的能力，也不得绕过 OPA。写资源必须通过 L2/L3 Tool 的审批、幂等、补偿或人工恢复机制。

### 7.13 ResourceSnapshot 与 ResourceHealth

新增不可变 `resource_snapshots`：

- evaluation_id、slot、resource_definition_id、稳定 `snapshot_key`；
- connection_version_id；
- direction：`INPUT/OUTPUT`；
- observed_version、etag、content_hash、retrieved_at；
- artifact_id/blob_id，可空且不能同时滥用；
- replayability：`REPLAYABLE/REFERENCE_ONLY/NON_REPLAYABLE`；
- non_replayable_reason，可空；
- metadata，必须脱敏；
- unique `(evaluation_id, slot, snapshot_key)` 保证幂等；`observed_version/content_hash` 允许外部系统无法提供时为空，但必须说明 replayability。

上传 Blob 已由 `BlobObject.sha256` 提供内容事实，ResourceSnapshot 只保存对 Blob 的引用和当次使用语义，不复制文件字节。

`ResourceHealth` 是按 tenant/project/environment 计算的动态投影，不写回 Connector Registry 或不可变版本。当前状态可以短 TTL 缓存；历史趋势进入 Metrics/Trace，不再建立另一套监控事实库。

## 8. Capability Pack v2 契约

### 8.1 兼容要求

- `swarmcore.io/v1` Manifest 必须继续解析和运行；
- v1 `workItemType/workItemSchema/rules` 由服务端适配为 Case 和一个 legacy Decision Slot；
- 新能力使用 `swarmcore.io/v2`；
- 禁止原地修改已发布 v1 Pack；迁移必须发布新的 v2 PackVersion；
- Registry 引用正则增加 `connector`，但项目 Connection/Resource ID 不属于 Manifest 引用。

### 8.2 v2 示例

```json
{
  "apiVersion": "swarmcore.io/v2",
  "kind": "CapabilityPack",
  "metadata": {"name": "contract-integrity", "version": "2.0.0"},
  "spec": {
    "case": {
      "type": "contract-integrity-check",
      "schema": "schema://contract/integrity-case@2",
      "subjectsRequired": true,
      "subjectRoles": [
        {"key": "contract", "objectType": "contract", "role": "PRIMARY", "min": 1, "max": 1},
        {"key": "attachments", "objectType": "contract-document", "role": "EVIDENCE", "min": 1}
      ]
    },
    "inputSchema": "schema://contract/integrity-input@2",
    "outputSchema": "schema://contract/integrity-output@2",
    "strategies": {"execute": "strategy://contract-integrity/validate@2"},
    "agents": ["agent://document/extractor@2"],
    "tools": ["tool://document/parse@2", "tool://rules/evaluate@2"],
    "decisions": [
      {
        "slot": "document-checklist",
        "required": true,
        "inputSchema": "schema://contract/checklist-input@2",
        "outputSchema": "schema://contract/checklist-output@2",
        "allowedTypes": ["CHECKLIST", "DECISION_TABLE"]
      }
    ],
    "resources": [
      {
        "slot": "contract-files",
        "required": true,
        "resourceKinds": ["DOCUMENT_COLLECTION", "OBJECT_STORE"],
        "accessMode": "READ"
      },
      {
        "slot": "report-output",
        "required": false,
        "resourceKinds": ["OUTPUT_TARGET", "OBJECT_STORE"],
        "accessMode": "WRITE"
      }
    ],
    "report": {"template": "report://contract/integrity@2"},
    "permissions": ["contract.read", "document.read", "finding.write"],
    "events": {"namespace": "capability.contract-integrity"},
    "ui": {"viewDefinition": "view://contract-integrity/case@2"}
  }
}
```

### 8.3 发布与启用校验

发布 PackVersion 时必须：

1. 校验 Manifest、所有版本化 Registry Ref 和禁止代码入口；
2. 编译并冻结 StrategyVersion、Spec/Plan Hash、Agent/Tool/Model 依赖；
3. 校验 Decision/Resource Slot key 唯一；
4. 校验 Slot Schema 与 Strategy 节点输入输出兼容；
5. 把 Slot 契约写入 CapabilityPackVersion dependency snapshot。

项目启用 PackVersion 时必须：

1. 解析全部必需 Decision Slot 和 Resource Slot；
2. DecisionVersion 必须为 `PUBLISHED`，类型和 Schema 与 Slot 兼容；
3. ResourceDefinition、ConnectionVersion、Secret 租约、策略和 executor 必须就绪；
4. 可选 Slot 未绑定时写入 warning，必需 Slot 未绑定时阻止启用；
5. `configuration` 只保存普通运行参数，不再夹带 DecisionVersion、Resource ID 或 Secret；
6. 失败一次性返回全部稳定 blocker，不允许逐个试错。

## 9. 应用服务边界

新增或扩展以下应用服务，REST、MCP、Worker 必须复用：

| 服务 | 职责 |
|---|---|
| `BusinessObjectService` | 对象创建、版本、关系、Schema、哈希、幂等、查询 |
| `CaseService` | Workbench 的 Case 术语适配、Subject 修订、Assessment 创建 |
| `DecisionAssetService` | RuleSet 兼容解析、验证、测试、发布和查询 |
| `DecisionExecutionService` | 冻结 DecisionVersion，写入决策执行留痕 |
| `ConnectionService` | Connection/Version、Schema、SecretRef、审计 |
| `ResourceCatalogService` | ResourceDefinition 列表和生命周期 |
| `CapabilityBindingService` | Decision/Resource Slot 绑定和完整性校验 |
| `ResourceSnapshotService` | 快照幂等、重放语义、Artifact/Blob 引用 |
| `ResourceReadinessService` | executor、Secret、Policy、Health 聚合 |

不得在 FastAPI route、MCP dispatch 或 React 中重写上述业务规则。

## 10. REST 与 MCP 契约

### 10.1 新 REST 资源

在现有 `/v1/projects/{project_id}` 范围下增加：

```text
POST   /business-objects
GET    /business-objects
GET    /business-objects/{object_id}
POST   /business-objects/{object_id}/versions
POST   /business-object-relations
GET    /business-objects/{object_id}/relations

POST   /cases
GET    /cases
GET    /cases/{case_id}
PATCH  /cases/{case_id}
POST   /cases/{case_id}:assess
GET    /cases/{case_id}/assessments
GET    /cases/{case_id}/findings

POST   /decision-assets
PATCH  /decision-assets/{asset_id}/draft
POST   /decision-assets/{asset_id}/draft:validate
POST   /decision-assets/{asset_id}/draft:publish
GET    /decision-assets/{asset_id}/versions

POST   /connections
GET    /connections
GET    /connections/{connection_id}
POST   /connections/{connection_id}/versions
POST   /connections/{connection_id}:test
POST   /resources
GET    /resources
GET    /resources/{resource_id}

PUT    /capability-packs/{version_id}/decision-bindings/{slot}
PUT    /capability-packs/{version_id}/resource-bindings/{slot}
GET    /capability-packs/{version_id}/bindings
GET    /assessments/{assessment_id}/resource-snapshots
GET    /assessments/{assessment_id}/decision-executions
```

兼容策略：

- 现有 `/work-items` 和 `/rule-sets` 路由继续可用并调用相同服务；
- 新 `/cases` 返回 `caseId/scenarioType/caseRevisionId`，旧路由继续返回原字段；
- 新 `/decision-assets` 返回 Decision 术语，旧路由继续返回 RuleSet 术语；
- 旧接口标记 deprecated，但本 Spec 不设置删除日期；
- 所有写请求继续使用现有 Idempotency-Key、revision 乐观锁、Problem Details、审计和事务 Outbox 模式。

`connections/{connection_id}:test` 不得在 HTTP 请求内直接访问外部网络；它创建受控健康检查命令，由 Activity/Tool 执行并返回 `202 Accepted`，查询接口读取健康投影。

### 10.2 MCP

新增最小 MCP 工具：

- `upsert_business_object`；
- `create_case`；
- `assess_case`；
- `get_case_result`；
- `list_case_findings`。

保留 `create_work_item`、`execute_work_item`，内部委托同一 `CaseService`。连接、Secret 和 DecisionAsset 发布默认不暴露为 MCP 工具，除非后续存在明确调用方和权限模型。

### 10.3 稳定错误码

至少新增：

- `BUSINESS_OBJECT_NOT_FOUND`
- `BUSINESS_OBJECT_SCHEMA_INVALID`
- `BUSINESS_OBJECT_KEY_CONFLICT`
- `OBJECT_RELATION_SCOPE_MISMATCH`
- `CASE_SUBJECT_REQUIRED`
- `CASE_SUBJECT_SCHEMA_MISMATCH`
- `CASE_REVISION_CONFLICT`
- `DECISION_ASSET_INVALID`
- `DECISION_TEST_FAILED`
- `DECISION_BINDING_REQUIRED`
- `DECISION_VERSION_NOT_PUBLISHED`
- `DECISION_SCHEMA_MISMATCH`
- `CONNECTOR_NOT_REGISTERED`
- `CONNECTION_NOT_READY`
- `CONNECTION_SECRET_UNAVAILABLE`
- `RESOURCE_BINDING_REQUIRED`
- `RESOURCE_ACCESS_MODE_DENIED`
- `RESOURCE_SNAPSHOT_FAILED`
- `RESOURCE_NOT_REPLAYABLE`

错误详情不得包含 Secret、原始文件正文或外部系统完整响应。

## 11. Assessment 执行流程

`assess_case` 必须按以下顺序执行：

1. 在 tenant/project 范围内锁定 Case，读取指定 CaseRevision。
2. 校验 Capability Pack 已启用且 Case type 匹配。
3. 校验 Subject 数量、类型和冻结的 BusinessObjectVersion。
4. 解析 StrategyVersion、Decision Binding 和 Resource Binding。
5. 重新计算 readiness；任何必需依赖未就绪则不创建 Run。
6. 计算 Case payload、Subjects、附件、DecisionVersion、ConnectionVersion 的规范化快照哈希。
7. 在同一数据库事务创建 Evaluation、`evaluation_decisions`、Run、RunCommand 和 Outbox。
8. 返回“已耐久接受”，不得在 HTTP 请求中同步调用 Temporal、S3、外部 API 或模型。
9. Runtime 通过 Activity/Tool 读取资源；每次实际读取或输出写入幂等 ResourceSnapshot。
10. 决策工具通过 DecisionExecutionService 写入输入/输出哈希和命中规则。
11. 需要沉淀抽取事实时，由显式、幂等的内部状态写入 Activity/Tool 调用 BusinessObjectService；Agent 不得直接写数据库。
12. 结果投影生成/更新 Finding、ReviewTask/FindingAction 和 Report。
13. 人工确认、改判或豁免只追加记录；需要重算时创建新的 Assessment 和 Run。

任何一步失败都不得留下没有 Outbox 的 Evaluation 或没有 Evaluation 的业务 Run。

## 12. Readiness

Capability Pack v2 readiness 在现有 Agent/Tool/Model/Strategy readiness 基础上增加：

### Decision Slot

- 已绑定 DecisionVersion；
- 版本为 PUBLISHED；
- content hash 与绑定一致；
- type、input/output schema、engine 满足 Slot；
- engine executor 存在且健康；
- 当前环境和 Policy 允许。

### Resource Slot

- 已绑定 ResourceDefinition；
- Resource kind 和 access mode 满足 Slot；
- 当前 ConnectionVersion 配置合法；
- credential_ref 可租用但不返回 Secret；
- Connector executor 存在；
- 健康检查和 Policy 通过；
- 写入资源具有幂等、补偿或人工恢复策略。

新增 blocker：

- `DECISION_BINDING_MISSING`
- `DECISION_ENGINE_MISSING`
- `DECISION_SCHEMA_INCOMPATIBLE`
- `RESOURCE_BINDING_MISSING`
- `CONNECTOR_EXECUTOR_MISSING`
- `CONNECTION_VERSION_INVALID`
- `RESOURCE_HEALTH_CHECK_FAILED`
- `RESOURCE_POLICY_DENIED`

缓存 key 必须包含 tenant/project/environment、PackVersion、DecisionVersion、ConnectionVersion 和 ResourceDefinition；版本变化必须自然失效。

## 13. 事件、审计与可观测

### 13.1 业务事件

使用独立命名空间，不修改 `run.*`：

- `business.object.created`
- `business.object.versioned`
- `business.object.relation_asserted`
- `business.case.created`
- `business.case.revised`
- `business.assessment.accepted`
- `business.decision.bound`
- `business.decision.executed`
- `business.resource.bound`
- `business.resource.snapshotted`

事件只携带稳定 ID、版本、哈希、状态和小型摘要；完整 data、输入、输出、证据和连接配置通过授权 API/Artifact 获取。

### 13.2 审计

至少审计：

- 对象创建和版本化；
- 关系断言与 supersede；
- Case 创建、修订和 Subject 变化；
- DecisionAsset 草稿修改、验证、发布和重新绑定；
- Connection 创建、版本更新、测试和禁用；
- Resource 创建、绑定和解绑；
- 人工确认、改判、豁免和解决。

DecisionExecution、ResourceSnapshot 和 Run Trace 属于机器执行事实，不为每条记录重复生成高噪声人工审计，但必须可通过 trace/correlation ID 串联。

### 13.3 指标与 Trace

新增至少以下指标：

- connector health、调用延迟、错误和限流；
- Resource Snapshot 成功率、不可重放率和新鲜度；
- Decision Execution 延迟、失败、命中率和版本分布；
- Case 到 Assessment、Finding 到人工处理的耗时；
- BusinessObject 抽取置信度、人工改判率和 Schema 失败率。

日志必须脱敏；禁止记录 Prompt、Secret、Token、原始文件正文和外部响应正文。

## 14. 权限与安全

建议新增 scope：

```text
business-object.read
business-object.write
case.read
case.write
case.assess
decision-asset.read
decision-asset.write
decision-asset.publish
connection.read
connection.manage
resource.read
resource.manage
resource.bind
review.act
```

兼容期内旧 `work-item.*` scope 映射到 Case 权限，但不能扩大授权。Connection 测试和写资源必须经过 OPA；Credential 租用必须绑定 tenant/project、connector、operation 和短 TTL。

所有新表必须：

- 同时带 `tenant_id/project_id`；
- 使用复合 FK 防止跨租户、跨项目关联；
- ENABLE/FORCE RLS；
- API/Worker 使用无 BYPASSRLS 角色；
- 集成测试验证跨租户不可见和不可写。

## 15. 前端产品模型

### 15.1 导航

- 不恢复“业务工作项”和“规则集”通用一级菜单。
- “业务工作”继续以“业务能力包”为入口。
- “平台底座”新增“资源中心”，管理 Connection、Resource 和 readiness。
- DecisionAsset 在 Capability Pack 的“决策资产”页签中管理，不与安全“策略”混淆。

### 15.2 Capability Pack 页面

至少提供：

```text
概览 | 编排策略 | 决策资产 | 资源绑定 | 业务案件 | 评估结果 | 报告与评测
```

允许分阶段交付，但“启用”操作必须在一个页面展示全部 Decision/Resource blocker。

### 15.3 场景化文案

UI 根据 Pack View Definition 显示“合同资料检查”“发票校验”“供应商风险事件”等名称，不向普通用户展示 WorkItem、RuleSet、Registry Snapshot 和 executor 等内部术语。高级详情可展示版本、哈希、证据和依赖。

所有新增页面处理 loading、empty、error、partial、stale、retry，覆盖明暗主题和键盘访问。

## 16. Migration 要求

实现时先读取当前 Alembic head，在其后新增一个或多个顺序 migration；如果当前 head 是 `0010_pack_version_delete`，首个 migration 使用 `0011_business_context_resources`。不得修改 `0008_business_workbench` 或其他历史 migration。

推荐按依赖拆分：

1. `business_context`：BusinessObject、Version、Relation、WorkItemSubject；
2. `decision_execution`：Capability Decision Binding、EvaluationDecision、DecisionExecution；
3. `resource_plane`：Connection/Version、ResourceDefinition/Binding/Snapshot；
4. 必要的 Evaluation 兼容列或索引。

每个 migration 必须：

- 使用显式表、约束、索引、RLS policy 和 immutability trigger；
- 不依赖修改后的 ORM 自动“猜测”历史结构；
- 提供可执行 downgrade，仅删除该 migration 新增对象；
- 不 CASCADE 删除历史业务表；
- 通过 metadata、upgrade/downgrade 和 RLS 集成测试。

历史 RuleSet 不批量改写；legacy 适配由读取路径完成。历史 WorkItem 不强制补 BusinessObject Subject；v1 Pack 继续允许无 Subject 执行。

## 17. 分阶段实施计划

### Phase 0：契约冻结与 ADR

任务：

1. 在系统设计中记录 BusinessObject/Case/Assessment/Run 分离和资源连接平面。
2. 为现有 WorkItem、RuleSet、Capability Pack v1、REST/MCP 和 contract-integrity 补兼容契约测试。
3. 固定旧 API、事件字段、scope 和当前 migration head。

验收：仅新增文档和测试；旧测试行为不变。

### Phase 1：BusinessObject 与 Case Subject

主要文件：

- `packages/domain/src/swarmcore_domain/business.py`
- `packages/persistence/src/swarmcore_persistence/models.py`
- `packages/persistence/alembic/versions/`
- `packages/application/src/swarmcore_application/business_context.py`
- `packages/application/src/swarmcore_application/workbench.py`
- `apps/api/src/swarmcore_api/business_schemas.py`
- `apps/api/src/swarmcore_api/business_routes.py`
- `apps/api/src/swarmcore_api/mcp.py`

任务：实现对象、版本、关系、EvidenceRef 校验、Subject 修订、Case REST/MCP 兼容入口、审计和 Outbox。

验收：对象幂等版本、关系 scope、CaseRevision 冻结 Subject、v1 无 Subject 兼容、RLS 全部通过。

### Phase 2：DecisionAsset 与 DecisionExecution

主要文件：

- `packages/application/src/swarmcore_application/rule_sets.py`
- 建议新增 `decision_assets.py`、`decision_executions.py`
- `packages/persistence/src/swarmcore_persistence/models.py`
- `apps/api/src/swarmcore_api/business_routes.py`
- contract-integrity 规则执行器及测试

任务：实现规范化信封、legacy 适配、发布 TestCase、项目槽位绑定、Assessment 冻结和执行留痕。

验收：规则版本不可变；重新绑定不改变历史 Assessment；失败 TestCase 不得发布；输入/输出/命中规则可审计。

### Phase 3：资源与连接平面

主要文件：

- `packages/registry/src/swarmcore_registry/`
- `packages/application/src/swarmcore_application/`
- `packages/governance/`
- `apps/tool-gateway/`
- `apps/api/`
- `packages/persistence/`

任务：实现 Connector Registry、ConnectionVersion、ResourceDefinition、绑定、snapshot、readiness 和健康接口。至少提供一个确定性 Fake Connector 用于测试。

验收：Secret 不落库；版本变化影响 readiness；跨项目绑定失败；读取通过 Tool/Activity；ResourceSnapshot 幂等且不可变。

### Phase 4：Capability Pack v2

任务：

1. 扩展 Manifest Parser，同时支持 v1/v2。
2. 增加 Case、Decision Slot、Resource Slot 契约。
3. 发布时冻结 Slot 契约，启用时校验项目绑定。
4. 扩展 readiness 和 dependency snapshot。
5. 发布 `contract-integrity` 2.0.0，不修改旧版本。

验收：v1 fixtures 全部继续通过；v2 缺少任一 required slot 不能启用；重新发布产生新不可变版本。

### Phase 5：contract-integrity 纵向闭环

必须完成：

```text
上传/绑定合同文件
→ 创建 ResourceSnapshot
→ 文件结构化
→ 创建/版本化 Contract 与 ContractDocument
→ 创建带 Subjects 的合同完整性 Case
→ 冻结 DecisionVersion
→ 执行确定性检查
→ 写入 DecisionExecution 和 Finding
→ 低置信度进入人工处理
→ 生成结构化 JSON 与报告 Artifact
→ 新 Assessment 重算且保留历史版本
```

验收必须证明：

- 同一合同两次 Assessment 可以使用不同对象版本和决策版本；
- 第一次结果、证据、报告仍可读取且判定口径不变；
- 人工改判不覆盖机器结果；
- Run 失败不会破坏 Case 和历史对象事实；
- 相同 idempotency key 不创建重复对象版本、Evaluation、snapshot 或 DecisionExecution。

### Phase 6：Web UI

任务：增加资源中心和 Capability Pack 页签；使用场景化 Case 文案；展示 blockers、版本、证据、Assessment 历史、Finding 和人工操作。

验收：Vitest 覆盖关键状态；Playwright 完成 contract-integrity 从绑定到报告的闭环；不恢复已删除的通用页面。

### Phase 7：文档、兼容和回归

任务：

- 更新系统设计、开发计划、README、OpenAPI、MCP 工具描述和 `.env.example`；
- 记录 v1/v2 兼容策略和旧术语 deprecated 状态；
- 检查没有修改 `agno/`、`agent-ui/`、生成目录和历史 migration；
- 运行全部相关静态检查、单元、集成、Web 和 E2E。

## 18. 测试矩阵

### 单元测试

- schema_ref、canonical JSON 和 hash 稳定性；
- 对象版本幂等和版本冲突；
- relation supersede 和 tenant/project scope；
- CaseRevision Subject 数量、类型和冻结版本；
- Decision legacy/新信封规范化；
- Decision TestCase、发布和 schema compatibility；
- Decision/Resource Slot 绑定与 blocker 聚合；
- Connection 配置脱敏和 SecretRef 拒绝规则；
- Resource Snapshot replayability 和幂等；
- v1/v2 Manifest 解析、哈希和依赖快照；
- REST 与 MCP 调用相同应用服务。

### PostgreSQL 集成测试

- migration upgrade/downgrade；
- 所有新表 RLS、FORCE RLS 和复合 FK；
- immutable trigger；
- 跨 tenant/project 对象、Subject、决策和资源绑定拒绝；
- 并发对象版本、CaseRevision 和绑定更新冲突；
- Evaluation、RunCommand、Outbox 原子创建；
- 禁用 Pack 只阻止新 Assessment，历史仍可读取。

### Runtime/外部集成测试

- Fake Connector 健康、超时、限流和凭据不可用；
- Activity 重试不重复创建 ResourceSnapshot/DecisionExecution；
- Workflow Replay 确定性；
- Tool Gateway risk、OPA、Capability Token、幂等和恢复；
- Artifact/Blob hash、扫描和授权。

### Web 测试

- required binding blockers；
- Connection/Resource loading、empty、error、stale、retry；
- Case/Assessment 历史与证据展示；
- Finding 确认、分派、豁免、解决和重新打开；
- 明暗主题、键盘操作和响应式布局。

### 验证命令

Python 变更至少运行：

```powershell
uv run ruff check .
uv run mypy
uv run pytest -q tests/unit
```

数据库、RLS、迁移、Temporal、Artifact 或跨服务变更必须运行对应 `tests/integration`。前端变更运行：

```powershell
pnpm web:lint
pnpm web:test
pnpm web:build
pnpm web:e2e
```

环境不具备 PostgreSQL、Temporal、Vault、MinIO 或浏览器条件时，必须列出未执行检查和原因，不得用 Fake 结果宣称生产资格。

## 19. 性能与容量约束

- 列表 API 必须游标或 limit/offset 分页，默认不返回全部版本、data 和 provenance。
- 单个 JSONB data、Decision 输入输出和 inline result 默认不超过 256 KiB。
- 大文件、大表格、完整外部响应和大模型上下文进入 Blob/Artifact。
- 对象查询首期只支持 object_type、canonical_key、lifecycle、更新时间和明确批准的投影字段；不得开放任意 JSONPath 查询。
- 不因方便为 JSONB 全量建立 GIN 索引；根据纵向场景的查询证据新增精确索引。
- Resource Health 使用短 TTL；健康变化不产生 Registry 新版本。
- Snapshot、Version 和 DecisionExecution 使用保留策略，但不得删除仍被 Assessment、Finding、Report 或审计引用的数据。

## 20. 禁止实现方式

实现评审发现以下任一项即不通过：

- 用 `Run.status` 直接表示 Case 状态；
- 创建 `facts(key, value)` 万能 EAV 作为主要业务存储；
- Agent 直接连接 PostgreSQL、ERP、S3、知识库或外部 API；
- 把数据库 URL、Token、API Key 写入 Manifest、Connection 普通配置或日志；
- 将 DecisionAsset 存成 Prompt 文本且没有版本、测试和执行留痕；
- 用 OPA 同时承担所有业务规则并混淆治理 Policy；
- 前端生成或信任 dependency snapshot；
- 在 Route/MCP 中复制应用服务逻辑；
- 修改已发布 Pack/Decision/Object Version 或历史 migration；
- 为兼容新术语批量改写历史记录；
- 以删除旧页面为由删除 Workbench/RuleSet 后端能力。

## 21. 最终完成标准

全部条件同时满足才能将本 Spec 标记为 `IMPLEMENTED / LOCAL`：

1. v1 WorkItem、RuleSet、Capability Pack、REST 和 MCP 契约回归通过。
2. BusinessObject、Case、Assessment、Run 语义和数据关系得到实现与测试证明。
3. DecisionAsset 发布、绑定、冻结、执行和历史审计闭环通过。
4. Connector、ConnectionVersion、ResourceDefinition、Binding、Snapshot 和 readiness 闭环通过。
5. contract-integrity v2 纵向闭环通过相关单元、集成和 Web E2E。
6. 所有新表具备 tenant/project 复合边界、RLS、索引和不可变约束。
7. REST/MCP/Worker 复用应用服务，没有旁路 Runtime、OPA、Secret、Outbox 或审计。
8. 静态检查和相关测试已实际执行；未执行检查明确记录。
9. 系统设计、开发计划、README、OpenAPI、MCP 描述和示例配置已同步。
10. 未修改 `agno/`、`agent-ui/`、`.venv/`、`node_modules/`、缓存、日志或生成产物。

只有绑定不可变 commit 和 CI 证据后，才能进一步标记为 `VERIFIED`。
