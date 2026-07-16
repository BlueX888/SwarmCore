# SwarmCore 开发计划与里程碑

| 属性 | 值 |
|---|---|
| 文档状态 | Living Document / 持续更新 |
| 版本 | 1.5 |
| 建立日期 | 2026-07-16 |
| 最近更新 | 2026-07-16 |
| 当前里程碑 | M2C：Strategy Canvas 可视化编排（VERIFIED） |
| 当前基线提交 | M2B/M2C 集成提交（本文件所在版本） |
| 关联设计 | [SwarmCore 系统设计](./swarmcore-system-design.md) |
| 维护者 | SwarmCore Team |

## 1. 文档目的

本文档记录 SwarmCore 的开发顺序、当前进度、验收证据、阻塞项和下一步工作。系统设计文档回答“系统最终是什么”，本文档回答“当前开发到哪里、接下来交付什么”。

每次里程碑状态变化、验收结果变化或开发优先级调整时更新本文档。代码已合并不等于里程碑已验收；只有满足退出标准并留下测试证据后，状态才能标记为 `VERIFIED`。

## 2. 产品目标与开发原则

SwarmCore 的核心目标是形成以下稳定闭环：

~~~text
DeepTalk / 其他调用方
  -> 查询 Agent、Tool、Model 和编排能力
  -> 通过 REST API 或 MCP 提交 SwarmSpec
  -> SwarmCore 校验、编译并耐久执行
  -> 调用方查询或订阅状态
  -> SwarmCore 返回统一 RunResult
~~~

开发遵循以下原则：

1. DeepTalk 负责目标理解和编排决策，SwarmCore 负责受控、可靠地执行。
2. REST API 与 MCP 是统一应用服务的并列适配器，不建立两套业务逻辑。
3. 控制台只用于人工测试、执行观测和问题诊断。
4. 优先完成真实端到端闭环，再扩展节点数量、治理能力和部署规模。
5. 每个里程碑必须具有可执行的验收场景，不以文件数量或代码量判断完成度。

## 3. 状态定义

| 状态 | 含义 |
|---|---|
| `PLANNED` | 范围和验收标准已定义，尚未开始实现 |
| `IN_PROGRESS` | 已开始实现，但尚未完成全部交付项 |
| `IMPLEMENTED` | 代码已实现，仍有集成、环境或验收项未完成 |
| `VERIFIED` | 所有退出标准通过，证据已记录 |
| `BLOCKED` | 存在明确阻塞条件，当前无法继续推进 |

## 4. 总体里程碑

| 里程碑 | 目标 | 当前状态 | 下一道门禁 |
|---|---|---|---|
| M0 | 产品定位与系统设计基线 | `VERIFIED` | 设计变更持续同步 |
| M1 | 耐久执行核心 MVP | `VERIFIED` | 持续回归 |
| M2A | 人工控制与运行干预 | `VERIFIED` | 持续回归 |
| M2B | DeepTalk Integration MVP | `IMPLEMENTED` | 远端 CI 运行并通过 Fake Agent E2E |
| M2C | Strategy Canvas 可视化编排 | `VERIFIED` | 持续回归 |
| M3 | 受控 Tool 与编排能力扩展 | `PLANNED` | Agent + Tool + Router/Loop 闭环 |
| M4 | 治理、安全与生产能力 | `PLANNED` | 安全、审计、预算、Artifact 验收 |
| M5 | 规模化与生态扩展 | `PLANNED` | 容量、灾备和扩展适配器验收 |

## 5. 当前进度基线

### 5.1 已提交能力

当前仓库已有两个明确的功能基线：

- `230a089`：Phase 1 MVP。
- `ea8a09b`：Phase 2A Human Control。

已存在的主要模块：

- SwarmSpec v1 数据模型、解析和模板。
- 确定性 Compiler、ExecutionPlan 和 Plan Hash。
- Run、Task、Attempt、Event、Command 等领域与持久化模型。
- PostgreSQL Migration、RLS、Transactional Outbox。
- Command Dispatcher、Event Publisher、Projection Reconciler。
- Temporal Workflow、调度器和控制 Worker。
- Agno Adapter、真实模型入口和确定性 Fake Agent。
- Strategy、Run、Command、SSE 和基础 MCP 接口。
- Pause、Resume、Cancel、Approval、External Input 和 Task Retry。
- 基础测试与观测控制台。

### 5.2 2026-07-16 验证快照

| 门禁 | 结果 | 证据/备注 |
|---|---|---|
| 后端单元测试 | 通过 | `44 passed` |
| Ruff | 通过 | `All checks passed` |
| Mypy | 通过 | `47 source files` 无问题 |
| 前端单元测试 | 通过 | `5 files / 10 tests passed` |
| 前端 ESLint | 通过 | 0 warning |
| 前端生产构建 | 通过 | Vite 构建成功；存在主 Chunk 大于 500 KiB 警告 |
| 后端集成测试 | 待复验 | 共收集 4 项；PostgreSQL 契约依赖 `SWARMCORE_TEST_DATABASE_URL`，Temporal 测试环境本次未完成启动 |
| Playwright E2E | 本次未执行 | M2B 验收前必须执行并记录结果 |

当时结论：M1 和 M2A 已实现，但环境型集成测试尚未形成可重复的全绿证据，因此保持 `IMPLEMENTED`；该缺口已在 5.3 节关闭。

### 5.3 2026-07-16 M1/M2A 验收记录

执行命令：

~~~powershell
./scripts/test-integration.ps1
uv run pytest -q tests/unit
uv run ruff check .
uv run mypy
~~~

结果：

- 独立 PostgreSQL 17.5 与 Temporal 1.28.0 环境从零创建，Migration `0001 -> 0002` 成功。
- 后端集成测试 `7 passed in 50.63s`，无警告；脚本结束后自动清理容器与数据。
- 后端单元测试 `44 passed`；Ruff 通过；Mypy 对 47 个源文件检查通过。
- 覆盖 Migration、RLS、Strategy API、完整 Run API/Outbox/Temporal/Worker/Projection 闭环。
- 覆盖顺序、并行、DAG、Supervisor、Activity 恢复、Cancel、Pause、Resume、Approval、External Input、Retry。
- Approval 与 External Input 均验证 Control Worker 重启后请求内容、Pending 状态、命令游标和乱序拒绝语义保持一致。

验收中发现并修复：

- `0002` 在全新数据库上可能因 `0001` 的 metadata 建表而重复创建 `uq_runs_scope_id`，现兼容 PostgreSQL `duplicate_table`。
- Temporal 容器健康检查必须使用容器 DNS 地址，不能使用容器内 loopback。
- Workflow 终态返回前等待 Update Handler 完成，消除命令结果可能被终态截断的警告。
- 真实 Temporal 下 Cancel 终态等待窗口由 5 秒调整为 30 秒，避免环境调度抖动造成假失败。

阻塞项：无。

下一步唯一最高优先事项：M2B-01，抽离 REST/MCP 共用的协议无关应用服务层。

### 5.4 2026-07-16 M2B 实现与验收快照

结果：

- 后端单元测试 `47 passed`；Ruff 通过；Mypy 对 53 个源文件检查通过。
- PostgreSQL/Temporal 集成测试 `7 passed in 55.05s`。
- DeepTalk Harness 完成 capabilities、compile、REST/MCP inline create、status、result 调用序列。
- 固定场景为“两路 Fake Agent 并行分析 -> Reducer”，Agent Worker 在 Activity 执行中重启后 Run 恢复成功。
- REST/MCP 对相同 Spec 的 Plan Hash、诊断、Run 状态和 RunResult 等价。
- 前端 `5 files / 10 tests passed`，ESLint 通过，生产构建通过；主 Chunk 大于 500 KiB 警告仍保留为 P2。
- Playwright `15 passed`，覆盖 desktop/tablet/mobile 与 light/dark。
- 新增 GitHub Actions 后端门禁和 Linux/PowerShell 双平台一键集成脚本；远端 workflow 尚未运行。
- `./scripts/smoke-agno-ollama.ps1` 使用本机 `qwen3:0.6b` 完成真实 Agno Model 受控调用，输出 `AGNO_OLLAMA_SMOKE_OK model=qwen3:0.6b`。
- Smoke 修复后复验：后端单元测试 `47 passed`；Ruff 通过；Mypy 对 53 个源文件检查通过。

发现并修复：

- REST 与 MCP 时间戳分别输出 `Z` 和 `+00:00`，现统一为 UTC `Z`。
- REST 与 MCP 的 compile 默认 registry/policy、诊断与 Plan Hash 原先可能分叉，现统一到应用服务。
- MCP 原先额外要求 Bearer 且使用异常类名作为错误码，现与 REST 统一使用当前租户作用域和稳定应用错误码；正式认证与 OPA 留在 M4。
- Worker 重启测试会对固定 Temporal task queue 留下取消投递，因此破坏性恢复场景固定为套件最后一项，避免测试间污染。
- Agno 2.7.3 的 Ollama provider 还会导入 OpenAI 基类，适配器改用官方 `ollama,openai` extras；结构化 Agent 输入稳定序列化为 JSON，消除 Message 校验警告。

阻塞项：GitHub Actions 只有推送或 PR 后才能形成远端 CI 通过证据；本轮未获授权发布分支或创建 PR。

下一步唯一最高优先事项：在 PR CI 中确认 Fake Agent E2E；通过后将 M2B 标记为 `VERIFIED`。

## 6. M0：产品定位与系统设计基线

状态：`VERIFIED`

已完成：

- 明确 SwarmCore 是协议无关的多 Agent 编排执行运行时。
- 明确 DeepTalk 是编排决策方，SwarmCore 是执行方。
- 明确 REST API 与 MCP 是并列入口。
- 明确控制台是人工测试与观测客户端。
- 建立系统边界、领域模型、执行设计、数据设计和安全设计。

持续要求：任何改变产品边界、事实源、执行语义或接口职责的决定，必须先更新系统设计或新增 ADR。

## 7. M1：耐久执行核心 MVP

状态：`VERIFIED`

目标：证明声明式 SwarmSpec 可以被编译为不可变 ExecutionPlan，并由 Temporal 可靠执行。

已完成：

- 顺序、并行、DAG、Supervisor 模板和基础 Reducer。
- Run 创建、耐久接收和异步启动。
- Temporal Worker 故障重试与状态投影。
- PostgreSQL 产品状态、事件和 Outbox。
- SSE 事件读取和基础控制台观察。
- REST API 与基础 MCP Server。

退出标准：

- [x] 单元测试覆盖 Spec、Compiler、调度、状态和持久化。
- [x] 静态检查和类型检查通过。
- [x] Temporal Workflow 集成测试在标准开发环境可重复通过。
- [x] PostgreSQL Migration、RLS 和 API 集成测试在标准测试数据库可重复通过。
- [x] 一条从提交 Run 到获得最终结果的本地部署验收记录。

## 8. M2A：人工控制与运行干预

状态：`VERIFIED`

目标：允许调用方在不破坏 Temporal 状态一致性的前提下控制运行和处理人工等待。

已完成：

- RunCommand 按 `command_seq` 顺序交付。
- Command `request_id` 幂等。
- Pause、Resume 和 Cancel。
- Approval 和 External Input 一次性请求。
- 失败 Task 的人工 Retry。
- 人工等待表、RLS 和 API。
- 控制台 Run 控制操作。

退出标准：

- [x] 状态机和命令顺序单元测试通过。
- [x] Migration 契约测试通过。
- [x] Pause/Resume/Approval/Input/Retry 的 Temporal 集成测试在标准环境可重复通过。
- [x] Worker 重启后未决人工请求和命令游标保持一致。

## 9. M2B：DeepTalk Integration MVP

状态：`IMPLEMENTED` / 待外部验收证据

### 9.1 目标

DeepTalk 可以通过 REST API 或 MCP 查询能力、自主生成并提交 SwarmSpec、跟踪执行并取得最终 RunResult。关闭控制台后，该链路仍完整可用。

### 9.2 工作分解

| ID | 工作项 | 状态 | 预期产出 |
|---|---|---|---|
| M2B-01 | 抽离协议无关的应用服务层 | `IMPLEMENTED` | `packages/application`；REST/MCP 共用 Strategy、Run、Run Query 服务；44 单测、Ruff、Mypy 通过 |
| M2B-02 | 建立 Capability Catalog | `IMPLEMENTED` | REST/MCP 统一 DTO；Agent、Model、6 种节点、限制和 SwarmSpec Schema；45 单测通过 |
| M2B-03 | 支持 Inline SwarmSpec 创建 Run | `IMPLEMENTED` | REST/MCP 可提交 inline Spec；EPHEMERAL 版本、幂等 RunHandle、双 Run 真实闭环通过 |
| M2B-04 | 建立标准 RunResult | `IMPLEMENTED` | REST `GET result`；终态信封、Task/Usage/Artifact/Error/Provenance；非终态 409；真实闭环通过 |
| M2B-05 | 补齐 MCP 入站适配器 | `IMPLEMENTED` | capabilities、validate、compile、create、status、result、control Tools；真实 MCP Run 通过 |
| M2B-06 | 统一 REST/MCP 契约 | `IMPLEMENTED` | 共用应用服务；Plan Hash、diagnostics、status、result 等价；修复 UTC 时间格式分叉 |
| M2B-07 | 建立 DeepTalk 契约测试 Harness | `IMPLEMENTED` | 可复用 Harness 按 capabilities/compile/create/status/result 顺序完成 REST/MCP 真实验收 |
| M2B-08 | 完成可重复集成测试环境 | `IMPLEMENTED` | PostgreSQL、Temporal 和服务进程一键启动与测试；`7 passed` |
| M2B-09 | 控制台适配新增公开接口 | `IMPLEMENTED` | RunHandle `planHash` 类型已适配；10 单测、Lint、Build、15 Playwright 通过 |

### 9.3 退出标准

- [x] DeepTalk 可查询当前允许使用的 Agent、Tool、Model 和编排节点。
- [x] DeepTalk 可通过 REST 提交 inline SwarmSpec 并获得 RunHandle。
- [x] DeepTalk 可通过 MCP 提交相同方案并获得结构等价的 RunHandle。
- [x] 调用方可查询状态、读取事件并获得统一 RunResult。
- [x] REST 与 MCP 对相同 Spec 产生相同 Plan Hash 和验证诊断。
- [x] REST 与 MCP 使用相同的权限、幂等和错误语义。
- [x] 短任务和长任务均不依赖长时间阻塞连接。
- [ ] Fake Agent 确定性 E2E 在 CI 通过。
- [x] 至少一条真实 Agno Model 的受控 Smoke Test 通过。
- [x] 控制台关闭或未部署时，REST/MCP/Worker 链路不受影响。
- [x] M1、M2A 遗留集成测试全部形成可重复证据。

### 9.4 固定验收场景

采用一个稳定场景作为 M2B 的主验收用例：

1. DeepTalk 查询两个 Agent 和一个 Reducer 能力。
2. DeepTalk 生成“两路并行分析 -> Reducer 汇总”的 inline SwarmSpec。
3. SwarmCore 编译并返回 Plan Hash 和 RunHandle。
4. DeepTalk 使用事件或状态查询跟踪运行。
5. Worker 在执行中重启，Run 自动恢复。
6. DeepTalk 获得包含输出、用量、警告和 provenance 的 RunResult。
7. 同一场景分别通过 REST 和 MCP 执行，契约保持一致。

### 9.5 本里程碑不做

- 不实现所有 SwarmSpec 节点类型。
- 不扩展 A2A 生态适配器。
- 不建设面向终端用户的聊天界面。
- 不进行大规模控制台视觉重构。
- 不引入 Kafka、Qdrant 或 Kata 等非必要基础设施。

## 10. M2C：Strategy Canvas 可视化编排

状态：`VERIFIED`

### 10.1 目标

让开发和测试人员通过 React Flow 画布拖拽节点、连线和编辑属性，生成、校验、保存、发布并执行与文本编辑器语义完全一致的 SwarmSpec。画布只是 SwarmSpec 的可视化编辑器，不引入第二套策略格式、编译规则或执行链路。

### 10.2 固定决策

1. SwarmSpec 是唯一执行语义和发布事实源；画布操作只对 Spec 做无损的局部修改。
2. 节点坐标和视口保存为 Draft 的独立 `editorState`，不写入 SwarmSpec，移动节点不得改变 Spec Hash 或 Plan Hash。
3. Canvas、JSON 和 YAML 共用同一份工作中 Spec；模式切换是显式同步边界，文本无效时不覆盖最后一份有效画布状态。
4. 节点库由 Capability Catalog 驱动；首版只允许 `agent`、`parallel`、`join`、`reducer`、`approval` 和 `input`。
5. 未支持节点在导入时必须保留原始数据并以只读节点显示，不允许静默丢弃。
6. 服务端 Compiler 是权威校验器；前端只做循环、自连接、重复连线和必填属性等即时防错。

### 10.3 画布语义

| 画布操作 | SwarmSpec 变更 |
|---|---|
| 添加 Agent 节点 | 新增 `spec.agents` 声明和 `graph.nodes` 中的 `agent` 节点 |
| A 连接 B | 向 `B.dependsOn` 加入 A |
| 删除连线 | 从目标节点 `dependsOn` 移除源节点 |
| Parallel 连接分支 | 同时维护 `parallel.branches` 和目标节点 `dependsOn` |
| 设置入口 | 修改 `graph.entrypoint` |
| 删除节点 | 删除节点、相关依赖和布局；仅在 Agent 声明已无引用时提示一并删除 |
| 移动节点 | 只更新 `editorState.positions` |

### 10.4 工作分解

| ID | 工作项 | 状态 | 预期产出 |
|---|---|---|---|
| M2C-01 | 建立前端 Strategy Editor 领域模型 | `VERIFIED` | 当前可执行 SwarmSpec 子集的 TypeScript 类型、无损局部修改和循环检测纯函数 |
| M2C-02 | 持久化独立编辑器布局 | `VERIFIED` | `strategy_drafts.editor_state` JSONB、Migration、REST DTO 和 ETag 并发更新；Publish 忽略界面状态 |
| M2C-03 | 建立可编辑 React Flow 画布 | `VERIFIED` | 节点库、自定义节点、连线、删除、入口设置、选择与属性面板 |
| M2C-04 | 实现当前节点的语义映射 | `VERIFIED` | Agent 引用、`dependsOn`、Parallel branches、Join、Reducer、Approval 和 External Input 的双向映射 |
| M2C-05 | 打通 Canvas / JSON / YAML | `VERIFIED` | 三模式显式切换、无效文本保护、dirty 状态、重载确认和 Draft revision 冲突处理 |
| M2C-06 | 接入 Compile / Save / Publish | `VERIFIED` | 语义变更的延迟编译、诊断定位与节点高亮；发布前对当前 Spec 强制重新编译 |
| M2C-07 | 完成自动化与真实验收 | `VERIFIED` | 纯函数单测、组件测试、Playwright 画布 E2E 和真实模型运行记录 |

### 10.5 退出标准

- [x] 可从空白画布创建、校验、保存和发布一个策略。
- [x] 可将现有顺序、并行和人工审批 Spec 无损载入画布，往返转换不改变执行语义。
- [x] 连线正确生成 `dependsOn`；Parallel 分支同时生成 `branches` 和调度依赖。
- [x] 自连接、重复连线和循环依赖在保存前被拒绝。
- [x] Compiler diagnostics 可定位到对应节点或全局属性。
- [x] 画布、JSON 和 YAML 可靠切换；无效文本不破坏最后有效 Spec。
- [x] 保存后刷新页面，节点位置和视口不丢失。
- [x] 仅移动节点不改变 Plan Hash；改变连线或节点配置会改变 Plan Hash。
- [x] 未支持节点不会被画布编辑器静默删除。
- [x] 窄屏、深色模式、键盘操作和未保存提示通过可用性检查。
- [x] 画布生成的“Planner -> Approval -> 两路并行 Agent -> Reducer”策略能通过真实 API 完成 Run 并返回 RunResult。

### 10.6 验收证据

- `uv run ruff check .`：通过。
- `.venv/Scripts/python.exe -m mypy`：53 个 source file 通过 strict 类型检查。
- `.venv/Scripts/python.exe -m pytest -q tests/unit`：52 项通过。
- `.\scripts\test-integration.ps1`：从零迁移 PostgreSQL、启动 Temporal 并完成 8 项集成测试；覆盖 `editorState` 持久化、ETag 冲突、布局不改变 Plan Hash、语义变更改变 Plan Hash，以及 Planner -> Approval -> Parallel 两路 Agent -> Reducer 的真实 REST API、PostgreSQL、Temporal、Worker、RunResult 闭环。
- `pnpm --filter @swarmcore/web lint`、`test`、`build`：通过；Vitest 17 项通过。
- `pnpm --filter @swarmcore/web test:e2e`：Desktop、Tablet、Mobile 共 21 项通过；覆盖空白画布创建、连线与 Parallel 双写、键盘删除、节点移动、保存刷新、发布、窄屏和深色模式。
- `.\scripts\smoke-agno-ollama.ps1`：本机 `qwen3:0.6b` 真实 Agno Model smoke 通过，输出 `AGNO_OLLAMA_SMOKE_OK model=qwen3:0.6b`。
- 下一步唯一最高优先事项：完成 M2B 远端 CI Fake Agent E2E 门禁。

### 10.7 本里程碑不做

- 不改变 SwarmSpec、Compiler、ExecutionPlan 或 Temporal 执行语义。
- 不在运行时未支持前开放 Tool、Team、Router、Loop 或 Subflow 发布。
- 不在首版实现多人实时协同、复杂 Schema 可视化设计器或自动优化布局。
- 不让控制台形成独立的策略执行入口。

## 11. M3：受控 Tool 与编排能力扩展

状态：`PLANNED`

目标：让 Agent 在不直接持有外部凭据的情况下使用受控 Tool，并覆盖实际业务需要的动态编排。

主要交付：

- Agent、Tool、Model Registry 与版本化引用。
- Tool Gateway、GatewayProxyTool 和 Capability Token。
- Tool 输入输出 Schema、风险等级、幂等和审批。
- `tool`、`router`、`loop` 节点进入 Compiler 和 Runtime 支持范围。
- Tool 结果、Agent 输出和 Reducer 的类型衔接。
- Tool 调用事件、成本和审计。

退出标准：

- [ ] Agent 只能通过 Tool Gateway 调用外部能力。
- [ ] 高风险 Tool 必须通过 Approval 才能执行。
- [ ] Activity 重试不会重复产生已确认的外部副作用。
- [ ] Router 和 Loop 具有明确、有界且可回放的执行语义。
- [ ] “并行 Agent -> Tool -> Reducer”真实业务场景通过验收。

## 12. M4：治理、安全与生产能力

状态：`PLANNED`

主要交付：

- OPA Policy、角色、Scope 和 obligations。
- Vault Secret Provider 和短期凭据。
- Artifact Gateway、S3、扫描、保留与下载授权。
- Model Gateway、预算、Token 和成本控制。
- Webhook、审计导出和完整 Observability。
- Sandbox Manager 与不可信代码隔离。
- 可恢复的补偿和外部副作用治理。

退出标准以系统设计第 17、18、20、22 和 26 章为准，并为每项保留安全测试和故障测试证据。

## 13. M5：规模化与生态扩展

状态：`PLANNED`

主要交付：

- Kubernetes 生产拓扑、Worker Autoscaling 和背压。
- NATS、PostgreSQL、Temporal 和 Artifact 高可用。
- 容量压测、Chaos、备份恢复和灾备演练。
- A2A RemoteAgent 和其他 Runtime Adapter。
- 可选向量后端与审计数据出口。

M5 只有在 M2B、M3 和 M4 的产品闭环稳定后启动，避免提前为尚未验证的负载扩容。

## 14. 当前风险与处理顺序

| 优先级 | 风险 | 影响 | 处理方式 |
|---|---|---|---|
| 已关闭 | REST 与 MCP 仍可能产生语义分叉 | DeepTalk 集成不稳定 | M2B-01、M2B-06 已实现并通过契约测试 |
| 已关闭 | 缺少 Capability Catalog、inline Run 和标准 RunResult | DeepTalk 无法独立完成闭环 | M2B-02 至 M2B-05 已实现 |
| 已关闭 | 缺少真实模型凭据 | 无法完成 Agno smoke | 使用本机 Ollama `qwen3:0.6b` 完成受控 smoke |
| 已关闭 | 集成测试环境不可重复 | M1/M2A 无法可靠验收 | M2B-08 已实现并通过从零复验 |
| P1 | Agno Agent 尚未接入受控 Tool | 只能执行有限 Agent 场景 | M3 Tool Gateway |
| P1 | Compiler 与 Runtime 支持节点有限 | 复杂编排无法落地 | M3 按业务优先级逐个扩展 |
| 已关闭 | 策略只能通过 JSON/YAML 编辑 | 人工编排门槛高，难以直观验证拓扑 | M2C Strategy Canvas 已通过验收 |
| P2 | 前端主 Chunk 大于 500 KiB | 控制台加载性能风险 | M2B 后按路由拆包处理 |

## 15. 进度更新规则

每次更新至少记录：

1. `最近更新` 日期和当前基线提交。
2. 当前里程碑及工作项状态。
3. 新完成的交付项。
4. 实际执行的测试及结果。
5. 新增阻塞、风险和决策。
6. 下一步唯一最高优先事项。

状态更新约束：

- 工作项只有合并并通过对应自动化测试后才能标记 `IMPLEMENTED`。
- 里程碑只有全部退出标准通过后才能标记 `VERIFIED`。
- 未执行的测试必须写“未执行”或“待复验”，不能视为通过。
- 产品边界变化更新系统设计；实施顺序和完成情况更新本文档。
- 每个里程碑完成后，在下方追加一条变更记录。

## 16. 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-07-16 | 1.0 | 建立开发计划；登记 M1、M2A 实现状态；将 M2B DeepTalk Integration MVP 设为下一里程碑 |
| 2026-07-16 | 1.1 | 建立隔离 PostgreSQL/Temporal 测试环境；7 项集成测试全绿；M1、M2A 标记为 VERIFIED；下一步 M2B-01 |
| 2026-07-16 | 1.2 | 完成 M2B-01 至 M2B-09 实现和本地验收；M2B 保持 IMPLEMENTED，等待远端 CI 与真实 Agno smoke |
| 2026-07-16 | 1.3 | 使用本机 Ollama 完成真实 Agno Model smoke；修复 provider 依赖与结构化输入警告；M2B 仅待远端 CI Fake Agent E2E |
| 2026-07-16 | 1.4 | 新增 M2C Strategy Canvas 可视化编排计划；固定 SwarmSpec 单一事实源、独立布局持久化、当前可执行节点范围与真实 Run 退出标准 |
| 2026-07-16 | 1.5 | M2C-01 至 M2C-07 全部完成；画布、独立布局、三模式、Compile/Save/Publish、自动化与真实 API RunResult 验收通过，M2C 标记为 VERIFIED |
