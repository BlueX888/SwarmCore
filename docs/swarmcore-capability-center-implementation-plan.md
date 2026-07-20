# SwarmCore 能力中心统一化实施 Plan

> 状态：IMPLEMENTED / LOCAL（2026-07-20）
>
> 目标读者：负责实现、评审和验收的 AI/工程师
>
> 事实来源：`docs/swarmcore-system-design.md`、`docs/swarmcore-development-plan.md`、仓库根目录 `AGENTS.md`
>
> 本地证据：Ruff、mypy、165 项 Python 单元测试、18 项 PostgreSQL/Temporal/MinIO/Vault
> 集成测试、Web lint/build、33 项 Vitest、33 项 Playwright 均通过。尚未绑定不可变提交和
> CI run，真实模型/OCR Provider 的环境资格仍属于后续门禁，因此不标记 `VERIFIED`。

## 1. 目标

从用户完成任务的角度统一智能体、工具、模型、策略和业务能力包的使用方式：

1. 用户在“能力中心”看到的能力必须能够端到端运行。
2. 用户无需理解注册表、运行时绑定、执行器和配置实例等内部概念。
3. 每项可用能力都提供“立即运行”和“加入画布”。
4. 参数只有需要复用时才保存为“预设”。
5. 未接入执行器、凭证失效或依赖不完整的资源不得显示为“可用”。
6. 直接运行不得绕过现有 Run、Temporal、幂等、策略、审计、Outbox 和多租户边界。

## 2. 必须采用的统一用户模型

| 概念 | 用户含义 | 是否可直接运行 |
|---|---|---:|
| 能力 | 系统提供且已经通过就绪检查的智能体、工具、模型或策略 | 是 |
| 未就绪资源 | 已声明，但执行器、凭证、依赖或健康检查不完整 | 否 |
| 我的预设 | 用户针对某项能力保存的参数模板 | 否，需基于所属能力运行 |
| 草稿 | 尚未发布或未通过验证的策略、规则等内容 | 否 |
| 业务能力包 | 一组带不可变版本的能力和业务资产 | 启用后，其就绪能力可运行 |

界面不得再把“注册成功”等同于“运行时可用”，也不得把预设描述成工具或智能体本身。

## 3. 核心架构决策

### 3.1 注册、就绪、运行三层分离

- Registry 只负责不可变定义和引用解析。
- Readiness Service 负责根据项目、环境和运行时状态生成可用性投影。
- Capability Run Service 负责把直接运行转换为标准 SwarmSpec/ExecutionPlan，并复用现有 Run Service。
- 网络、数据库、模型和文件探测不得放进 Temporal Workflow；需要耐久执行的探测使用 Activity。

### 3.2 能力就绪状态

应用层至少提供：

- `READY`：允许立即运行和加入画布。
- `NOT_READY`：不可运行，必须包含一个或多个稳定原因码。

建议原因码：

- `EXECUTOR_MISSING`
- `ADAPTER_MISSING`
- `MODEL_ROUTE_MISSING`
- `SECRET_MISSING`
- `DEPENDENCY_NOT_READY`
- `HEALTH_CHECK_FAILED`
- `ENVIRONMENT_NOT_ALLOWED`
- `CAPABILITY_PACK_DISABLED`
- `SCHEMA_INVALID`
- `POLICY_DENIED`

UI 显示用户可理解的中文说明；日志、API 和审计保留稳定原因码。

### 3.3 各类能力的 READY 门槛

工具：

- 存在 `ToolRegistration`；
- 输入/输出 Schema 合法；
- Tool Gateway 中存在对应 executor；
- 风险、幂等、恢复策略完整；
- 当前环境和策略允许；
- executor 健康检查通过。

模型：

- 存在逻辑模型注册和 Provider Route；
- 凭证引用可租用，但不得泄露凭证值；
- Endpoint 可访问且模型名称有效；
- 当前环境允许；
- Model Gateway 健康检查通过。

智能体：

- 存在 Agent 注册或受支持的内联 Agent 类型；
- Agent Adapter 可用；
- 默认模型为 `READY`；
- 所有声明工具为 `READY`；
- 声明 Schema 合法且当前环境允许。

策略：

- 已发布为不可变版本；
- 编译通过；
- Registry Snapshot 匹配；
- 所有解析后的 Agent、工具和模型均为 `READY`。

业务能力包：

- Manifest 和依赖快照合法；
- 所有引用资源已注册；
- 启用前所有必需运行能力均为 `READY`；
- 任一必需依赖未就绪时，启用失败并返回完整阻塞原因。

## 4. 目标用户流程

### 4.1 能力中心

统一入口“能力中心”，支持按智能体、工具、模型、策略筛选。

每张能力卡只突出：

- 用户可理解的名称和用途；
- `可用` 或 `未就绪`；
- 来源（系统内置、业务能力包、自定义）；
- 风险等级（仅工具）；
- “立即运行”“加入画布”“查看详情”。

URI、runtime、Schema、Provider Route、依赖图放入高级详情。

### 4.2 立即运行

1. 用户选择能力。
2. 系统根据输入 Schema 生成表单。
3. 用户填写输入，可选加载一个预设。
4. 服务端执行预检。
5. 服务端创建标准 Run，不建立旁路执行逻辑。
6. UI 跳转运行详情页，复用已有状态、事件、审批和结果展示。

### 4.3 我的预设

- 预设必须引用一个不可变能力 Ref。
- 预设只保存允许持久化的参数，不保存 API Key、Token 或其他秘密。
- 预设可以编辑、复制、删除和用于立即运行/加入画布。
- 原 `ProjectConfiguration` 数据保留，应用层和 UI 逐步更名为 `CapabilityPreset`/“我的预设”。

## 5. 分阶段实施

每个阶段独立提交、独立测试；上一阶段未通过不得开始下一阶段。

### Phase 0：冻结契约和基线

目标：在行为变化前固定现状和兼容边界。

任务：

1. 为现有 REST/MCP 能力目录、项目配置和能力包启用补充契约测试。
2. 记录当前 `ProjectConfiguration` API 和数据库结构。
3. 增加功能开关 `SWARMCORE_CAPABILITY_CENTER_V2`，默认关闭；`.env.example` 同步。
4. 在系统设计文档记录“能力不等于注册项”的 ADR。

主要文件：

- `apps/api/src/swarmcore_api/routes.py`
- `apps/api/src/swarmcore_api/mcp.py`
- `packages/application/src/swarmcore_application/configurations.py`
- `tests/unit/test_mcp.py`
- `tests/integration/test_project_configuration_api.py`
- `docs/swarmcore-system-design.md`

验收：旧接口和旧 UI 在开关关闭时行为不变。

### Phase 1：能力就绪投影

目标：建立一个 REST、MCP 和 UI 共用的就绪事实来源。

任务：

1. 在领域/应用边界定义 `CapabilityKind`、`CapabilityReadiness`、`ReadinessReason` 和 `CapabilitySummary`。
2. 实现 `CapabilityReadinessService`，输入 tenant/project/environment 和 Registry Snapshot，输出能力投影。
3. 为 Tool Gateway、Model Gateway 和 Agent Adapter 定义只读健康/注册查询接口。
4. Tool Gateway 必须能报告注册项是否有 executor，禁止仅根据 Registry 推断可运行。
5. Model Gateway 只报告 secret 是否可租用和路由/健康状态，不返回秘密。
6. Agent Readiness 递归聚合模型、工具和 Adapter 状态，并检测依赖循环。
7. 对 readiness 结果使用短 TTL 缓存；缓存必须包含 tenant/project/environment 维度。

建议新增文件：

- `packages/application/src/swarmcore_application/capability_readiness.py`
- `packages/domain/src/swarmcore_domain/capabilities.py`

主要修改文件：

- `apps/tool-gateway/src/swarmcore_tool_gateway_api/main.py`
- `apps/model-gateway/src/swarmcore_model_gateway/main.py`
- `packages/registry/src/swarmcore_registry/models.py`

验收：当前缺少 executor 的能力包工具返回 `NOT_READY/EXECUTOR_MISSING`，不得返回 READY。

### Phase 2：能力中心应用服务与 API

目标：提供统一的用户能力查询和直接运行入口。

任务：

1. 实现 `CapabilityCenterService`，组合 Registry、Readiness、能力包绑定和预设。
2. 新增兼容性 API，避免直接破坏现有 `/capabilities`：
   - `GET /v1/projects/{project_id}/capability-center`
   - `POST /v1/projects/{project_id}/capability-runs`
3. `capability-runs` 请求包含 `capabilityRef`、`input`、可选 `presetId` 和幂等键。
4. 将工具、智能体、模型的直接运行分别转换为单节点标准 SwarmSpec；随后调用现有编译、发布/临时版本和 Run Service。
5. REST 与 MCP 复用同一应用服务；新增对应 MCP tools，而不是复制业务逻辑。
6. 所有写操作保留 tenant/project、授权、审计和幂等检查。

主要文件：

- `packages/application/src/swarmcore_application/capability_center.py`
- `apps/api/src/swarmcore_api/routes.py`
- `apps/api/src/swarmcore_api/mcp.py`
- `apps/api/src/swarmcore_api/schemas.py`

验收：同一能力通过 REST 与 MCP 查询得到相同 readiness；直接运行返回正常 `RunHandle`。

### Phase 3：预设统一和兼容迁移

目标：把“已配置”统一为用户可理解的“我的预设”。

任务：

1. 应用层引入 `CapabilityPresetService`，复用现有 `project_configurations` 表，首版不改表名。
2. 新增 `/presets` API，并让旧 `/configurations` API 进入兼容层。
3. Preset 校验必须使用 Capability Center：所属能力必须存在；能力可以暂时 NOT_READY，但 UI 必须显示原因。
4. 禁止秘密字段写入 preset；复用现有 secret scanner/redaction 规则。
5. 增加 Alembic migration 仅在确实需要新字段时创建；不得修改历史 migration。
6. 将演示数据名称改为“演示预设”，避免误认为可运行能力。

主要文件：

- `packages/application/src/swarmcore_application/configurations.py`
- `apps/api/src/swarmcore_api/routes.py`
- `apps/api/src/swarmcore_api/schemas.py`
- `apps/api/src/swarmcore_api/seed.py`

验收：现有配置数据无损显示为预设，旧 API 仍通过契约测试。

### Phase 4：能力中心 UI

目标：让普通用户只面对“可用能力、未就绪资源、我的预设”。

任务：

1. 新增统一能力中心页面，默认只展示 READY，提供“显示未就绪”开关。
2. 支持智能体、工具、模型、策略筛选与搜索。
3. READY 卡片提供“立即运行”“加入画布”；NOT_READY 卡片禁用执行并展示具体原因。
4. 新增基于 JSON Schema 的输入表单；无法安全生成表单时回退到校验型 JSON 编辑器。
5. “我的预设”作为能力详情的次级区域，不再与能力并列为两套资源。
6. 现有 `/agents`、`/tools`、`/models` 页面先重定向或包装到带筛选条件的能力中心，保留旧链接兼容。
7. 原始 URI、runtime 和 Schema 移入“高级详情”。
8. 运行后跳转现有运行详情页，不新增另一套运行结果页面。

主要文件：

- `apps/web/src/pages/capabilities-page.tsx`
- `apps/web/src/pages/registry-config-page.tsx`
- `apps/web/src/api/client.ts`
- `apps/web/src/api/types.ts`
- `apps/web/src/components/layout/app-shell.tsx`
- `apps/web/src/main.tsx`

验收：首次使用者无需理解 Registry/Runtime/Configuration 即可完成一次能力运行。

### Phase 5：能力包启用门禁

目标：业务能力包一旦显示“已启用”，其必需运行能力必须可用。

任务：

1. 在 `CapabilityPackService.enable` 前调用 Readiness Service 检查 Manifest 所有必需运行引用。
2. 任一依赖 NOT_READY 时拒绝启用，返回所有阻塞引用和原因码。
3. 对已启用但后续退化的能力包显示 `DEGRADED`，历史 Evaluation 继续绑定原版本。
4. 禁止静默切换 Pack Version 或 Provider Route。
5. 启用、拒绝、退化和恢复均写审计事件。

主要文件：

- `packages/application/src/swarmcore_application/capability_packs.py`
- `apps/api/src/swarmcore_api/business_routes.py`
- `apps/web/src/pages/capability-packs-page.tsx`

验收：缺少 executor 的 contract-integrity 工具存在时，能力包不能被错误标记为完全可用。

### Phase 6：补齐执行器并逐项开放

目标：把当前只注册未执行的能力逐项变为 READY。

实现顺序：

1. `tool://document/read@1`
2. `tool://rules/evaluate@1`
3. `tool://contract/cross-file-consistency@1`
4. `tool://workbench/record-evaluation@1`
5. `tool://report/render@1`
6. `agent://contract/document-classifier@1`
7. `agent://contract/field-extractor@1`

每个工具必须：

- 有真实 executor，不允许返回占位结果；
- 明确定义输入/输出 Schema，替换当前开放对象 Schema；
- 明确 risk、sideEffecting、idempotent 和 recoveryPolicy；
- 有 tenant/project 授权和审计；
- 有成功、失败、重试、幂等和越权测试；
- 通过 Readiness Service 后才在 UI 显示“可用”。

## 6. 兼容与迁移约束

1. 不删除 `ProjectConfiguration` 数据，不直接重命名数据库表。
2. 不修改已使用的 Alembic migration；需要变更时新增 migration。
3. 旧 `/capabilities` 继续作为底层运行时目录契约；新用户投影使用 `/capability-center`。
4. 旧 `/agents`、`/tools`、`/models` URL 在迁移期保持可访问。
5. REST 与 MCP 必须共享应用服务和 readiness 计算。
6. Registry Snapshot 变化必须进入计划哈希和审计，不得动态污染已发布执行计划。
7. 健康状态是动态投影，不写入不可变 Registry 定义。

## 7. 测试矩阵

### 单元测试

- 每类能力的 READY/NOT_READY 状态矩阵。
- 依赖传播和循环检测。
- Preset 校验、秘密拒绝和旧配置兼容。
- 单节点 SwarmSpec 生成和编译。
- 能力包启用门禁。
- REST/MCP structured content 一致性。

### 集成测试

- PostgreSQL tenant/project 隔离。
- Tool Gateway executor 注册和真实调用。
- Model Gateway route、Vault secret lease 和 Provider 故障。
- Temporal 直接运行、重试、取消、审计和 Outbox。
- 能力包启用失败与恢复。

### 前端测试

- READY 默认展示，NOT_READY 原因展示。
- “立即运行”生成正确请求并跳转运行详情。
- “加入画布”生成正确节点。
- Preset 创建、加载、更新、删除。
- 旧路由兼容。

### E2E

至少覆盖：

1. 用户打开能力中心。
2. 选择 READY 工具。
3. 填写输入并保存预设。
4. 立即运行。
5. 在运行详情看到完成结果和审计事件。
6. 对 NOT_READY 工具无法运行且能看到明确原因。

## 8. 完成标准

只有同时满足以下条件才能把本计划标记为 IMPLEMENTED/VERIFIED：

- 能力中心默认展示的每项能力都通过端到端运行测试。
- 不存在“注册但无 executor”仍显示为可用的工具。
- 智能体的模型和工具依赖全部参与 readiness。
- 模型的 Route、Secret 和 Endpoint 全部参与 readiness。
- 直接运行走标准 Run/Temporal 链路。
- REST/MCP 共用应用服务并返回一致结果。
- Preset 不包含秘密且保持 tenant/project 隔离。
- 业务能力包启用有完整依赖门禁。
- Ruff、mypy、Python 单元测试、相关集成测试、Web lint/test/build 和 Playwright E2E 全部通过。
- README、`.env.example`、系统设计和开发计划同步更新。

## 9. AI 执行指令

实现 AI 必须遵循：

1. 开始前读取根目录 `AGENTS.md` 和本计划，不得绕过架构约束。
2. 先检查工作树，保留用户已有修改；只修改当前 Phase 相关文件。
3. 一次只实施一个 Phase，不跨阶段顺手重构。
4. 行为变更先补测试或同步补测试，不得只改 UI 文案。
5. 不得把占位 executor、静态假健康状态或空 Schema 标记为 READY。
6. 不得把 API Key 写入源码、Preset、数据库普通 JSON 或前端状态。
7. 不得建立 REST/MCP 两套实现。
8. 不得绕过 Temporal、状态机、幂等、Outbox、审计、策略和多租户过滤。
9. 未执行的测试必须明确记录，未通过对应测试不得标记 VERIFIED。
10. 每个 Phase 完成后报告：修改内容、兼容影响、测试结果、未完成项和下一阶段入口条件。

## 10. 非目标

- 不在本计划中重写画布编辑器。
- 不引入第二套工作流引擎或旁路任务队列。
- 不允许用户上传任意 Python/JavaScript 作为工具执行器。
- 不把能力包 Manifest 变成代码入口。
- 不为了统一 UI 删除不可变版本、Registry Snapshot 或项目隔离。
