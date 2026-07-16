# 场景 Scenario Domain Disabled Loading Viewport Light/Dark Screenshot 评审清单

> DOCS-052 / G101 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 disabled/loading 独立截图抽检**，确保各域 section 在 disabled/loading 态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`（SDDL-01～05）、`scene-scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`（SDFK-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 disabled/loading tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDDL 块 + `quality-rubric.md` |
| BI Analytics 指标 disabled/loading tablet/mobile light/dark 独立截图 | SDDL-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 disabled/loading tablet/mobile light/dark 独立截图 | SDDL-07 + `scenario-devops` |
| Gateway 端点 disabled/loading tablet/mobile light/dark 独立截图 | SDDL-08 + `scenario-gateway` |
| Governance 审计行 disabled/loading tablet/mobile light/dark 独立截图 | SDDL-09 + `scenario-governance` |
| 场景域 disabled/loading tablet/mobile light/dark 独立截图束缺门禁 | SDDL-10 + `verify:runtime` `scenarioDomainDisabledLoadingViewportLightDarkScreenshotStates` + `verifyScenarioDomainDisabledLoadingViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` SDDL-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{disabled,loading}.png` 共 40 张 disabled/loading 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark disabled/loading 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 disabled/loading tablet/mobile light/dark 独立截图（G101）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 disabled/loading tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDDL-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDDL-06 — BI Analytics 指标 disabled/loading tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-disabled.png`、`scenario-bi-domain-mobile-dark-loading.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark disabled | `scenario-bi-domain-tablet-disabled.png` + `scenario-bi-domain-tablet-dark-disabled.png` disabled framing 正常 | SDDL-06 · RESP-06 |
| 2 | mobile light/dark loading | `scenario-bi-domain-mobile-loading.png` + `scenario-bi-domain-mobile-dark-loading.png` loading framing 正常 | SDDL-06 · RESP-07 |
| 3 | 指标禁用/加载 | 导出指标禁用 + 指标 loading spinner tablet/mobile light/dark 首屏可见 | SDDL-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 disabled 按钮与 loading spinner 层级可辨认 | SDDL-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 disabled/loading 截图全过 | SDDL-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 disabled 面板 → 点击「触发指标加载」→ 对照 tablet/mobile light/dark 八张 disabled/loading 截图。

## SDDL-07 — DevOps 阶段 disabled/loading tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-disabled.png`、`scenario-devops-domain-mobile-dark-loading.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark disabled | `scenario-devops-domain-tablet-disabled.png` + `scenario-devops-domain-tablet-dark-disabled.png` disabled framing 正常 | SDDL-07 · RESP-06 |
| 2 | mobile light/dark loading | `scenario-devops-domain-mobile-loading.png` + `scenario-devops-domain-mobile-dark-loading.png` loading framing 正常 | SDDL-07 · RESP-07 |
| 3 | 阶段禁用/加载 | 推进生产禁用 + 阶段 loading spinner tablet/mobile light/dark 首屏可见 | SDDL-07 · PAT-07 |
| 4 | loading 态 | mobile dark 下 loading 文案与 spinner 可辨认 | SDDL-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 disabled/loading 截图全过 | SDDL-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 disabled 面板 → 点击「触发阶段加载」→ 对照 tablet/mobile light/dark 八张截图。

## SDDL-08 — Gateway 端点 disabled/loading tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-disabled.png`、`scenario-gateway-domain-mobile-dark-loading.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark disabled | `scenario-gateway-domain-tablet-disabled.png` + `scenario-gateway-domain-tablet-dark-disabled.png` disabled framing 正常 | SDDL-08 · RESP-06 |
| 2 | mobile light/dark loading | `scenario-gateway-domain-mobile-loading.png` + `scenario-gateway-domain-mobile-dark-loading.png` loading framing 正常 | SDDL-08 · RESP-07 |
| 3 | 端点禁用/加载 | 轮换密钥禁用 + 端点 loading spinner tablet/mobile light/dark 首屏可见 | SDDL-08 · PAT-08 |
| 4 | disabled 态 | mobile dark 下禁用按钮对比度可辨认 | SDDL-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 disabled/loading 截图全过 | SDDL-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 disabled 面板 → 点击「触发端点加载」→ 对照 tablet/mobile light/dark 八张截图。

## SDDL-09 — Governance 审计行 disabled/loading tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-disabled.png`、`scenario-governance-domain-mobile-disabled.png`、`scenario-governance-domain-mobile-dark-loading.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark disabled | `scenario-governance-domain-tablet-disabled.png` + `scenario-governance-domain-tablet-dark-disabled.png` disabled framing 正常 | SDDL-09 · RESP-06 |
| 2 | mobile light/dark loading | `scenario-governance-domain-mobile-loading.png` + `scenario-governance-domain-mobile-dark-loading.png` loading framing 正常 | SDDL-09 · RESP-07 |
| 3 | 审计禁用/加载 | 导出审计禁用 + 审计 loading spinner tablet/mobile light/dark 首屏可见 | SDDL-09 · PAT-09 |
| 4 | loading 文案 | mobile dark 下「正在同步数据」文案可辨认 | SDDL-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 disabled/loading 截图全过 | SDDL-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 disabled 面板 → 点击「触发审计加载」→ 对照 tablet/mobile light/dark 八张截图。

## SDDL-10 — 场景域 disabled/loading tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{disabled,loading}.png` + `scenarioDomainDisabledLoadingViewportLightDarkScreenshotStates.disabledLoadingStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × disabled/loading 全量 golden 存在 | SDDL-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainDisabledLoadingViewportLightDarkScreenshots` 通过 | SDDL-10 · PREVIEW-* |
| 3 | disabled 态 | 五域 `data-audit="scenario-domain-disabled-overlay"` `data-state="disabled"` 可见 | SDDL-10 · LOGIC-* |
| 4 | loading 态 | 五域点击 loading trigger 后 spinner + `data-state="loading"` 可见 | SDDL-10 · ASYNC-* |
| 5 | 矩阵完整 | `disabledLoadingStateMatrixComplete = true` | SDDL-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 disabled/loading 截图与门禁 JSON 输出。
