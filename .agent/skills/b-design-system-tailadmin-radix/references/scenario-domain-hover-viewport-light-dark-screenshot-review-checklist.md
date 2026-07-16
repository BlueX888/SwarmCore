# Scenario Domain Hover Viewport Light/Dark Screenshot 评审清单

> DOCS-050 / G99 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 Hover 轻量浮层独立截图视觉回归抽检**，确保每个场景 section 在 hover 态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDTC-01～05）、`scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`（SDHO-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图抽检 | 对应 SDHO 块 + `quality-rubric.md` 交互与动效 |
| BI 场景指标 Hover tablet/mobile light/dark golden 对照 | SDHO-01 + `scenario-bi-domain-tablet-hover.png` + `scenario-bi-domain-mobile-dark-hover.png` |
| DevOps 场景阶段 Hover tablet/mobile light/dark golden 对照 | SDHO-02 + `scenario-devops-domain-tablet-hover.png` + `scenario-devops-domain-mobile-dark-hover.png` |
| Gateway 场景端点 Hover tablet/mobile light/dark golden 对照 | SDHO-03 + `scenario-gateway-domain-tablet-hover.png` + `scenario-gateway-domain-mobile-dark-hover.png` |
| Governance 场景审计行 Hover tablet/mobile light/dark golden 对照 | SDHO-04 + `scenario-governance-domain-tablet-hover.png` + `scenario-governance-domain-mobile-dark-hover.png` |
| PaaS 场景容量 Hover tablet/mobile light/dark golden 对照 | SDHO-05 + `scenario-paas-domain-tablet-hover.png` + `scenario-paas-domain-mobile-dark-hover.png` |

## 通用前置

1. 先完成 `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDTC-01～05（Tooltip/Context Menu 打开态独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-hover.png` 四视口双主题 Hover 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 两张 Hover 独立截图，且 hover 面板必须真实出现、移出后消失。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. Hover 截图出现文案裁切、提示框遮挡关键控件到不可读、移出后仍残留面板时，交互与动效质量不得评 95+，综合美学不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图（G99）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图抽检行。

## SDHO-01 — BI 场景指标 Hover tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-hover.png`、`scenario-bi-domain-tablet-dark-hover.png`、`scenario-bi-domain-mobile-hover.png`、`scenario-bi-domain-mobile-dark-hover.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light hover 截图 | `scenario-bi-domain-tablet-hover.png` 存在且 Hover framing 正常 | SDHO-01 · RESP-06 |
| 2 | tablet dark hover 截图 | `scenario-bi-domain-tablet-dark-hover.png` 存在且指标说明可读 | SDHO-01 · VIS-05 |
| 3 | mobile light hover 截图 | `scenario-bi-domain-mobile-hover.png` 指标口径首屏可见 | SDHO-01 · RESP-07 |
| 4 | mobile dark hover 截图 | `scenario-bi-domain-mobile-dark-hover.png` hover 对比度可辨认 | SDHO-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainHoverViewportLightDarkScreenshots` biDomain 全过 | SDHO-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 悬停「悬停查看指标口径」→ 对照 tablet/mobile light/dark 四张 hover 截图 → 移出鼠标确认面板消失。

## SDHO-02 — DevOps 场景阶段 Hover tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-hover.png`、`scenario-devops-domain-tablet-dark-hover.png`、`scenario-devops-domain-mobile-hover.png`、`scenario-devops-domain-mobile-dark-hover.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light hover 截图 | `scenario-devops-domain-tablet-hover.png` 存在且 Hover framing 正常 | SDHO-02 · RESP-06 |
| 2 | tablet dark hover 截图 | `scenario-devops-domain-tablet-dark-hover.png` 存在且阶段说明可读 | SDHO-02 · VIS-05 |
| 3 | mobile light hover 截图 | `scenario-devops-domain-mobile-hover.png` 流水线阶段首屏可见 | SDHO-02 · RESP-07 |
| 4 | mobile dark hover 截图 | `scenario-devops-domain-mobile-dark-hover.png` 提示对比度可辨认 | SDHO-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + Hover tablet/mobile light/dark 可见 | SDHO-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 悬停「悬停查看阶段说明」→ 对照 tablet/mobile light/dark 四张 hover 截图 → 移出鼠标。

## SDHO-03 — Gateway 场景端点 Hover tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-hover.png`、`scenario-gateway-domain-tablet-dark-hover.png`、`scenario-gateway-domain-mobile-hover.png`、`scenario-gateway-domain-mobile-dark-hover.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light hover 截图 | `scenario-gateway-domain-tablet-hover.png` 存在且 Hover framing 正常 | SDHO-03 · RESP-06 |
| 2 | tablet dark hover 截图 | `scenario-gateway-domain-tablet-dark-hover.png` 存在且端点摘要可读 | SDHO-03 · VIS-05 |
| 3 | mobile light hover 截图 | `scenario-gateway-domain-mobile-hover.png` 端点状态首屏可见 | SDHO-03 · RESP-07 |
| 4 | mobile dark hover 截图 | `scenario-gateway-domain-mobile-dark-hover.png` 提示层级不丢失 | SDHO-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + Hover tablet/mobile light/dark 可见 | SDHO-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 悬停「悬停查看端点状态」→ 对照 tablet/mobile light/dark 四张 hover 截图 → 移出鼠标。

## SDHO-04 — Governance 场景审计行 Hover tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-hover.png`、`scenario-governance-domain-tablet-dark-hover.png`、`scenario-governance-domain-mobile-hover.png`、`scenario-governance-domain-mobile-dark-hover.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light hover 截图 | `scenario-governance-domain-tablet-hover.png` 存在且 Hover framing 正常 | SDHO-04 · RESP-06 |
| 2 | tablet dark hover 截图 | `scenario-governance-domain-tablet-dark-hover.png` 存在且审计摘要可读 | SDHO-04 · VIS-05 |
| 3 | mobile light hover 截图 | `scenario-governance-domain-mobile-hover.png` 审计行摘要首屏可见 | SDHO-04 · RESP-07 |
| 4 | mobile dark hover 截图 | `scenario-governance-domain-mobile-dark-hover.png` 提示密度一致 | SDHO-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + Hover tablet/mobile light/dark 可见 | SDHO-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 悬停「悬停查看审计行」→ 对照 tablet/mobile light/dark 四张 hover 截图 → 移出鼠标。

## SDHO-05 — PaaS 场景容量 Hover tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-hover.png`、`scenario-paas-domain-tablet-dark-hover.png`、`scenario-paas-domain-mobile-hover.png`、`scenario-paas-domain-mobile-dark-hover.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light hover 截图 | `scenario-paas-domain-tablet-hover.png` 存在且 Hover framing 正常 | SDHO-05 · RESP-06 |
| 2 | tablet dark hover 截图 | `scenario-paas-domain-tablet-dark-hover.png` 存在且容量摘要可读 | SDHO-05 · VIS-05 |
| 3 | mobile light hover 截图 | `scenario-paas-domain-mobile-hover.png` 容量阈值首屏可见 | SDHO-05 · RESP-07 |
| 4 | mobile dark hover 截图 | `scenario-paas-domain-mobile-dark-hover.png` 列表项可辨认 | SDHO-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + Hover tablet/mobile light/dark 可见 | SDHO-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 悬停「悬停查看容量阈值」→ 对照 tablet/mobile light/dark 四张 hover 截图 → 移出鼠标。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | SDHO-01～05 |
| 场景/页面级 | `scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` | SDHO-06～10 |

## 交叉引用

- `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDTC-01～05
- `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDTC-06～10
- `scene-interaction-review-checklist.md` — INTER-06～10
- `decision-matrix.md` — G99 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDHO-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图检索路径
- `quality-rubric.md` — 交互与动效质量 / 综合美学维度
