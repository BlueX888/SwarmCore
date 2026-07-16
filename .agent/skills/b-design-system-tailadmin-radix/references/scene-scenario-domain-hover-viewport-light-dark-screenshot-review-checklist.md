# 场景 Scenario Domain Hover Viewport Light/Dark Screenshot 评审清单

> DOCS-050 / G99 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 Hover 轻量浮层独立截图抽检**，确保各域 section 在 Hover 态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`（SDHO-01～05）、`scene-scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md`（SDTC-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDHO 块 + `quality-rubric.md` |
| BI Analytics 指标 Hover tablet/mobile light/dark 独立截图 | SDHO-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 Hover tablet/mobile light/dark 独立截图 | SDHO-07 + `scenario-devops` |
| Gateway 端点 Hover tablet/mobile light/dark 独立截图 | SDHO-08 + `scenario-gateway` |
| Governance 审计行 Hover tablet/mobile light/dark 独立截图 | SDHO-09 + `scenario-governance` |
| 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图束缺门禁 | SDHO-10 + `verify:runtime` `scenarioDomainHoverViewportLightDarkScreenshotStates` + `verifyScenarioDomainHoverViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` SDHO-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-hover.png` 共 20 张 Hover 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark Hover 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图（G99）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图抽检行。
7. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDHO-06 — BI Analytics 指标 Hover tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-hover.png`、`scenario-bi-domain-mobile-dark-hover.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark hover | `scenario-bi-domain-tablet-hover.png` + `scenario-bi-domain-tablet-dark-hover.png` Hover framing 正常 | SDHO-06 · RESP-06 |
| 2 | mobile light/dark hover | `scenario-bi-domain-mobile-hover.png` + `scenario-bi-domain-mobile-dark-hover.png` Hover framing 正常 | SDHO-06 · RESP-07 |
| 3 | 指标口径 | 总收入 Hover 提示/口径版本 tablet/mobile light/dark 首屏可见 | SDHO-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 hover 边框/背景/文字层级可辨认 | SDHO-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 四视口双主题 hover 截图全过 | SDHO-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 悬停「悬停查看指标口径」→ 对照 tablet/mobile light/dark 四张 hover 截图 → 移出鼠标。

## SDHO-07 — DevOps 阶段 Hover tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-hover.png`、`scenario-devops-domain-mobile-dark-hover.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark hover | `scenario-devops-domain-tablet-hover.png` + `scenario-devops-domain-tablet-dark-hover.png` Hover framing 正常 | SDHO-07 · RESP-06 |
| 2 | mobile light/dark hover | `scenario-devops-domain-mobile-hover.png` + `scenario-devops-domain-mobile-dark-hover.png` Hover framing 正常 | SDHO-07 · RESP-07 |
| 3 | 阶段说明 | 灰度阶段/流量比例 tablet/mobile light/dark 首屏可见 | SDHO-07 · PAT-07 |
| 4 | 移出消失 | mobile dark 下移出鼠标后 hover 面板消失 | SDHO-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 四视口双主题 hover 截图全过 | SDHO-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 悬停「悬停查看阶段说明」→ 对照 tablet/mobile light/dark 四张 hover 截图 → 移出鼠标。

## SDHO-08 — Gateway 端点 Hover tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-hover.png`、`scenario-gateway-domain-mobile-dark-hover.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark hover | `scenario-gateway-domain-tablet-hover.png` + `scenario-gateway-domain-tablet-dark-hover.png` Hover framing 正常 | SDHO-08 · RESP-06 |
| 2 | mobile light/dark hover | `scenario-gateway-domain-mobile-hover.png` + `scenario-gateway-domain-mobile-dark-hover.png` Hover framing 正常 | SDHO-08 · RESP-07 |
| 3 | 端点摘要 | 在线端点/最近探测 tablet/mobile light/dark 首屏可见 | SDHO-08 · PAT-08 |
| 4 | 提示层级 | mobile dark 下 hover 文案与列表层级不丢失 | SDHO-08 · RESP-08 |
| 5 | example runtime | Gateway 场景 section + 四视口双主题 hover 截图全过 | SDHO-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 悬停「悬停查看端点状态」→ 对照 tablet/mobile light/dark 四张 hover 截图 → 移出鼠标。

## SDHO-09 — Governance 审计行 Hover tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-hover.png`、`scenario-governance-domain-mobile-dark-hover.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark hover | `scenario-governance-domain-tablet-hover.png` + `scenario-governance-domain-tablet-dark-hover.png` Hover framing 正常 | SDHO-09 · RESP-06 |
| 2 | mobile light/dark hover | `scenario-governance-domain-mobile-hover.png` + `scenario-governance-domain-mobile-dark-hover.png` Hover framing 正常 | SDHO-09 · RESP-07 |
| 3 | 审计摘要 | 操作/执行人/状态 tablet/mobile light/dark 首屏可见 | SDHO-09 · PAT-09 |
| 4 | 移出消失 | mobile dark 下移出鼠标后 hover 面板消失 | SDHO-09 · INTER-09 |
| 5 | example runtime | Governance 场景 section + 四视口双主题 hover 截图全过 | SDHO-09 · PREVIEW-* |

**交互动作**：打开治理场景 → 悬停「悬停查看审计行」→ 对照 tablet/mobile light/dark 四张 hover 截图 → 移出鼠标。

## SDHO-10 — 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图束

**对照 golden**：20 张 `scenario-*-domain-{tablet,mobile}{,-dark}-hover.png`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 截图数量 | 5 域 × tablet/mobile × light/dark = 20 张 `-hover.png` 全存在 | SDHO-10 · PREVIEW-* |
| 2 | runtime 门禁 | `scenarioDomainHoverViewportLightDarkScreenshotStates.hoverStateMatrixComplete = true` | SDHO-10 · VAL-* |
| 3 | 移出消失 | 每域 hover 后移出鼠标，面板从 DOM 移除 | SDHO-10 · INTER-06 |
| 4 | 与 SDTC 区分 | Hover 截图不含 click-open backdrop；打开态仍走 SDTC | SDHO-10 · INTER-07 |
| 5 | CI 审计 | `audit_migration_drills.py` + `audit_override_recipes.py` SDHO 交叉引用全过 | SDHO-10 · AUDIT-* |

**交互动作**：`npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 `hoverStateMatrixComplete = true` 与 20 张 hover 截图生成。

## 交叉引用

- `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` — SDHO-01～05
- `scenario-domain-tooltip-context-menu-interactive-open-viewport-light-dark-screenshot-review-checklist.md` — SDTC-01～05
- `decision-matrix.md` — G99 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图选型表
- `upgrade-troubleshooting.md` — SDHO-01～10 症状路由
- `agent-retrieval-guide.md` — 场景域 Hover 轻量浮层 tablet/mobile light/dark 独立截图检索路径
- `business-validation-checklist.md` — MS-09～13 场景冒烟
