# Scenario Domain Dropdown/Popover/Command Interactive Open Viewport Light/Dark Screenshot 评审清单

> DOCS-048 / G97 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 Dropdown/Popover/Command 交互态打开态独立截图视觉回归抽检**，确保每个场景 section 在 dropdown/popover/command 浮层打开态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDIO-01～05）、`scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDPC-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图抽检 | 对应 SDPC 块 + `quality-rubric.md` 交互与动效 |
| BI 场景导出 Dropdown tablet/mobile light/dark golden 对照 | SDPC-01 + `scenario-bi-domain-tablet-dropdown-open.png` + `scenario-bi-domain-mobile-dark-dropdown-open.png` |
| DevOps 场景流水线 Popover tablet/mobile light/dark golden 对照 | SDPC-02 + `scenario-devops-domain-tablet-popover-open.png` + `scenario-devops-domain-mobile-dark-popover-open.png` |
| Gateway 场景 Command Palette tablet/mobile light/dark golden 对照 | SDPC-03 + `scenario-gateway-domain-tablet-command-open.png` + `scenario-gateway-domain-mobile-dark-command-open.png` |
| Governance 场景审计筛选 Dropdown tablet/mobile light/dark golden 对照 | SDPC-04 + `scenario-governance-domain-tablet-dropdown-open.png` + `scenario-governance-domain-mobile-dark-dropdown-open.png` |
| PaaS 场景容量 Popover tablet/mobile light/dark golden 对照 | SDPC-05 + `scenario-paas-domain-tablet-popover-open.png` + `scenario-paas-domain-mobile-dark-popover-open.png` |

## 通用前置

1. 先完成 `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDIO-01～05（Dialog/Drawer 打开态独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{dropdown,popover,command}-open.png` 四视口双主题浮层打开态截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 两张浮层打开态独立截图，且 dropdown/popover/command 必须真实打开、可关闭。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 浮层打开态截图出现菜单项裁切、Popover 遮挡关键文案到不可读、Command 面板越界或关闭路径缺失时，交互与动效质量不得评 95+，综合美学不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图（G97）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图抽检行。

## SDPC-01 — BI 场景导出 Dropdown tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-bi-domain-tablet-dropdown-open.png`、`scenario-bi-domain-tablet-dark-dropdown-open.png`、`scenario-bi-domain-mobile-dropdown-open.png`、`scenario-bi-domain-mobile-dark-dropdown-open.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-bi-domain-tablet-dropdown-open.png` 存在且 Dropdown framing 正常 | SDPC-01 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-bi-domain-tablet-dark-dropdown-open.png` 存在且菜单项可读 | SDPC-01 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-bi-domain-mobile-dropdown-open.png` 导出菜单首屏可见 | SDPC-01 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-bi-domain-mobile-dark-dropdown-open.png` 打开态对比度可辨认 | SDPC-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainFloatingInteractiveOpenViewportLightDarkScreenshots` biDomain 全过 | SDPC-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 点击「打开导出菜单」→ 对照 tablet/mobile light/dark 四张 dropdown 打开态截图 → 关闭菜单。

## SDPC-02 — DevOps 场景流水线 Popover tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-devops-domain-tablet-popover-open.png`、`scenario-devops-domain-tablet-dark-popover-open.png`、`scenario-devops-domain-mobile-popover-open.png`、`scenario-devops-domain-mobile-dark-popover-open.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-devops-domain-tablet-popover-open.png` 存在且 Popover framing 正常 | SDPC-02 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-devops-domain-tablet-dark-popover-open.png` 存在且说明文案可读 | SDPC-02 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-devops-domain-mobile-popover-open.png` 流水线说明首屏可见 | SDPC-02 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-devops-domain-mobile-dark-popover-open.png` 列表项对比度可辨认 | SDPC-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + 浮层打开态 tablet/mobile light/dark 可见 | SDPC-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 点击「打开流水线说明」→ 对照 tablet/mobile light/dark 四张 popover 打开态截图 → 关闭 Popover。

## SDPC-03 — Gateway 场景 Command Palette tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-gateway-domain-tablet-command-open.png`、`scenario-gateway-domain-tablet-dark-command-open.png`、`scenario-gateway-domain-mobile-command-open.png`、`scenario-gateway-domain-mobile-dark-command-open.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-gateway-domain-tablet-command-open.png` 存在且 Command framing 正常 | SDPC-03 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-gateway-domain-tablet-dark-command-open.png` 存在且命令项可读 | SDPC-03 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-gateway-domain-mobile-command-open.png` 快速命令首屏可见 | SDPC-03 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-gateway-domain-mobile-dark-command-open.png` 搜索框与命令层级不丢失 | SDPC-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + Command 浮层 tablet/mobile light/dark 可见 | SDPC-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 点击「打开快速命令」→ 对照 tablet/mobile light/dark 四张 command 打开态截图 → 关闭 Command。

## SDPC-04 — Governance 场景审计筛选 Dropdown tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-governance-domain-tablet-dropdown-open.png`、`scenario-governance-domain-tablet-dark-dropdown-open.png`、`scenario-governance-domain-mobile-dropdown-open.png`、`scenario-governance-domain-mobile-dark-dropdown-open.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-governance-domain-tablet-dropdown-open.png` 存在且 Dropdown framing 正常 | SDPC-04 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-governance-domain-tablet-dark-dropdown-open.png` 存在且筛选项可读 | SDPC-04 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-governance-domain-mobile-dropdown-open.png` 审计筛选首屏可见 | SDPC-04 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-governance-domain-mobile-dark-dropdown-open.png` 菜单密度一致 | SDPC-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + Dropdown 浮层 tablet/mobile light/dark 可见 | SDPC-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 点击「打开审计筛选」→ 对照 tablet/mobile light/dark 四张 dropdown 打开态截图 → 关闭菜单。

## SDPC-05 — PaaS 场景容量 Popover tablet/mobile light/dark 打开态独立截图

**对照 golden**：`scenario-paas-domain-tablet-popover-open.png`、`scenario-paas-domain-tablet-dark-popover-open.png`、`scenario-paas-domain-mobile-popover-open.png`、`scenario-paas-domain-mobile-dark-popover-open.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light 打开态截图 | `scenario-paas-domain-tablet-popover-open.png` 存在且 Popover framing 正常 | SDPC-05 · RESP-06 |
| 2 | tablet dark 打开态截图 | `scenario-paas-domain-tablet-dark-popover-open.png` 存在且阈值说明可读 | SDPC-05 · VIS-05 |
| 3 | mobile light 打开态截图 | `scenario-paas-domain-mobile-popover-open.png` 容量提示首屏可见 | SDPC-05 · RESP-07 |
| 4 | mobile dark 打开态截图 | `scenario-paas-domain-mobile-dark-popover-open.png` 列表项可辨认 | SDPC-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + Popover 浮层 tablet/mobile light/dark 可见 | SDPC-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 点击「打开容量提示」→ 对照 tablet/mobile light/dark 四张 popover 打开态截图 → 关闭 Popover。

## 完整路径

| 层级 | 清单 | ID 范围 |
|---|---|---|
| 控件级 | 本文件 | SDPC-01～05 |
| 场景/页面级 | `scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` | SDPC-06～10 |

## 交叉引用

- `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDIO-01～05
- `scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDIO-06～10
- `scene-interaction-review-checklist.md` — INTER-06～10
- `decision-matrix.md` — G97 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDPC-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图检索路径
- `quality-rubric.md` — 交互与动效质量 / 综合美学维度
