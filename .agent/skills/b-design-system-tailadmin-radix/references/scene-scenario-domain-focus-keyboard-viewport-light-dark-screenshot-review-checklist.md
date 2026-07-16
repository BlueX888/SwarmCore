# 场景 Scenario Domain Focus Keyboard Viewport Light/Dark Screenshot 评审清单

> DOCS-051 / G100 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 Focus 态与键盘导航独立截图抽检**，确保各域 section 在 Focus 态、方向键导航、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`（SDFK-01～05）、`scene-scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`（SDHO-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDFK 块 + `quality-rubric.md` |
| BI Analytics 指标 Focus tablet/mobile light/dark 独立截图 | SDFK-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 Focus tablet/mobile light/dark 独立截图 | SDFK-07 + `scenario-devops` |
| Gateway 端点 Focus tablet/mobile light/dark 独立截图 | SDFK-08 + `scenario-gateway` |
| Governance 审计行 Focus tablet/mobile light/dark 独立截图 | SDFK-09 + `scenario-governance` |
| 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图束缺门禁 | SDFK-10 + `verify:runtime` `scenarioDomainFocusKeyboardViewportLightDarkScreenshotStates` + `verifyScenarioDomainFocusKeyboardViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` SDFK-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-focus.png` 共 20 张 Focus 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark Focus 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图（G100）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDFK-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDFK-06 — BI Analytics 指标 Focus tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-focus.png`、`scenario-bi-domain-mobile-dark-focus.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark focus | `scenario-bi-domain-tablet-focus.png` + `scenario-bi-domain-tablet-dark-focus.png` Focus framing 正常 | SDFK-06 · RESP-06 |
| 2 | mobile light/dark focus | `scenario-bi-domain-mobile-focus.png` + `scenario-bi-domain-mobile-dark-focus.png` Focus framing 正常 | SDFK-06 · RESP-07 |
| 3 | 指标导航 | 总收入 Focus 导航/口径版本 tablet/mobile light/dark 首屏可见 | SDFK-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 focus 边框/背景/文字层级可辨认 | SDFK-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 四视口双主题 focus 截图全过 | SDFK-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → Tab 聚焦触发按钮 → ArrowDown 切换高亮项 → 对照 tablet/mobile light/dark 四张 focus 截图 → Esc 关闭。

## SDFK-07 — DevOps 阶段 Focus tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-focus.png`、`scenario-devops-domain-mobile-dark-focus.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark focus | `scenario-devops-domain-tablet-focus.png` + `scenario-devops-domain-tablet-dark-focus.png` Focus framing 正常 | SDFK-07 · RESP-06 |
| 2 | mobile light/dark focus | `scenario-devops-domain-mobile-focus.png` + `scenario-devops-domain-mobile-dark-focus.png` Focus framing 正常 | SDFK-07 · RESP-07 |
| 3 | 阶段导航 | 灰度阶段/流量比例 tablet/mobile light/dark 首屏可见 | SDFK-07 · PAT-07 |
| 4 | Esc 关闭 | mobile dark 下按 Esc 后 focus 面板消失 | SDFK-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 四视口双主题 focus 截图全过 | SDFK-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → Tab 聚焦 → ArrowDown → 对照 tablet/mobile light/dark 四张 focus 截图 → Esc。

## SDFK-08 — Gateway 端点 Focus tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-focus.png`、`scenario-gateway-domain-mobile-dark-focus.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark focus | `scenario-gateway-domain-tablet-focus.png` + `scenario-gateway-domain-tablet-dark-focus.png` Focus framing 正常 | SDFK-08 · RESP-06 |
| 2 | mobile light/dark focus | `scenario-gateway-domain-mobile-focus.png` + `scenario-gateway-domain-mobile-dark-focus.png` Focus framing 正常 | SDFK-08 · RESP-07 |
| 3 | 端点导航 | 在线端点/探测摘要 tablet/mobile light/dark 首屏可见 | SDFK-08 · PAT-08 |
| 4 | 方向键 | mobile dark 下 ArrowDown 高亮项切换可见 | SDFK-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 四视口双主题 focus 截图全过 | SDFK-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → Tab 聚焦 → ArrowDown → 对照 tablet/mobile light/dark 四张 focus 截图 → Esc。

## SDFK-09 — Governance 审计行 Focus tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-focus.png`、`scenario-governance-domain-mobile-dark-focus.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark focus | `scenario-governance-domain-tablet-focus.png` + `scenario-governance-domain-tablet-dark-focus.png` Focus framing 正常 | SDFK-09 · RESP-06 |
| 2 | mobile light/dark focus | `scenario-governance-domain-mobile-focus.png` + `scenario-governance-domain-mobile-dark-focus.png` Focus framing 正常 | SDFK-09 · RESP-07 |
| 3 | 审计导航 | 操作/执行人/状态 tablet/mobile light/dark 首屏可见 | SDFK-09 · PAT-09 |
| 4 | focus 环 | mobile dark 下 focus-visible 环可辨认 | SDFK-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 四视口双主题 focus 截图全过 | SDFK-09 · PREVIEW-* |

**交互动作**：打开治理场景 → Tab 聚焦 → ArrowDown → 对照 tablet/mobile light/dark 四张 focus 截图 → Esc。

## SDFK-10 — 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图束

**对照 golden**：20 张 `scenario-*-domain-{tablet,mobile}{,-dark}-focus.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 截图数量 | 5 域 × 2 视口 × 2 主题 = 20 张 `-focus.png` 全存在 | SDFK-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainFocusKeyboardViewportLightDarkScreenshots` 全过 | SDFK-10 · PREVIEW-* |
| 3 | focusStateMatrixComplete | `scenarioDomainFocusKeyboardViewportLightDarkScreenshotStates.focusStateMatrixComplete = true` | SDFK-10 · VAL-* |
| 4 | 方向键导航 | 五域 `data-active-index` 在 ArrowDown 后 ≥ 1 | SDFK-10 · INTER-* |
| 5 | Esc 关闭 | 五域 Esc 后 `scenario-domain-focus-overlay` 从 DOM 移除 | SDFK-10 · A11Y-* |

**交互动作**：逐域 Tab 聚焦 → ArrowDown → 截图 → Esc → 确认 `focusStateMatrixComplete = true`。
