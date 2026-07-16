# 场景 Scenario Domain Tooltip/Context Menu Interactive Open Viewport Light/Dark Screenshot 评审清单

> DOCS-049 / G98 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 Tooltip/Context Menu 交互态打开态独立截图抽检**，确保各域 section 在 Tooltip/Context Menu 打开态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDTC-01～05）、`scene-scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDPC-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDTC 块 + `quality-rubric.md` |
| BI Analytics 指标 Tooltip tablet/mobile light/dark 打开态独立截图 | SDTC-06 + `tailadmin-bi-analytics` |
| DevOps 流水线 Context Menu tablet/mobile light/dark 打开态独立截图 | SDTC-07 + `scenario-devops` |
| Gateway 端点 Tooltip tablet/mobile light/dark 打开态独立截图 | SDTC-08 + `scenario-gateway` |
| Governance 审计行 Context Menu tablet/mobile light/dark 打开态独立截图 | SDTC-09 + `scenario-governance` |
| 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图束缺门禁 | SDTC-10 + `verify:runtime` `scenarioDomainTooltipContextMenuInteractiveOpenViewportLightDarkScreenshotStates` + `verifyScenarioDomainTooltipContextMenuInteractiveOpenViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` SDTC-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{tooltip,context-menu}-open.png` 共 20 张 Tooltip/Context Menu 打开态独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark Tooltip/Context Menu 打开态独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图（G98）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图抽检行。
7. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDTC-06 — BI Analytics 指标 Tooltip tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-tooltip-open.png`、`scenario-bi-domain-mobile-dark-tooltip-open.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-bi-domain-tablet-tooltip-open.png` + `scenario-bi-domain-tablet-dark-tooltip-open.png` Tooltip framing 正常 | SDTC-06 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-bi-domain-mobile-tooltip-open.png` + `scenario-bi-domain-mobile-dark-tooltip-open.png` Tooltip framing 正常 | SDTC-06 · RESP-07 |
| 3 | 指标口径 | 总收入指标口径/刷新频率 tablet/mobile light/dark 首屏可见 | SDTC-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下提示边框/背景/文字层级可辨认 | SDTC-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 四视口双主题 tooltip 打开态截图全过 | SDTC-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 点击「显示指标说明」→ 对照 tablet/mobile light/dark 四张 tooltip 打开态截图 → 关闭提示。

## SDTC-07 — DevOps 流水线 Context Menu tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-context-menu-open.png`、`scenario-devops-domain-mobile-dark-context-menu-open.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-devops-domain-tablet-context-menu-open.png` + `scenario-devops-domain-tablet-dark-context-menu-open.png` Context Menu framing 正常 | SDTC-07 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-devops-domain-mobile-context-menu-open.png` + `scenario-devops-domain-mobile-dark-context-menu-open.png` Context Menu framing 正常 | SDTC-07 · RESP-07 |
| 3 | 流水线操作 | 重新运行/跳过/查看日志 tablet/mobile light/dark 首屏可见 | SDTC-07 · PAT-07 |
| 4 | 关闭路径 | mobile dark 下关闭按钮可读且可关闭 | SDTC-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 四视口双主题 context-menu 打开态截图全过 | SDTC-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 点击「打开流水线右键菜单」→ 对照 tablet/mobile light/dark 四张 context-menu 打开态截图 → 关闭菜单。

## SDTC-08 — Gateway 端点 Tooltip tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-tooltip-open.png`、`scenario-gateway-domain-mobile-dark-tooltip-open.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-gateway-domain-tablet-tooltip-open.png` + `scenario-gateway-domain-tablet-dark-tooltip-open.png` Tooltip framing 正常 | SDTC-08 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-gateway-domain-mobile-tooltip-open.png` + `scenario-gateway-domain-mobile-dark-tooltip-open.png` Tooltip framing 正常 | SDTC-08 · RESP-07 |
| 3 | 端点探测说明 | 探测超时/告警阈值 tablet/mobile light/dark 首屏可见 | SDTC-08 · PAT-08 |
| 4 | 提示层级 | mobile dark 下说明文案与列表层级不丢失 | SDTC-08 · RESP-08 |
| 5 | example runtime | Gateway 场景 section + 四视口双主题 tooltip 打开态截图全过 | SDTC-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 点击「显示端点提示」→ 对照 tablet/mobile light/dark 四张 tooltip 打开态截图 → 关闭提示。

## SDTC-09 — Governance 审计行 Context Menu tablet/mobile light/dark 打开态独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-context-menu-open.png`、`scenario-governance-domain-mobile-dark-context-menu-open.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark 打开态 | `scenario-governance-domain-tablet-context-menu-open.png` + `scenario-governance-domain-tablet-dark-context-menu-open.png` Context Menu framing 正常 | SDTC-09 · RESP-06 |
| 2 | mobile light/dark 打开态 | `scenario-governance-domain-mobile-context-menu-open.png` + `scenario-governance-domain-mobile-dark-context-menu-open.png` Context Menu framing 正常 | SDTC-09 · RESP-07 |
| 3 | 审计行操作 | 查看详情/导出单条/标记复核 tablet/mobile light/dark 首屏可见 | SDTC-09 · PAT-09 |
| 4 | 关闭路径 | mobile dark 下关闭菜单按钮可读 | SDTC-09 · INTER-09 |
| 5 | example runtime | Governance 场景 section + 四视口双主题 context-menu 打开态截图全过 | SDTC-09 · PREVIEW-* |

**交互动作**：打开治理场景 → 点击「打开审计行菜单」→ 对照 tablet/mobile light/dark 四张 context-menu 打开态截图 → 关闭菜单。

## SDTC-10 — 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图束

**对照 golden**：20 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{tooltip,context-menu}-open.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 截图数量 | 20 张 Tooltip/Context Menu 打开态截图全部存在 | SDTC-10 · VAL-* |
| 2 | runtime 门禁 | `tooltipContextOpenStateMatrixComplete = true` + `verifyScenarioDomainTooltipContextMenuInteractiveOpenViewportLightDarkScreenshots` | SDTC-10 · PREVIEW-* |
| 3 | 五域覆盖 | BI tooltip、DevOps context-menu、Gateway tooltip、Governance context-menu、PaaS tooltip 均有打开态 | SDTC-10 · COV-06 |
| 4 | 关闭路径 | 每个域打开态截图后均可通过关闭按钮/Escape 关闭 | SDTC-10 · INTER-10 |
| 5 | 交叉引用 | SDTC-01～09 + decision-matrix G98 + upgrade-troubleshooting SDTC 症状 | SDTC-10 · GEN-06 |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 `scenarioDomainTooltipContextMenuInteractiveOpenViewportLightDarkScreenshotStates` 全过。

## 交叉引用

- `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDTC-01～05
- `scenario-domain-dropdown-popover-command-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDPC-01～05
- `decision-matrix.md` — G98 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDTC-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 Tooltip/Context Menu 交互态打开态 tablet/mobile light/dark 独立截图检索路径
