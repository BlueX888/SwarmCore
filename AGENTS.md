# SwarmCore Agent Instructions

## 工作原则

1. 修改前先确认需求、影响范围和验证方式。
2. 只修改与当前任务相关的内容，不顺手重构无关代码。
3. 优先复用现有实现和模式，避免引入重复抽象。
4. 行为变更必须补充或更新测试。
5. 不得把未执行的测试描述为已通过。

## 项目边界

- `apps/`：可独立运行的 API、Worker 和 Web 应用。
- `packages/`：领域、应用服务、编译器、持久化、运行时和适配器。
- `tests/unit/`：快速、隔离的单元测试。
- `tests/integration/`：依赖 PostgreSQL、Temporal 等基础设施的集成测试。
- `deployments/compose/`：本地基础设施。
- `docs/swarmcore-system-design.md`：产品边界和架构设计的事实来源。
- `docs/swarmcore-development-plan.md`：里程碑、验收结果和当前进度。
- `agno/`、`agent-ui/`：上游参考代码，不属于 SwarmCore workspace，不要修改。

不要修改 `.venv/`、`node_modules/`、缓存、日志和测试产物。

## 架构约束

- SwarmCore 负责受控、可靠和耐久执行，不承担上游调用方的目标理解。
- REST API 与 MCP 必须复用同一套应用服务，禁止建立两套业务逻辑。
- `packages/domain` 保持领域模型纯净，不依赖 FastAPI、数据库或具体 Agent SDK。
- Temporal Workflow 必须保持确定性；网络、数据库、模型和文件 I/O 放入 Activity。
- Agent SDK 通过 Adapter 接入，业务层不要直接绑定 Agno。
- 数据库结构变更必须新增 Alembic migration，不修改已经使用的历史 migration。
- 多租户数据访问必须保留 tenant/project 边界。
- 条件表达式不得使用 Python `eval`。
- 不得绕过现有的幂等、状态机、Outbox 或审计机制。

## 开发环境

- Python：3.12
- Python workspace：uv
- 前端：React 19、TypeScript、Vite、pnpm
- Python 格式和检查：Ruff、mypy strict
- 测试：pytest、Vitest、Playwright

安装依赖：

```powershell
uv sync --all-packages
pnpm install
```

不要提交 `.env`，新增配置时同步更新 `.env.example`。

## 验证要求

Python 修改至少运行相关测试，并根据影响范围运行：

```powershell
uv run ruff check .
uv run mypy
uv run pytest -q tests/unit
```

前端修改运行：

```powershell
pnpm web:lint
pnpm web:test
pnpm web:build
```

涉及完整交互流程时运行：

```powershell
pnpm web:e2e
```

涉及 PostgreSQL、Temporal、RLS、迁移或跨服务行为时，运行对应集成测试。若环境不具备条件，明确说明哪些测试未执行。

## 文档同步

- 产品目标、系统边界或架构决策变化：更新 `docs/swarmcore-system-design.md`。
- 实施状态或验收结果变化：更新 `docs/swarmcore-development-plan.md`。
- 只有实现完成并通过对应测试后，才能标记为 `IMPLEMENTED` 或 `VERIFIED`。
- 公共 API、配置项或启动方式变化时，同步更新 README 和示例配置。

## 完成标准

交付前确认：

- 修改范围与需求一致；
- 没有意外修改上游参考目录或生成文件；
- 新行为有测试覆盖；
- 静态检查和相关测试已执行；
- 数据库、API 和事件契约保持兼容，或已明确记录破坏性变更；
- 最终说明包含修改内容、验证结果以及未执行的检查。