# Scenario Domain Independent Screenshot 评审清单

> DOCS-044 / G93 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现独立截图视觉回归抽检**，确保每个场景 section 有独立 golden 截图，而非仅依赖合并门禁截图，并与 `scenario-page-visual-regression-review-checklist.md`（SPVR-01～05）、`scene-scenario-page-visual-regression-review-checklist.md`（SPVR-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域独立截图抽检 | 对应 SDIS 块 + `quality-rubric.md` 综合美学 |
| BI 场景独立 golden 对照 | SDIS-01 + `scenario-bi-domain.png` |
| DevOps 场景独立 golden 对照 | SDIS-02 + `scenario-devops-domain.png` |
| Gateway 场景独立 golden 对照 | SDIS-03 + `scenario-gateway-domain.png` |
| Governance 场景独立 golden 对照 | SDIS-04 + `scenario-governance-domain.png` |
| PaaS 场景独立 golden 对照 | SDIS-05 + `scenario-paas-domain.png` |

## 通用前置

1. 先完成 `scenario-page-visual-regression-review-checklist.md` SPVR-01～05（控件级门禁）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-page-visual-regression-gates.png`（合并门禁）。
3. 每个场景域必须有**独立** `scenario-*-domain.png` 截图，不得只引用合并门禁。
4. 视口 **desktop 1440×1000** 首屏宽度利用率 ≥80%。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域独立截图（G93）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域独立截图抽检行。

## SDIS-01 — BI 场景独立截图

**对照 golden**：`scenario-bi-domain.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立截图 | `scenario-bi-domain.png` 存在且 framing 正常 | SDIS-01 · REV-01 |
| 2 | Data Screen tab | BI 场景默认或切换到 Data Screen，画布可见 | SDIS-01 · PAT-06 |
| 3 | KPI 栅格 | 4 列 KPI + 大屏画布首屏可见 | SDIS-01 · VIS-01 |
| 4 | 中文文案 | 指标、筛选、按钮使用中文 mock | SDIS-01 · COPY-01 |
| 5 | example runtime | `verifyScenarioDomainScreenshots` biDomain 全过 | SDIS-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 确认 Data Screen tab → 检查 `bi-analytics-layout` 画布可见 → 对照 `scenario-bi-domain.png`。

## SDIS-02 — DevOps 场景独立截图

**对照 golden**：`scenario-devops-domain.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立截图 | `scenario-devops-domain.png` 存在且 framing 正常 | SDIS-02 · REV-02 |
| 2 | 流水线可见 | PipelineStageBar 6 阶段首屏可见 | SDIS-02 · PAT-07 |
| 3 | 日志区 | LogStreamPanel 固定高度，等宽字体可读 | SDIS-02 · VIS-02 |
| 4 | 中文文案 | 阶段、审批、制品表使用中文 mock | SDIS-02 · COPY-02 |
| 5 | example runtime | `data-audit="scenario-devops"` + `.pipeline` 画布可见 | SDIS-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 检查 PipelineStageBar framing → 对照 `scenario-devops-domain.png`。

## SDIS-03 — Gateway 场景独立截图

**对照 golden**：`scenario-gateway-domain.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立截图 | `scenario-gateway-domain.png` 存在且 framing 正常 | SDIS-03 · REV-03 |
| 2 | 部署矩阵 | DeploymentModeMatrix 4 模式首屏可见 | SDIS-03 · PAT-08 |
| 3 | KPI 栅格 | 4 列网关 KPI 与 EndpointProbeTable 对齐 | SDIS-03 · RESP-03 |
| 4 | 中文文案 | 节点、许可、密钥文案使用中文 mock | SDIS-03 · COPY-03 |
| 5 | example runtime | `data-audit="scenario-gateway"` + `.matrix-cards` 画布可见 | SDIS-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 检查 DeploymentModeMatrix framing → 对照 `scenario-gateway-domain.png`。

## SDIS-04 — Governance 场景独立截图

**对照 golden**：`scenario-governance-domain.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立截图 | `scenario-governance-domain.png` 存在且 framing 正常 | SDIS-04 · REV-04 |
| 2 | 权限矩阵 | PermissionMatrix 行列对齐首屏可见 | SDIS-04 · PAT-09 |
| 3 | 审计日志 | AuditLogTable 时间/操作/结果列密度一致 | SDIS-04 · VIS-04 |
| 4 | 中文文案 | 权限、审计、合规文案使用中文 mock | SDIS-04 · COPY-04 |
| 5 | example runtime | `data-audit="scenario-governance"` + `.permission-grid` 画布可见 | SDIS-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 检查 PermissionMatrix framing → 对照 `scenario-governance-domain.png`。

## SDIS-05 — PaaS 场景独立截图

**对照 golden**：`scenario-paas-domain.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 独立截图 | `scenario-paas-domain.png` 存在且 framing 正常 | SDIS-05 · REV-05 |
| 2 | 容量卡片 | CapacityCard CPU/Memory/Disk 三列首屏可见 | SDIS-05 · PAT-05 |
| 3 | 资源表 | ResourceTable 列宽利用 ≥85% | SDIS-05 · RESP-05 |
| 4 | 中文文案 | 集群、命名空间、容量文案使用中文 mock | SDIS-05 · COPY-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + `.capacity-stack` 画布可见 | SDIS-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 检查 CapacityCard framing → 对照 `scenario-paas-domain.png`。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | SDIS-01～05 |
| 场景/页面级 | `scene-scenario-domain-independent-screenshot-review-checklist.md` | SDIS-06～10 |

## 交叉引用

- `scenario-page-visual-regression-review-checklist.md` — SPVR-01～05
- `scene-scenario-page-visual-regression-review-checklist.md` — SPVR-06～10
- `scene-ui-drift-review-checklist.md` — REV-06～10
- `decision-matrix.md` — G93 场景域独立截图选型表
- `upgrade-troubleshooting.md` — SDIS-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域独立截图检索路径
- `quality-rubric.md` — 综合美学维度
