# Scenario Domain Light/Dark Screenshot 评审清单

> DOCS-045 / G94 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 light/dark 双主题独立截图视觉回归抽检**，确保每个场景 section 在浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-independent-screenshot-review-checklist.md`（SDIS-01～05）、`scene-scenario-domain-light-dark-screenshot-review-checklist.md`（SDLD-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 light/dark 独立截图抽检 | 对应 SDLD 块 + `quality-rubric.md` 综合美学 |
| BI 场景 light/dark golden 对照 | SDLD-01 + `scenario-bi-domain.png` + `scenario-bi-domain-dark.png` |
| DevOps 场景 light/dark golden 对照 | SDLD-02 + `scenario-devops-domain.png` + `scenario-devops-domain-dark.png` |
| Gateway 场景 light/dark golden 对照 | SDLD-03 + `scenario-gateway-domain.png` + `scenario-gateway-domain-dark.png` |
| Governance 场景 light/dark golden 对照 | SDLD-04 + `scenario-governance-domain.png` + `scenario-governance-domain-dark.png` |
| PaaS 场景 light/dark golden 对照 | SDLD-05 + `scenario-paas-domain.png` + `scenario-paas-domain-dark.png` |

## 通用前置

1. 先完成 `scenario-domain-independent-screenshot-review-checklist.md` SDIS-01～05（light 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain.png` 与 `scenario-*-domain-dark.png` 双主题截图。
3. 每个场景域必须有 **light + dark** 两张独立截图，不得只引用 light 截图或合并门禁。
4. 视口 **desktop 1440×1000**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. light/dark 任一主题出现对比度不足、边框/背景层级丢失或主要控件不可辨认时，综合美学不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 light/dark 独立截图（G94）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 light/dark 独立截图抽检行。

## SDLD-01 — BI 场景 light/dark 独立截图

**对照 golden**：`scenario-bi-domain.png`、`scenario-bi-domain-dark.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light 独立截图 | `scenario-bi-domain.png` 存在且 framing 正常 | SDLD-01 · REV-01 |
| 2 | dark 独立截图 | `scenario-bi-domain-dark.png` 存在且 framing 正常 | SDLD-01 · VIS-05 |
| 3 | Data Screen tab | BI 场景 light/dark 均切换到 Data Screen，画布可见 | SDLD-01 · PAT-06 |
| 4 | 主题对比 | dark 下 KPI/图表 grid/legend 边框背景文字层级可辨认 | SDLD-01 · VIS-05 |
| 5 | example runtime | `verifyScenarioDomainLightDarkScreenshots` biDomain 全过 | SDLD-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 确认 Data Screen tab → 对照 light 截图 → 点击「切换主题」→ 对照 dark 截图。

## SDLD-02 — DevOps 场景 light/dark 独立截图

**对照 golden**：`scenario-devops-domain.png`、`scenario-devops-domain-dark.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light 独立截图 | `scenario-devops-domain.png` 存在且 framing 正常 | SDLD-02 · REV-02 |
| 2 | dark 独立截图 | `scenario-devops-domain-dark.png` 存在且 framing 正常 | SDLD-02 · VIS-05 |
| 3 | 流水线可见 | PipelineStageBar 6 阶段 light/dark 首屏可见 | SDLD-02 · PAT-07 |
| 4 | 日志区 | LogStreamPanel 等宽字体在 dark 下可读 | SDLD-02 · VIS-02 |
| 5 | example runtime | `data-audit="scenario-devops"` + `.pipeline` light/dark 画布可见 | SDLD-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 light/dark 双截图 → 检查 PipelineStageBar framing。

## SDLD-03 — Gateway 场景 light/dark 独立截图

**对照 golden**：`scenario-gateway-domain.png`、`scenario-gateway-domain-dark.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light 独立截图 | `scenario-gateway-domain.png` 存在且 framing 正常 | SDLD-03 · REV-03 |
| 2 | dark 独立截图 | `scenario-gateway-domain-dark.png` 存在且 framing 正常 | SDLD-03 · VIS-05 |
| 3 | 部署矩阵 | DeploymentModeMatrix 4 模式 light/dark 首屏可见 | SDLD-03 · PAT-08 |
| 4 | KPI 栅格 | 4 列网关 KPI dark 下边框/背景层级不丢失 | SDLD-03 · RESP-03 |
| 5 | example runtime | `data-audit="scenario-gateway"` + `.matrix-cards` light/dark 画布可见 | SDLD-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 light/dark 双截图 → 检查 DeploymentModeMatrix framing。

## SDLD-04 — Governance 场景 light/dark 独立截图

**对照 golden**：`scenario-governance-domain.png`、`scenario-governance-domain-dark.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light 独立截图 | `scenario-governance-domain.png` 存在且 framing 正常 | SDLD-04 · REV-04 |
| 2 | dark 独立截图 | `scenario-governance-domain-dark.png` 存在且 framing 正常 | SDLD-04 · VIS-05 |
| 3 | 权限矩阵 | PermissionMatrix 行列对齐 light/dark 首屏可见 | SDLD-04 · PAT-09 |
| 4 | 审计日志 | AuditLogTable dark 下时间/操作/结果列密度一致 | SDLD-04 · VIS-04 |
| 5 | example runtime | `data-audit="scenario-governance"` + `.permission-grid` light/dark 画布可见 | SDLD-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 light/dark 双截图 → 检查 PermissionMatrix framing。

## SDLD-05 — PaaS 场景 light/dark 独立截图

**对照 golden**：`scenario-paas-domain.png`、`scenario-paas-domain-dark.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | light 独立截图 | `scenario-paas-domain.png` 存在且 framing 正常 | SDLD-05 · REV-05 |
| 2 | dark 独立截图 | `scenario-paas-domain-dark.png` 存在且 framing 正常 | SDLD-05 · VIS-05 |
| 3 | 容量卡片 | CapacityCard CPU/Memory/Disk 三列 light/dark 首屏可见 | SDLD-05 · PAT-05 |
| 4 | 资源表 | ResourceTable dark 下列宽利用 ≥85% | SDLD-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + `.capacity-stack` light/dark 画布可见 | SDLD-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 light/dark 双截图 → 检查 CapacityCard framing。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | SDLD-01～05 |
| 场景/页面级 | `scene-scenario-domain-light-dark-screenshot-review-checklist.md` | SDLD-06～10 |

## 交叉引用

- `scenario-domain-independent-screenshot-review-checklist.md` — SDIS-01～05
- `scene-scenario-domain-independent-screenshot-review-checklist.md` — SDIS-06～10
- `page-family-visual-regression-review-checklist.md` — PFVR-05 主题对比
- `decision-matrix.md` — G94 场景域 light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDLD-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 light/dark 独立截图检索路径
- `quality-rubric.md` — 综合美学维度
