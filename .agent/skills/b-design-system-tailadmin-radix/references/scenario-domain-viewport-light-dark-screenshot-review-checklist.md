# Scenario Domain Viewport Light/Dark Screenshot 评审清单

> DOCS-046 / G95 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题独立截图视觉回归抽检**，确保每个场景 section 在平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-light-dark-screenshot-review-checklist.md`（SDLD-01～05）、`scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md`（SDTM-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 tablet/mobile light/dark 独立截图抽检 | 对应 SDTM 块 + `quality-rubric.md` 综合美学 |
| BI 场景 tablet/mobile light/dark golden 对照 | SDTM-01 + `scenario-bi-domain-tablet.png` + `scenario-bi-domain-mobile-dark.png` |
| DevOps 场景 tablet/mobile light/dark golden 对照 | SDTM-02 + `scenario-devops-domain-tablet.png` + `scenario-devops-domain-mobile-dark.png` |
| Gateway 场景 tablet/mobile light/dark golden 对照 | SDTM-03 + `scenario-gateway-domain-tablet.png` + `scenario-gateway-domain-mobile-dark.png` |
| Governance 场景 tablet/mobile light/dark golden 对照 | SDTM-04 + `scenario-governance-domain-tablet.png` + `scenario-governance-domain-mobile-dark.png` |
| PaaS 场景 tablet/mobile light/dark golden 对照 | SDTM-05 + `scenario-paas-domain-tablet.png` + `scenario-paas-domain-mobile-dark.png` |

## 通用前置

1. 先完成 `scenario-domain-light-dark-screenshot-review-checklist.md` SDLD-01～05（desktop light/dark 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}.png` 四视口双主题截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 两张独立截图，不得只引用 desktop 截图或合并门禁。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. tablet/mobile 任一主题出现对比度不足、边框/背景层级丢失、主任务内容不在首屏或文本裁切时，综合美学不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 tablet/mobile light/dark 独立截图（G95）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 tablet/mobile light/dark 独立截图抽检行。

## SDTM-01 — BI 场景 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet.png`、`scenario-bi-domain-tablet-dark.png`、`scenario-bi-domain-mobile.png`、`scenario-bi-domain-mobile-dark.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 独立截图 | `scenario-bi-domain-tablet.png` 存在且 framing 正常 | SDTM-01 · RESP-06 |
| 2 | tablet dark 独立截图 | `scenario-bi-domain-tablet-dark.png` 存在且 framing 正常 | SDTM-01 · VIS-05 |
| 3 | mobile light 独立截图 | `scenario-bi-domain-mobile.png` 存在且首屏 KPI 可见 | SDTM-01 · RESP-07 |
| 4 | mobile dark 独立截图 | `scenario-bi-domain-mobile-dark.png` 存在且对比度可辨认 | SDTM-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainViewportLightDarkScreenshots` biDomain 全过 | SDTM-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 确认 Data Screen tab → 对照 tablet/mobile light/dark 四张截图。

## SDTM-02 — DevOps 场景 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet.png`、`scenario-devops-domain-tablet-dark.png`、`scenario-devops-domain-mobile.png`、`scenario-devops-domain-mobile-dark.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 独立截图 | `scenario-devops-domain-tablet.png` 存在且 framing 正常 | SDTM-02 · RESP-06 |
| 2 | tablet dark 独立截图 | `scenario-devops-domain-tablet-dark.png` 存在且 framing 正常 | SDTM-02 · VIS-05 |
| 3 | mobile light 独立截图 | `scenario-devops-domain-mobile.png` 流水线首屏可见 | SDTM-02 · RESP-07 |
| 4 | mobile dark 独立截图 | `scenario-devops-domain-mobile-dark.png` 日志区等宽字体可读 | SDTM-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + `.pipeline` tablet/mobile light/dark 画布可见 | SDTM-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 tablet/mobile light/dark 四张截图 → 检查 PipelineStageBar framing。

## SDTM-03 — Gateway 场景 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet.png`、`scenario-gateway-domain-tablet-dark.png`、`scenario-gateway-domain-mobile.png`、`scenario-gateway-domain-mobile-dark.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 独立截图 | `scenario-gateway-domain-tablet.png` 存在且 framing 正常 | SDTM-03 · RESP-06 |
| 2 | tablet dark 独立截图 | `scenario-gateway-domain-tablet-dark.png` 存在且 framing 正常 | SDTM-03 · VIS-05 |
| 3 | mobile light 独立截图 | `scenario-gateway-domain-mobile.png` 部署矩阵首屏可见 | SDTM-03 · RESP-07 |
| 4 | mobile dark 独立截图 | `scenario-gateway-domain-mobile-dark.png` KPI 栅格层级不丢失 | SDTM-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + `.matrix-cards` tablet/mobile light/dark 画布可见 | SDTM-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 tablet/mobile light/dark 四张截图 → 检查 DeploymentModeMatrix framing。

## SDTM-04 — Governance 场景 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet.png`、`scenario-governance-domain-tablet-dark.png`、`scenario-governance-domain-mobile.png`、`scenario-governance-domain-mobile-dark.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 独立截图 | `scenario-governance-domain-tablet.png` 存在且 framing 正常 | SDTM-04 · RESP-06 |
| 2 | tablet dark 独立截图 | `scenario-governance-domain-tablet-dark.png` 存在且 framing 正常 | SDTM-04 · VIS-05 |
| 3 | mobile light 独立截图 | `scenario-governance-domain-mobile.png` 权限矩阵首屏可见 | SDTM-04 · RESP-07 |
| 4 | mobile dark 独立截图 | `scenario-governance-domain-mobile-dark.png` 审计表密度一致 | SDTM-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + `.permission-grid` tablet/mobile light/dark 画布可见 | SDTM-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 tablet/mobile light/dark 四张截图 → 检查 PermissionMatrix framing。

## SDTM-05 — PaaS 场景 tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet.png`、`scenario-paas-domain-tablet-dark.png`、`scenario-paas-domain-mobile.png`、`scenario-paas-domain-mobile-dark.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 独立截图 | `scenario-paas-domain-tablet.png` 存在且 framing 正常 | SDTM-05 · RESP-06 |
| 2 | tablet dark 独立截图 | `scenario-paas-domain-tablet-dark.png` 存在且 framing 正常 | SDTM-05 · VIS-05 |
| 3 | mobile light 独立截图 | `scenario-paas-domain-mobile.png` 容量卡片首屏可见 | SDTM-05 · RESP-07 |
| 4 | mobile dark 独立截图 | `scenario-paas-domain-mobile-dark.png` KPI 可辨认 | SDTM-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + `.capacity-stack` tablet/mobile light/dark 画布可见 | SDTM-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 tablet/mobile light/dark 四张截图 → 检查 CapacityCard framing。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | SDTM-01～05 |
| 场景/页面级 | `scene-scenario-domain-viewport-light-dark-screenshot-review-checklist.md` | SDTM-06～10 |

## 交叉引用

- `scenario-domain-light-dark-screenshot-review-checklist.md` — SDLD-01～05
- `scene-scenario-domain-light-dark-screenshot-review-checklist.md` — SDLD-06～10
- `scene-responsive-review-checklist.md` — RESP-06～10
- `decision-matrix.md` — G95 场景域 tablet/mobile light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDTM-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 tablet/mobile light/dark 独立截图检索路径
- `quality-rubric.md` — 综合美学维度
