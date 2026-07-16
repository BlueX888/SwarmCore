# 场景 Scenario Domain Dropdown/Popover/Command Interactive Open Viewport Light/Dark Screenshot 评审清单

> DOCS-048 / G97 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 Dropdown/Popover/Command 交互态打开态独立截图抽检**，确保各域 section 在浮层打开态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDPC-01～05）、`scene-scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDIO-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDPC 块 + `quality-rubric.md` |
| BI Analytics 导出 Dropdown tablet/mobile light/dark 打开态独立截图 | SDPC-06 + `tailadmin-bi-analytics` |
| DevOps 流水线 Popover tablet/mobile light/dark 打开态独立截图 | SDPC-07 + `scenario-devops` |
| Gateway Command Palette tablet/mobile light/dark 打开态独立截图 | SDPC-08 + `scenario-gateway` |
| Governance 审计筛选 Dropdown tablet/mobile light/dark 打开态独立截图 | SDPC-09 + `scenario-governance` |
| 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图束缺门禁 | SDPC-10 + `verify:runtime` `scenarioDomainFloatingInteractiveOpenViewportLightDarkScreenshotStates` |

## 通用前置

1. 先完成 `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDPC-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{dropdown,popover,command}-open.png` 共 20 张浮层打开态独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark 浮层打开态独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图（G97）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图抽检行。

## SDPC-06 — BI Analytics 导出 Dropdown tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-dropdown-open.png`、`scenario-bi-domain-mobile-dark-dropdown-open.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-bi-domain-tablet-dropdown-open.png` + `scenario-bi-domain-tablet-dark-dropdown-open.png` Dropdown framing 正常 | SDPC-06 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-bi-domain-mobile-dropdown-open.png` + `scenario-bi-domain-mobile-dark-dropdown-open.png` Dropdown framing 正常 | SDPC-06 · RESP-07 |
| 3 | 导出菜单 | 导出 PNG/PDF/Excel/订阅周报 菜单项 tablet/mobile light/dark 首屏可见 | SDPC-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下菜单边框/背景/文字层级可辨认 | SDPC-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 四视口双主题 dropdown 打开态截图全过 | SDPC-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 点击「打开导出菜单」→ 对照 tablet/mobile light/dark 四张 dropdown 打开态截图 → 关闭菜单。

## SDPC-07 — DevOps 流水线 Popover tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-popover-open.png`、`scenario-devops-domain-mobile-dark-popover-open.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-devops-domain-tablet-popover-open.png` + `scenario-devops-domain-tablet-dark-popover-open.png` Popover framing 正常 | SDPC-07 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-devops-domain-mobile-popover-open.png` + `scenario-devops-domain-mobile-dark-popover-open.png` Popover framing 正常 | SDPC-07 · RESP-07 |
| 3 | 流水线说明 | 灰度发布阶段说明 tablet/mobile light/dark 首屏可见 | SDPC-07 · PAT-07 |
| 4 | 关闭路径 | mobile dark 下关闭按钮可读且可关闭 | SDPC-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 四视口双主题 popover 打开态截图全过 | SDPC-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 点击「打开流水线说明」→ 对照 tablet/mobile light/dark 四张 popover 打开态截图 → 关闭 Popover。

## SDPC-08 — Gateway Command Palette tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-command-open.png`、`scenario-gateway-domain-mobile-dark-command-open.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-gateway-domain-tablet-command-open.png` + `scenario-gateway-domain-tablet-dark-command-open.png` Command framing 正常 | SDPC-08 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-gateway-domain-mobile-command-open.png` + `scenario-gateway-domain-mobile-dark-command-open.png` Command framing 正常 | SDPC-08 · RESP-07 |
| 3 | 快速命令 | 控制平面/创建 API Key 等命令 tablet/mobile light/dark 首屏可见 | SDPC-08 · PAT-08 |
| 4 | 搜索框层级 | mobile dark 下搜索框与命令列表层级不丢失 | SDPC-08 · RESP-08 |
| 5 | example runtime | Gateway 场景 section + 四视口双主题 command 打开态截图全过 | SDPC-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 点击「打开快速命令」→ 对照 tablet/mobile light/dark 四张 command 打开态截图 → 关闭 Command。

## SDPC-09 — Governance 审计筛选 Dropdown tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-dropdown-open.png`、`scenario-governance-domain-mobile-dark-dropdown-open.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-governance-domain-tablet-dropdown-open.png` + `scenario-governance-domain-tablet-dark-dropdown-open.png` Dropdown framing 正常 | SDPC-09 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-governance-domain-mobile-dropdown-open.png` + `scenario-governance-domain-mobile-dark-dropdown-open.png` Dropdown framing 正常 | SDPC-09 · RESP-07 |
| 3 | 审计筛选 | 全部操作/登录失败/权限变更 筛选项 tablet/mobile light/dark 首屏可见 | SDPC-09 · PAT-09 |
| 4 | 关闭路径 | mobile dark 下关闭菜单按钮可读 | SDPC-09 · INTER-09 |
| 5 | example runtime | Governance 场景 section + 四视口双主题 dropdown 打开态截图全过 | SDPC-09 · PREVIEW-* |

**交互动作**：打开治理场景 → 点击「打开审计筛选」→ 对照 tablet/mobile light/dark 四张 dropdown 打开态截图 → 关闭菜单。

## SDPC-10 — 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图束

**对照 golden**：20 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{dropdown,popover,command}-open.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 截图束完整 | `verifyScenarioDomainFloatingInteractiveOpenViewportLightDarkScreenshots` 返回 `floatingOpenStateMatrixComplete = true` | SDPC-10 · VAL-* |
| 2 | BI dropdown | 四张 `scenario-bi-domain-*-dropdown-open.png` 存在 | SDPC-10 · SDPC-01 |
| 3 | DevOps/Gateway popover/command | DevOps popover + Gateway command 各四张打开态截图存在 | SDPC-10 · SDPC-02/03 |
| 4 | Governance/PaaS | Governance dropdown + PaaS popover 各四张打开态截图存在 | SDPC-10 · SDPC-04/05 |
| 5 | 反向审计 | 缺任一域 tablet/mobile dark 浮层打开态截图时不得评交互与动效 95+ | SDPC-10 · INTER-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 20 张浮层打开态截图生成且 `floatingOpenStateMatrixComplete = true`。

## 交叉引用

- `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDPC-01～05
- `scenario-domain-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDIO-01～05
- `decision-matrix.md` — G97 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图选型表
- `business-validation-checklist.md` — MS-09～13 业务验证交叉引用
- `upgrade-troubleshooting.md` — SDPC-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 Dropdown/Popover/Command 交互态打开态 tablet/mobile light/dark 独立截图检索路径
