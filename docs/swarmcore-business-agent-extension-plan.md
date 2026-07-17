# SwarmCore 通用业务智能体扩展实施计划

| 属性 | 值 |
|---|---|
| 文档状态 | IN_PROGRESS（E0-E3 IMPLEMENTED / LOCAL） |
| 版本 | 0.2 |
| 建立日期 | 2026-07-17 |
| 当前目标 | 建立通用业务智能体扩展框架，并以文件完整性校验作为首个能力包 |
| 架构事实源 | [SwarmCore 系统设计](./swarmcore-system-design.md) |
| 总体里程碑 | [SwarmCore 开发计划](./swarmcore-development-plan.md) |

## 1. 文档职责

本文负责规划 SwarmCore 的通用业务智能体扩展能力，回答以下问题：

1. 如何在不修改执行内核的前提下持续增加不同业务智能体；
2. 哪些能力属于平台通用能力，哪些能力必须留在业务能力包；
3. 如何实现能力包注册、项目启用、输入资料、规则、问题追踪和报告；
4. 如何以文件完整性校验验证首个完整业务闭环；
5. 如何证明后续新增智能体不需要复制或侵入核心实现。

本文不替代系统设计和总体开发计划。发生冲突时，以系统设计中的架构边界和总体开发计划中的开放门禁为准。开始实施、改变公共 API 或调整主里程碑时，必须同步更新对应事实来源。

## 2. 目标与非目标

### 2.1 目标

- SwarmCore 保持协议无关的受控执行内核，不内置合同、发票或客服等业务知识。
- 建立版本化 Capability Pack 契约，统一声明业务 Schema、策略、Agent、Tool、规则、权限、事件、报告和 UI 元数据。
- 建立通用 Workbench，复用工作项、附件、执行评估、问题追踪和报告能力。
- 允许简单智能体只通过 Agent、Tool 和 SwarmSpec 配置接入。
- 允许复杂业务通过可信能力包扩展，但不得绕过应用服务、状态机、RLS、Outbox、审计和 Tool Gateway。
- 以文件完整性校验能力包完成第一个端到端闭环。
- 以一个非文档类最小能力包验证扩展契约的通用性。
- 所有已发布版本和历史运行均可追溯、可复现且不受后续升级影响。

### 2.2 非目标

- 不在首版建设公开能力包市场。
- 不允许运行时上传任意 Python、JavaScript 或 React 代码到控制面执行。
- 不为每个业务建立独立 Run、Workflow、权限、审计或事件体系。
- 不把业务硬规则实现为 Prompt，也不让模型直接决定确定性合规结论。
- 不为了抽象完整性一次性支持所有业务对象、页面和规则类型。
- 不在本计划中提前实现 team、subflow、emit 等当前未冻结的执行节点。
- 不改变 DeepTalk 或其他调用方负责目标理解、SwarmCore 负责受控执行的边界。

## 3. 实施原则

1. 配置优先：能用现有 Agent、Tool、Strategy 配置完成的场景，不新增能力包代码。
2. 内核稳定：新增业务不得修改 Run 状态机、Temporal 调度语义或建立第二套执行引擎。
3. 契约先行：Manifest、Schema、权限、事件和版本语义先于 UI 和具体能力包实现。
4. 版本不可变：Capability Pack、RuleSet、Strategy、报告模板和业务 Schema 发布后不可修改。
5. 确定性优先：硬规则由 JSON Schema、CEL 和受控 Tool 执行，禁止 Python eval。
6. AI 有界：模型只承担分类、抽取、归纳和解释；低置信度进入人工复核。
7. 统一服务：REST 与 MCP 复用同一应用服务、授权、幂等、错误和结果 DTO。
8. 资源引用：Workflow 只传稳定资源引用和小型结构化数据，不传大型文件或完整模型上下文。
9. 安全继承：能力包不能削弱 tenant/project、OPA、Secret、Artifact、预算和审计约束。
10. 用第二场景证伪：只有差异明显的第二个能力包无需修改核心，通用性才得到初步证明。

## 4. 扩展级别

| 级别 | 适用场景 | 交付物 | 是否修改平台代码 |
|---|---|---|---|
| L1 配置扩展 | 一次性输入输出、已有工具足够 | AgentDefinition、Tool 配置、SwarmSpec | 否 |
| L2 能力包扩展 | 有业务对象、规则、追踪、报告和专用页面 | Capability Pack Manifest、Schema、策略、规则、模板 | 原则上否 |
| L3 Provider 扩展 | 新 OCR、ERP、知识库、签章、Agent SDK | Adapter、MCP/API Connector、受控 Tool | 仅新增适配器 |
| L4 运行时扩展 | 现有节点确实无法表达且有多个明确场景 | 新节点契约、Compiler、Runtime、Canvas | 必须单独立项 |

任何需求默认从 L1 开始评估。只有 L1 无法形成业务闭环时进入 L2；只有外部能力无法通过现有 Provider 接口接入时进入 L3。

## 5. 目标架构

~~~mermaid
flowchart TB
    Caller[DeepTalk / 业务系统 / 控制台]
    REST[REST Adapter]
    MCP[MCP Adapter]
    Workbench[Business Workbench Application Service]
    PackRegistry[Capability Pack Registry]
    RuleService[Versioned Rule Service]
    RunService[Existing Strategy and Run Services]
    Temporal[Temporal Runtime]
    AgentWorker[Agent Worker]
    ToolWorker[Tool Worker]
    BlobGateway[Artifact Gateway / Input Blob Capability]
    PG[(PostgreSQL)]
    S3[(S3 / Local Artifact Store)]
    Provider[OCR / ERP / Knowledge / Signature Provider]

    Caller --> REST
    Caller --> MCP
    REST --> Workbench
    MCP --> Workbench
    Workbench --> PackRegistry
    Workbench --> RuleService
    Workbench --> RunService
    Workbench --> PG
    RunService --> Temporal
    Temporal --> AgentWorker
    Temporal --> ToolWorker
    AgentWorker --> BlobGateway
    ToolWorker --> BlobGateway
    ToolWorker --> Provider
    BlobGateway --> S3
    AgentWorker --> Workbench
    ToolWorker --> Workbench
~~~

边界要求：

- Capability Pack 只引用已注册的 Strategy、Agent、Model、Tool 和 Schema。
- Capability Pack 不直接访问 Temporal、Run 表、Outbox 或其他租户数据。
- Workbench 负责业务工作项和结果状态，Run Service 仍负责执行命令和生命周期。
- 文件字节保存在 Artifact Store，PostgreSQL 只保存元数据、归属、哈希和状态。
- 模型、OCR、数据库、网络和文件 I/O 必须位于 Activity、Tool 或 Adapter。

## 6. 通用领域模型

### 6.1 Capability Pack

| 实体 | 职责 |
|---|---|
| CapabilityPack | 能力包稳定身份、名称和生命周期 |
| CapabilityPackVersion | 不可变 Manifest、Schema 引用、依赖、权限和内容哈希 |
| ProjectCapabilityBinding | 项目启用的能力包版本、配置和状态 |

Capability Pack Version 发布时执行：

1. Manifest 结构校验；
2. Agent、Model、Tool、Strategy、Schema 和报告模板引用解析；
3. 权限和事件命名空间校验；
4. 依赖版本兼容性校验；
5. 规范化和 SHA-256 计算；
6. 不可变持久化。

### 6.2 Business Workbench

| 实体 | 通用字段与职责 |
|---|---|
| WorkItem | tenant、project、type、schemaVersion、payload、status、owner |
| WorkItemRevision | 工作项输入的不可变快照 |
| BlobObject | 运行前输入文件的不可变字节元数据、SHA-256、MIME 和保留策略 |
| WorkItemAttachment | 工作项修订与 BlobObject 的关联及业务标签 |
| Evaluation | 一次执行评估，绑定 WorkItemRevision、Run 和全部版本快照 |
| Finding | 缺失、异常、风险、建议或低置信度问题 |
| FindingAction | 确认、分派、豁免、解决和重新打开的审计历史 |
| Report | 结构化结果及 HTML/PDF Artifact 引用 |

WorkItem 只保存通用字段和经过 Schema 校验的 payload。需要强关系约束、高频聚合或大规模查询的能力包，可以新增以 work_item_id 为主键或外键的扩展表，但不能向通用表持续增加业务专用列。

### 6.3 RuleSet

规则能力是 Workbench 的可选模块，不要求所有能力包使用：

| 实体 | 职责 |
|---|---|
| RuleSet | 稳定身份和业务用途 |
| RuleSetDraft | 可编辑规则及 revision/ETag |
| RuleSetVersion | 发布后的不可变规则、Schema 版本和规则哈希 |

通用规则层首版只支持：

- JSON Schema 校验；
- CEL 条件匹配；
- presence、count、format、date、compare、cross-reference 等内置检查；
- 严重级别、问题码和报告映射；
- 唯一匹配、无匹配和歧义匹配诊断。

无法由通用规则表达的复杂检查必须通过已注册受控 Tool 实现，不在规则中嵌入代码。

## 7. Capability Pack Manifest

首版 Manifest 至少包含：

~~~yaml
apiVersion: swarmcore.io/v1
kind: CapabilityPack
metadata:
  name: contract-integrity
  version: 1.0.0

spec:
  workItemType: contract-case
  workItemSchema: schema://contract/case@1
  inputSchema: schema://contract/validation-input@1
  outputSchema: schema://contract/validation-result@1

  strategies:
    execute: strategy://contract-integrity/validate@1

  agents:
    - agent://contract/document-classifier@1
    - agent://contract/field-extractor@1

  tools:
    - tool://document/read@1
    - tool://rules/evaluate@1
    - tool://workbench/record-evaluation@1
    - tool://report/render@1

  rules:
    schema: schema://contract/checklist-rule@1

  report:
    template: report://contract/validation@1

  permissions:
    - work-item.read
    - work-item.execute
    - finding.act
    - rule.manage

  events:
    namespace: capability.contract-integrity

  ui:
    viewDefinition: view://contract-integrity/work-item@1
~~~

约束：

- Manifest 不允许 module、classPath、script、componentUrl 等任意代码入口。
- 所有引用必须包含版本或在发布时解析为唯一不可变版本。
- 事件必须位于 capability.{pack-name} 命名空间。
- Pack Version 必须记录规范化 Manifest、内容哈希和依赖快照。
- 项目绑定 Pack Version，不直接绑定可变 Pack。

## 8. 执行与一致性

### 8.1 发起执行

1. 调用方创建或更新 WorkItem；
2. 服务端创建不可变 WorkItemRevision；
3. 上传并完成 BlobObject，生成附件清单哈希；
4. Workbench 解析项目启用的 CapabilityPackVersion；
5. 校验 WorkItem、输入和附件是否满足 Pack Schema；
6. 冻结 Pack、Strategy、RuleSet、Registry 和附件清单版本；
7. 通过现有 Run Service 创建 Run；
8. 返回 EvaluationHandle 和 RunHandle。

相同项目、WorkItemRevision、Pack Version 和 Idempotency-Key 不得创建第二次 Evaluation 或 Run。

### 8.2 执行期间

- Strategy 使用现有 agent、tool、parallel、join、router、approval、input、loop 和 reducer 节点。
- Tool 和 Agent 通过短期 Capability Token 读取必要 BlobObject。
- Activity 输出先进行 Schema 校验，再进入后续节点。
- 低置信度分类或抽取进入 approval/input 节点，不直接给出确定性通过结论。
- 副作用 Tool 使用 effect_id、Tool Journal 和补偿语义。

### 8.3 结果落库

最终结果通过受控、幂等的 Workbench Tool 或应用服务写入：

- Evaluation 终态及结构化结果；
- Finding 和 FindingAction；
- Report 元数据和 Artifact 引用；
- 同事务 Outbox 事件；
- AuditLog。

不得由前端根据 Run 输出自行推导或保存业务状态。

### 8.4 版本快照

每个 Evaluation 至少冻结：

- capability_pack_version_id；
- strategy_version_id 和 plan_hash；
- registry_snapshot；
- rule_set_version_id，可为空；
- work_item_revision_id；
- attachment_manifest_hash；
- input_schema_version 和 output_schema_version；
- report_template_version；
- policy_revision。

## 9. 输入文件与 Artifact 策略

现有 Artifact 继续表示 Run 输出，不直接破坏其 run_id 外键和既有下载契约。

新增 BlobObject 作为运行前输入资源：

- 使用独立表保存归属、对象键、版本、大小、MIME、SHA-256、扫描状态和保留时间；
- 复用现有 Local/S3 Artifact Store、ClamAV、OPA、一次性下载和审计实现；
- Artifact Gateway 增加内部 Blob 上传/读取能力，不建立第二套对象存储；
- 对象键保持 tenant/project/blob/version 前缀；
- 未通过病毒扫描、格式检查或哈希校验的 Blob 不可绑定 WorkItemRevision；
- Workflow 和 Run 输入只携带 blobId、attachmentId 和哈希，不携带文件字节。

若后续证据表明 Artifact 与 BlobObject 可以安全统一，再单独设计兼容迁移；首版不重写既有 Artifact 表。

## 10. REST 与 MCP 契约

### 10.1 REST

计划新增的核心资源：

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | /projects/{project_id}/capability-packs | 查询项目可用和已启用能力包 |
| POST | /projects/{project_id}/capability-packs/{version_id}:enable | 启用不可变能力包版本 |
| POST | /projects/{project_id}/work-items | 创建工作项 |
| GET | /projects/{project_id}/work-items | 查询工作项 |
| GET | /projects/{project_id}/work-items/{work_item_id} | 获取工作项详情 |
| PUT | /projects/{project_id}/work-items/{work_item_id} | 更新并产生新 revision |
| POST | /projects/{project_id}/work-items/{work_item_id}/attachments:initiate | 初始化输入文件上传 |
| POST | /projects/{project_id}/attachments/{attachment_id}:complete | 完成上传和扫描 |
| POST | /projects/{project_id}/work-items/{work_item_id}:execute | 发起 Evaluation 和 Run |
| GET | /projects/{project_id}/evaluations/{evaluation_id} | 获取评估状态和结果 |
| GET | /projects/{project_id}/work-items/{work_item_id}/findings | 查询问题 |
| POST | /projects/{project_id}/findings/{finding_id}:act | 确认、分派、豁免或解决 |
| GET | /projects/{project_id}/evaluations/{evaluation_id}/reports | 获取报告 |
| POST | /projects/{project_id}/rule-sets | 创建规则集 |
| PUT | /projects/{project_id}/rule-set-drafts/{draft_id} | 更新规则草稿 |
| POST | /projects/{project_id}/rule-set-drafts/{draft_id}:validate | 校验和预览 |
| POST | /projects/{project_id}/rule-set-drafts/{draft_id}:publish | 发布不可变版本 |

所有写请求遵循现有 Idempotency-Key、If-Match、错误信封、鉴权和审计规则。

### 10.2 MCP

首版 MCP 只暴露业务执行所需能力：

- list_capability_packs；
- create_work_item；
- execute_work_item；
- get_evaluation；
- list_findings；
- act_on_finding；
- get_report。

规则设计和能力包发布默认只通过受控 REST/控制台开放。即使协议能力范围不同，REST 与 MCP 仍必须调用同一应用服务，不能复制业务逻辑。

## 11. UI 计划

首版使用 Schema 驱动页面，不加载能力包提供的任意前端代码。

### 11.1 通用页面

- /capability-packs：能力包、版本、依赖和项目启用状态；
- /work-items：按类型、状态、负责人和 Finding 严重级别筛选；
- /work-items/:id：业务表单、附件、执行记录、问题和报告；
- /rule-sets：规则集、草稿、版本和发布状态；
- /rule-sets/:id：可视化规则配置、诊断和示例预览；
- /evaluations/:id：执行拓扑、版本快照、问题和报告。

### 11.2 View Definition

能力包可以声明：

- 列表列和默认筛选；
- JSON Schema 表单；
- 详情区块及字段映射；
- 可用操作及所需权限；
- Finding 展示分组；
- 报告模板和预览类型；
- 导航标签和图标逻辑名。

View Definition 只能使用平台允许的组件和字段表达式，不允许脚本、远程组件或自定义 HTML。

### 11.3 交互要求

- 规则编辑器首版采用条件区、资料清单表、检查维度和样例预览，不复用通用 Strategy Canvas 表达业务规则。
- 异步页面覆盖 loading、empty、error、partial、stale 和 retry。
- 所有新增页面支持桌面、平板、移动端及明暗主题。
- 表单、Dialog、附件上传、规则表格和 Finding 操作可通过键盘完成。

## 12. 首个能力包：文件完整性校验

### 12.1 MVP 范围

- 人工选择或上游提供业务/合同类型；
- 按 RuleSetVersion 唯一匹配资料清单；
- 校验必备资料、数量、格式、可读性、重复、版本和有效期；
- 生成缺失或异常 Finding；
- 支持 Finding 确认、豁免、解决和重新打开；
- 补充文件后创建新 Evaluation，不覆盖历史结果；
- 输出稳定 JSON 结果和 HTML 报告；
- 全过程保留规则版本、附件哈希、证据和审计。

### 12.2 AI 增强范围

确定性 MVP 通过后再增加：

- 自动识别业务/合同类型；
- 文档分类和 OCR；
- 主体、编号、金额、日期等结构化字段抽取；
- 跨文件一致性检查；
- 证据页码和坐标；
- 低置信度人工复核；
- PDF 报告。

AI 不负责判断印章或签名的法律真实性。首版只检查存在性和可识别性；真实性必须由权威验签 Provider 或人工确认。

### 12.3 Finding 生命周期

状态固定为：

~~~text
OPEN -> ACKNOWLEDGED -> RESOLVED
  |            |
  +----------> WAIVED

RESOLVED / WAIVED -> OPEN
~~~

要求：

- 状态迁移由应用服务校验；
- 每次操作产生 FindingAction 和 AuditLog；
- 自动重检只能在新证据明确满足规则时解决 Finding；
- 豁免必须记录原因、操作者和可选失效时间；
- 已解决问题重新出现时保留原历史并记录重新打开动作。

### 12.4 固定验收场景

1. 发布采购合同资料规则 v1，要求合同正文、营业执照和授权书；
2. 创建 WorkItem 并上传合同正文和营业执照；
3. 执行后生成缺少授权书的 OPEN Finding 和报告；
4. 重放相同幂等键，不产生第二个 Evaluation、Run、Finding 或报告；
5. 补充授权书并形成新的 WorkItemRevision；
6. 重新执行，新 Evaluation 通过，原 Finding 转为 RESOLVED；
7. 两次 Evaluation 均能查询各自规则版本、附件哈希、结果和报告；
8. REST 与 MCP 发起的等价输入产生相同业务结果结构。

## 13. 第二能力包通用性验证

实现一个最小的工单分诊能力包，避免继续使用文件审核类场景：

- 输入：标题、正文、客户等级和渠道；
- 执行：分类、优先级判断、低置信度人工复核；
- 输出：队列、优先级、原因和建议回复；
- 不要求附件和 RuleSet；
- 复用 WorkItem、Evaluation、Finding、Report 和 Pack Registry。

通用性退出标准：

- 不修改 Run/Workflow 状态机；
- 不新增通用数据库业务字段；
- 不新增专用 REST/MCP 执行链路；
- 不复制 WorkItem、Evaluation、Finding 或 Report 服务；
- 只增加能力包 Manifest、Schema、Strategy、Agent/Tool 配置和 View Definition；
- 禁用能力包后历史数据和报告仍可读取；
- 两个能力包可在同一项目独立启用和升级。

## 14. 实施里程碑

### E0：契约与基线冻结

状态：`IMPLEMENTED / LOCAL`。Manifest v1、领域状态、REST/MCP DTO、权限、幂等、数据库/事件兼容边界和合同/工单固定夹具已冻结；事实来源已同步。

结果：形成可评审的扩展契约，不开始业务代码堆叠。

实施项：

- 将本计划纳入总体开发计划，明确它位于 M5 基线闭合之后、现生产资格里程碑之前；
- 冻结 Capability Pack Manifest v1；
- 冻结 WorkItem、Evaluation、Finding、Report 和 BlobObject 状态语义；
- 冻结 REST/MCP DTO、错误码、幂等和权限 Scope；
- 为合同校验和工单分诊建立固定 JSON 测试夹具；
- 编写数据库和事件兼容性说明。

退出标准：

- Manifest、Schema 和状态机经过评审；
- 所有开放决策已关闭或记录为明确非目标；
- 不与现有 Strategy、Run、Artifact 和权限契约冲突；
- 总体开发计划和系统设计已按实际决策同步。

### E1：Capability Pack Registry

状态：`IMPLEMENTED / LOCAL`。可信静态 Manifest 加载、引用解析、规范化哈希、不可变版本、项目绑定、RLS、审计、REST 和 Capability Catalog 已实现。

结果：平台可以注册、发布、查询和按项目启用不可变能力包版本。

实施项：

- Registry 模型、规范化、引用解析和哈希；
- CapabilityPack、CapabilityPackVersion、ProjectCapabilityBinding 表和 RLS；
- 应用服务、REST API 和 Capability Catalog 扩展；
- Pack 版本兼容、启停和审计；
- 静态可信 Manifest 加载，首版不支持远程动态安装。

退出标准：

- 发布相同 Manifest 得到相同哈希；
- 缺失、歧义或不兼容引用无法发布；
- 项目只能使用已启用的不可变版本；
- tenant/project 越权测试通过；
- 旧 Registry Snapshot 和 Run 行为不变。

### E2：通用 Business Workbench

状态：`IMPLEMENTED / LOCAL`。WorkItem/Revision、Blob/Attachment、Evaluation、Finding/Action、Report、Run 接线、Outbox/审计、REST/MCP 和通用控制台页面已实现。

结果：任意能力包可以创建工作项、上传输入、发起执行并保存通用结果。

实施项：

- WorkItem、Revision、BlobObject、Attachment、Evaluation、Finding、Action、Report；
- Artifact Gateway 输入 Blob 能力；
- Workbench 应用服务及 REST/MCP；
- Evaluation 与现有 Run Service 接线；
- 结果幂等落库、Outbox 和审计；
- 通用工作项、评估和问题 UI。

退出标准：

- 运行前文件上传、扫描、读取和保留策略闭环通过；
- 相同幂等键不创建重复 WorkItemRevision、Evaluation 或 Run；
- Worker 重试不重复 Finding、Report 或副作用；
- WorkItem 与 Run 状态不存在双向覆盖或第二事实源；
- REST/MCP 契约等价测试通过。

### E3：确定性文件完整性校验 MVP

状态：`IMPLEMENTED / LOCAL`。RuleSet 草稿/校验/发布/唯一匹配，人工资料类型，presence/count/format/duplicate/version/expiry，重检解决，JSON/HTML 报告和规则表格/样例预览已实现；第 12.4 节固定场景已在 PostgreSQL 集成测试通过。

结果：不依赖 OCR 和模型即可完成资料清单校验、预警追踪和报告。

实施项：

- RuleSet 草稿、校验、发布和唯一匹配；
- 人工资料类型标注；
- presence、count、format、duplicate、version、expiry 检查；
- Finding 生命周期和重检解决逻辑；
- JSON/HTML 报告；
- 规则表格编辑器和样例预览。

退出标准：

- 第 12.4 节固定场景全部通过；
- 规则版本、附件哈希和报告可追溯；
- 无规则和多规则匹配返回稳定诊断；
- 修改草稿不影响已发布版本和历史 Evaluation；
- 合同专用字段没有进入通用表或核心 Run 模型。

### E4：AI 文档理解与多维校验

结果：在确定性内核之上增加自动分类、抽取、证据和人工复核。

实施项：

- OCR/文档解析 Provider Adapter；
- 分类和字段抽取 Agent；
- 输出 Schema、置信度和证据定位；
- 跨文件一致性 Tool；
- approval/input 低置信度复核；
- PDF 报告和完整证据清单。

退出标准：

- 模型输出不符合 Schema 时不会进入硬规则；
- 相同文件重试不产生重复抽取和 Finding；
- 低置信度不会自动判定通过；
- OCR、模型和 Provider 故障具有超时、重试和可诊断错误；
- 固定脱敏样本集形成准确率、召回率和人工复核率基线。

### E5：第二能力包与通用性闭合

结果：工单分诊能力包证明扩展框架不依赖合同或文档场景。

实施项：

- 工单 Schema、Strategy、Agent 配置、报告和 View Definition；
- 无附件、无 RuleSet 的执行路径；
- 两能力包并存、独立版本升级和禁用测试；
- 清理为首个能力包添加的隐式分支和硬编码。

退出标准：

- 第 13 节通用性标准全部满足；
- 新能力包无需数据库 migration 和核心 API 修改；
- Capability Catalog 能发现两个能力包及其输入输出契约；
- 前端无基于 pack name 的业务分支；
- 受影响的静态、单元、集成、前端和 E2E 测试通过。

### E6：生产资格

结果：扩展框架和首个能力包在生产同构环境达到可部署、可观测和可恢复状态。

实施项：

- Kubernetes、S3/MinIO、ClamAV、OPA、Vault 和工作负载身份；
- Pack、RuleSet、Blob 和 Evaluation 指标、日志和 Trace；
- 大文件、并行抽取、慢消费者和配额压测；
- Provider 故障、Worker 重启、Temporal Replay 和对象存储故障；
- 备份恢复、保留清理和升级回滚。

退出标准：

- 受影响的总体 M5-M7 门禁在同一不可变候选版本重新通过；
- 安全、故障、恢复和容量证据绑定 commit、镜像和环境；
- 无开放 Release Blocker 或未处置 P1；
- README、配置示例、系统设计和总体开发计划同步。

## 15. 计划代码落点

| 位置 | 计划改动 |
|---|---|
| packages/domain | 通用 WorkItem、Evaluation、Finding 等纯领域类型和状态迁移 |
| packages/application | Capability Pack、Workbench、RuleSet 应用服务和 DTO |
| packages/registry | Capability Pack Manifest、版本解析、依赖和 Snapshot |
| packages/persistence | ORM、Repository、RLS 和新增 Alembic migration |
| packages/governance | Blob Capability、OPA Action、审计和保留约束 |
| packages/tool-gateway | 通用规则执行、结果落库和报告 Tool 接口 |
| packages/capability-contract-integrity | 合同能力包 Manifest、Schema、策略、规则模板和 Tool/Agent 配置 |
| packages/capability-ticket-triage | 第二能力包测试夹具与最小实现 |
| apps/api | REST/MCP Adapter，不复制应用逻辑 |
| apps/artifact-gateway | 输入 Blob 上传、扫描和受控读取 |
| apps/worker-agent | 业务 Agent 仍通过现有 Adapter 执行 |
| apps/worker-tool | 注册可信能力包 Tool Executor |
| apps/web | 通用能力包、工作项、规则、评估、问题和报告页面 |
| tests/unit | 领域、规则、Manifest、状态机、幂等和 Schema |
| tests/integration | PostgreSQL/RLS、Temporal、Blob、REST/MCP 和 Provider |

能力包目录不得依赖 FastAPI、SQLAlchemy 或 Temporal 内部对象。业务 I/O 只能通过应用服务接口、Tool/Agent 请求和稳定资源引用完成。

## 16. Migration 与兼容策略

- 所有数据库变化使用新的 Alembic migration，不修改 0001 至当前历史 migration。
- 首版只新增表、索引、RLS 和可选配置，不改变既有 Run、Artifact 和事件字段语义。
- 新 REST 资源使用独立路径；既有 Strategy/Run API 保持兼容。
- 新公共事件使用 capability.*、work-item.*、evaluation.*、finding.* 和 report.* 命名空间。
- 事件 Schema 增加字段时保持向后兼容；破坏性变化使用新 schemaVersion。
- Capability Pack、RuleSet 和 View Definition 升级产生新版本，不原地迁移历史快照。
- 功能默认通过显式项目绑定启用，未启用项目行为与当前版本一致。
- 新增配置同步更新 .env.example 和 README，不提交 .env。

## 17. 测试与证据矩阵

| 维度 | 必测内容 |
|---|---|
| 单元 | Manifest 规范化、引用解析、哈希、规则匹配、状态迁移、Schema 和幂等键 |
| 属性测试 | 相同输入的规则结果和版本哈希确定；Finding 重放不重复 |
| 持久化 | Migration、唯一约束、RLS、并发更新、ETag 和 Outbox |
| Runtime | Worker 重试、取消、人工复核、结果落库、Temporal Replay |
| Blob | 大小、MIME、SHA-256、病毒扫描、配额、保留和跨租户读取 |
| 契约 | REST/MCP 等价、稳定错误码、Capability Catalog 和旧 API 回归 |
| 前端 | Schema 表单、附件、规则编辑、Finding 操作、错误和响应式布局 |
| E2E | 合同固定场景、工单分诊、两能力包并存、升级和禁用 |
| 安全 | OPA、Scope、Capability Token、Secret、恶意文件和审计 |
| 故障 | OCR/模型/S3/数据库/Worker/Temporal 故障与恢复 |

Python 变更至少执行：

~~~powershell
uv run ruff check .
uv run mypy
uv run pytest -q tests/unit
~~~

涉及 PostgreSQL、Temporal、RLS、Migration、Artifact 或跨服务行为时运行对应集成测试。

前端变更执行：

~~~powershell
pnpm web:lint
pnpm web:test
pnpm web:build
~~~

完整交互变化执行：

~~~powershell
pnpm web:e2e
~~~

未具备依赖环境时必须记录未执行项，不能将单元测试结果描述为集成或生产证据。

## 18. 风险与控制

| 风险 | 控制 |
|---|---|
| 为合同场景过度抽象 | E3 前只抽取已出现的共性，E5 使用非文档场景验证 |
| 通用 JSONB 退化为无约束存储 | Schema 版本、应用校验、索引字段和必要扩展表 |
| 能力包绕过核心治理 | 只允许稳定引用，通过应用服务、Tool Gateway 和 OPA |
| 动态代码污染控制面 | Manifest 禁止代码入口，第三方能力使用远程 API/MCP 或 Sandbox |
| UI 出现 pack name 硬编码 | Schema 驱动 View Definition，E5 静态扫描和第二包测试 |
| AI 结果被当作硬规则 | 模型输出 Schema、置信度阈值、证据和人工复核 |
| 输入文件扩大攻击面 | 病毒扫描、MIME 校验、大小限制、隔离解析和短期 Token |
| WorkItem 与 Run 双状态源 | WorkItem 管业务状态，Run 管执行状态，Evaluation 显式关联 |
| 升级破坏历史运行 | 所有依赖版本快照不可变，历史读取不依赖当前启用版本 |
| 报告与结构化结果漂移 | 报告绑定结果 Schema 和模板版本，JSON 作为事实结果 |

## 19. 完成标准

本计划只有同时满足以下条件才能标记为 IMPLEMENTED：

- Capability Pack、Workbench、Blob、RuleSet、Evaluation、Finding 和 Report 已形成完整代码闭环；
- 文件完整性校验固定场景通过；
- 工单分诊能力包无需修改核心模型、API 或 Workflow 即可运行；
- REST 与 MCP 复用同一应用服务并有契约测试；
- 新行为具备单元、集成和前端测试；
- Migration、RLS、幂等、Outbox、审计、Artifact 和状态机约束未被绕过；
- 静态检查和相关测试已执行并记录真实结果；
- 系统设计、总体开发计划、README 和配置示例已按实际交付同步。

只有生产同构环境的部署、安全、故障、恢复和容量门禁通过，并将证据绑定到同一不可变 commit 和镜像后，才能标记为 VERIFIED。

## 20. 文档更新规则

1. 本文只维护通用业务智能体扩展和能力包交付，不记录无关基础设施工作。
2. 状态变化必须有对应代码、测试和不可变证据，不能按主观进度修改。
3. 产品边界、扩展契约或核心领域变化同步系统设计。
4. 实施顺序或总体里程碑变化同步主开发计划。
5. 公共 API、配置和启动方式变化同步 README 与 .env.example。
6. 已关闭实现细节由 Git 历史保留，正文只维护当前结果、开放风险和下一门禁。
