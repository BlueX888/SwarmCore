# Scenario Domain Focus Keyboard Viewport Light/Dark Screenshot 评审清单

> DOCS-051 / G100 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 Focus 态与键盘导航独立截图视觉回归抽检**，确保每个场景 section 在 Tab 聚焦、方向键导航、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md`（SDHO-01～05）、`scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`（SDFK-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图抽检 | 对应 SDFK 块 + `quality-rubric.md` 交互与动效 |
| BI 场景指标 Focus tablet/mobile light/dark golden 对照 | SDFK-01 + `scenario-bi-domain-tablet-focus.png` + `scenario-bi-domain-mobile-dark-focus.png` |
| DevOps 场景阶段 Focus tablet/mobile light/dark golden 对照 | SDFK-02 + `scenario-devops-domain-tablet-focus.png` + `scenario-devops-domain-mobile-dark-focus.png` |
| Gateway 场景端点 Focus tablet/mobile light/dark golden 对照 | SDFK-03 + `scenario-gateway-domain-tablet-focus.png` + `scenario-gateway-domain-mobile-dark-focus.png` |
| Governance 场景审计行 Focus tablet/mobile light/dark golden 对照 | SDFK-04 + `scenario-governance-domain-tablet-focus.png` + `scenario-governance-domain-mobile-dark-focus.png` |
| PaaS 场景容量 Focus tablet/mobile light/dark golden 对照 | SDFK-05 + `scenario-paas-domain-tablet-focus.png` + `scenario-paas-domain-mobile-dark-focus.png` |

## 通用前置

1. 先完成 `scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` SDHO-01～05（Hover 轻量浮层独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-focus.png` 四视口双主题 Focus 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 两张 Focus 独立截图，且 focus 面板必须真实出现、方向键可切换高亮项、Esc 后消失。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. Focus 截图出现文案裁切、focus 环不可辨认、方向键导航失效、Esc 后仍残留面板时，交互与动效质量不得评 95+，综合美学不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图（G100）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图抽检行。

## SDFK-01 — BI 场景指标 Focus tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-focus.png`、`scenario-bi-domain-tablet-dark-focus.png`、`scenario-bi-domain-mobile-focus.png`、`scenario-bi-domain-mobile-dark-focus.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light focus 截图 | `scenario-bi-domain-tablet-focus.png` 存在且 Focus framing 正常 | SDFK-01 · RESP-06 |
| 2 | tablet dark focus 截图 | `scenario-bi-domain-tablet-dark-focus.png` 存在且指标导航可读 | SDFK-01 · VIS-05 |
| 3 | mobile light focus 截图 | `scenario-bi-domain-mobile-focus.png` 指标导航首屏可见 | SDFK-01 · RESP-07 |
| 4 | mobile dark focus 截图 | `scenario-bi-domain-mobile-dark-focus.png` focus 对比度可辨认 | SDFK-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainFocusKeyboardViewportLightDarkScreenshots` biDomain 全过 | SDFK-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ Tab 聚焦「Tab 聚焦查看指标导航」→ 按 ArrowDown 切换高亮项 → 对照 tablet/mobile light/dark 四张 focus 截图 → 按 Esc 确认面板消失。

## SDFK-02 — DevOps 场景阶段 Focus tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-focus.png`、`scenario-devops-domain-tablet-dark-focus.png`、`scenario-devops-domain-mobile-focus.png`、`scenario-devops-domain-mobile-dark-focus.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light focus 截图 | `scenario-devops-domain-tablet-focus.png` 存在且 Focus framing 正常 | SDFK-02 · RESP-06 |
| 2 | tablet dark focus 截图 | `scenario-devops-domain-tablet-dark-focus.png` 存在且阶段导航可读 | SDFK-02 · VIS-05 |
| 3 | mobile light focus 截图 | `scenario-devops-domain-mobile-focus.png` 流水线阶段首屏可见 | SDFK-02 · RESP-07 |
| 4 | mobile dark focus 截图 | `scenario-devops-domain-mobile-dark-focus.png` focus 对比度可辨认 | SDFK-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + Focus tablet/mobile light/dark 可见 | SDFK-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ Tab 聚焦「Tab 聚焦查看阶段导航」→ 按 ArrowDown → 对照 tablet/mobile light/dark 四张 focus 截图 → 按 Esc。

## SDFK-03 — Gateway 场景端点 Focus tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-focus.png`、`scenario-gateway-domain-tablet-dark-focus.png`、`scenario-gateway-domain-mobile-focus.png`、`scenario-gateway-domain-mobile-dark-focus.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light focus 截图 | `scenario-gateway-domain-tablet-focus.png` 存在且 Focus framing 正常 | SDFK-03 · RESP-06 |
| 2 | tablet dark focus 截图 | `scenario-gateway-domain-tablet-dark-focus.png` 存在且端点摘要可读 | SDFK-03 · VIS-05 |
| 3 | mobile light focus 截图 | `scenario-gateway-domain-mobile-focus.png` 端点状态首屏可见 | SDFK-03 · RESP-07 |
| 4 | mobile dark focus 截图 | `scenario-gateway-domain-mobile-dark-focus.png` focus 层级不丢失 | SDFK-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + Focus tablet/mobile light/dark 可见 | SDFK-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ Tab 聚焦「Tab 聚焦查看端点导航」→ 按 ArrowDown → 对照 tablet/mobile light/dark 四张 focus 截图 → 按 Esc。

## SDFK-04 — Governance 场景审计行 Focus tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-focus.png`、`scenario-governance-domain-tablet-dark-focus.png`、`scenario-governance-domain-mobile-focus.png`、`scenario-governance-domain-mobile-dark-focus.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light focus 截图 | `scenario-governance-domain-tablet-focus.png` 存在且 Focus framing 正常 | SDFK-04 · RESP-06 |
| 2 | tablet dark focus 截图 | `scenario-governance-domain-tablet-dark-focus.png` 存在且审计摘要可读 | SDFK-04 · VIS-05 |
| 3 | mobile light focus 截图 | `scenario-governance-domain-mobile-focus.png` 审计行摘要首屏可见 | SDFK-04 · RESP-07 |
| 4 | mobile dark focus 截图 | `scenario-governance-domain-mobile-dark-focus.png` focus 密度一致 | SDFK-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + Focus tablet/mobile light/dark 可见 | SDFK-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ Tab 聚焦「Tab 聚焦查看审计导航」→ 按 ArrowDown → 对照 tablet/mobile light/dark 四张 focus 截图 → 按 Esc。

## SDFK-05 — PaaS 场景容量 Focus tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-focus.png`、`scenario-paas-domain-tablet-dark-focus.png`、`scenario-paas-domain-mobile-focus.png`、`scenario-paas-domain-mobile-dark-focus.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light focus 截图 | `scenario-paas-domain-tablet-focus.png` 存在且 Focus framing 正常 | SDFK-05 · RESP-06 |
| 2 | tablet dark focus 截图 | `scenario-paas-domain-tablet-dark-focus.png` 存在且容量摘要可读 | SDFK-05 · VIS-05 |
| 3 | mobile light focus 截图 | `scenario-paas-domain-mobile-focus.png` 容量导航首屏可见 | SDFK-05 · RESP-07 |
| 4 | mobile dark focus 截图 | `scenario-paas-domain-mobile-dark-focus.png` 列表项可辨认 | SDFK-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + Focus tablet/mobile light/dark 可见 | SDFK-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ Tab 聚焦「Tab 聚焦查看容量导航」→ 按 ArrowDown → 对照 tablet/mobile light/dark 四张 focus 截图 → 按 Esc。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` SDFK-06～10
- Hover 前置：`scenario-domain-hover-viewport-light-dark-screenshot-review-checklist.md` SDHO-01～05
- 选型表：`decision-matrix.md` G100 场景域 Focus/键盘导航 tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDFK-01～10
- Runtime 门禁：`verifyScenarioDomainFocusKeyboardViewportLightDarkScreenshots`
