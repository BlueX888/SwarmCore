# Scenario Domain Tooltip/Context Menu Interactive Open Viewport Light/Dark Screenshot 评审清单

> DOCS-049 / G98 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 Tooltip/Context Menu 交互态打开态独立截图视觉回归抽检**，确保每个场景 section 在 tooltip/context-menu 浮层打开态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDPC-01～05）、`scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDTC-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图抽检 | 对应 SDTC 块 + `quality-rubric.md` 交互与动效 |
| BI 场景指标 Tooltip tablet/mobile light/dark golden 对照 | SDTC-01 + `scenario-bi-domain-tablet-tooltip-open.png` + `scenario-bi-domain-mobile-dark-tooltip-open.png` |
| DevOps 场景流水线 Context Menu tablet/mobile light/dark golden 对照 | SDTC-02 + `scenario-devops-domain-tablet-context-menu-open.png` + `scenario-devops-domain-mobile-dark-context-menu-open.png` |
| Gateway 场景端点 Tooltip tablet/mobile light/dark golden 对照 | SDTC-03 + `scenario-gateway-domain-tablet-tooltip-open.png` + `scenario-gateway-domain-mobile-dark-tooltip-open.png` |
| Governance 场景审计行 Context Menu tablet/mobile light/dark golden 对照 | SDTC-04 + `scenario-governance-domain-tablet-context-menu-open.png` + `scenario-governance-domain-mobile-dark-context-menu-open.png` |
| PaaS 场景容量 Tooltip tablet/mobile light/dark golden 对照 | SDTC-05 + `scenario-paas-domain-tablet-tooltip-open.png` + `scenario-paas-domain-mobile-dark-tooltip-open.png` |

## 通用前置

1. 先完成 `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDPC-01～05（Dropdown/Popover/Command 打开态独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{tooltip,context-menu}-open.png` 四视口双主题 Tooltip/Context Menu 打开态截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 两张 Tooltip/Context Menu 打开态独立截图，且 tooltip/context-menu 必须真实打开、可关闭。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. Tooltip/Context Menu 打开态截图出现文案裁切、提示框遮挡关键控件到不可读、菜单项越界或关闭路径缺失时，交互与动效质量不得评 95+，综合美学不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图（G98）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图抽检行。

## SDTC-01 — BI 场景指标 Tooltip tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-bi-domain-tablet-tooltip-open.png`、`scenario-bi-domain-tablet-dark-tooltip-open.png`、`scenario-bi-domain-mobile-tooltip-open.png`、`scenario-bi-domain-mobile-dark-tooltip-open.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-bi-domain-tablet-tooltip-open.png` 存在且 Tooltip framing 正常 | SDTC-01 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-bi-domain-tablet-dark-tooltip-open.png` 存在且指标说明可读 | SDTC-01 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-bi-domain-mobile-tooltip-open.png` 指标口径首屏可见 | SDTC-01 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-bi-domain-mobile-dark-tooltip-open.png` 打开态对比度可辨认 | SDTC-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainTooltipContextMenuInteractiveOpenViewportLightDarkScreenshots` biDomain 全过 | SDTC-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 点击「显示指标说明」→ 对照 tablet/mobile light/dark 四张 tooltip 打开态截图 → 关闭提示。

## SDTC-02 — DevOps 场景流水线 Context Menu tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-devops-domain-tablet-context-menu-open.png`、`scenario-devops-domain-tablet-dark-context-menu-open.png`、`scenario-devops-domain-mobile-context-menu-open.png`、`scenario-devops-domain-mobile-dark-context-menu-open.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-devops-domain-tablet-context-menu-open.png` 存在且 Context Menu framing 正常 | SDTC-02 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-devops-domain-tablet-dark-context-menu-open.png` 存在且菜单项可读 | SDTC-02 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-devops-domain-mobile-context-menu-open.png` 流水线操作首屏可见 | SDTC-02 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-devops-domain-mobile-dark-context-menu-open.png` 菜单项对比度可辨认 | SDTC-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + Context Menu 打开态 tablet/mobile light/dark 可见 | SDTC-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 点击「打开流水线右键菜单」→ 对照 tablet/mobile light/dark 四张 context-menu 打开态截图 → 关闭菜单。

## SDTC-03 — Gateway 场景端点 Tooltip tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-gateway-domain-tablet-tooltip-open.png`、`scenario-gateway-domain-tablet-dark-tooltip-open.png`、`scenario-gateway-domain-mobile-tooltip-open.png`、`scenario-gateway-domain-mobile-dark-tooltip-open.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-gateway-domain-tablet-tooltip-open.png` 存在且 Tooltip framing 正常 | SDTC-03 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-gateway-domain-tablet-dark-tooltip-open.png` 存在且探测说明可读 | SDTC-03 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-gateway-domain-mobile-tooltip-open.png` 端点提示首屏可见 | SDTC-03 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-gateway-domain-mobile-dark-tooltip-open.png` 提示层级不丢失 | SDTC-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + Tooltip 打开态 tablet/mobile light/dark 可见 | SDTC-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 点击「显示端点提示」→ 对照 tablet/mobile light/dark 四张 tooltip 打开态截图 → 关闭提示。

## SDTC-04 — Governance 场景审计行 Context Menu tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-governance-domain-tablet-context-menu-open.png`、`scenario-governance-domain-tablet-dark-context-menu-open.png`、`scenario-governance-domain-mobile-context-menu-open.png`、`scenario-governance-domain-mobile-dark-context-menu-open.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-governance-domain-tablet-context-menu-open.png` 存在且 Context Menu framing 正常 | SDTC-04 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-governance-domain-tablet-dark-context-menu-open.png` 存在且操作项可读 | SDTC-04 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-governance-domain-mobile-context-menu-open.png` 审计行操作首屏可见 | SDTC-04 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-governance-domain-mobile-dark-context-menu-open.png` 菜单密度一致 | SDTC-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + Context Menu 打开态 tablet/mobile light/dark 可见 | SDTC-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 点击「打开审计行菜单」→ 对照 tablet/mobile light/dark 四张 context-menu 打开态截图 → 关闭菜单。

## SDTC-05 — PaaS 场景容量 Tooltip tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-paas-domain-tablet-tooltip-open.png`、`scenario-paas-domain-tablet-dark-tooltip-open.png`、`scenario-paas-domain-mobile-tooltip-open.png`、`scenario-paas-domain-mobile-dark-tooltip-open.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-paas-domain-tablet-tooltip-open.png` 存在且 Tooltip framing 正常 | SDTC-05 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-paas-domain-tablet-dark-tooltip-open.png` 存在且阈值说明可读 | SDTC-05 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-paas-domain-mobile-tooltip-open.png` 容量阈值首屏可见 | SDTC-05 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-paas-domain-mobile-dark-tooltip-open.png` 列表项可辨认 | SDTC-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + Tooltip 打开态 tablet/mobile light/dark 可见 | SDTC-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 点击「显示容量阈值说明」→ 对照 tablet/mobile light/dark 四张 tooltip 打开态截图 → 关闭提示。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | SDTC-01～05 |
| 场景/页面级 | `scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` | SDTC-06～10 |

## 交叉引用

- `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDPC-01～05
- `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDPC-06～10
- `scene-interaction-review-checklist.md` — INTER-06～10
- `decision-matrix.md` — G98 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDTC-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图检索路径
- `quality-rubric.md` — 交互与动效质量 / 综合美学维度
