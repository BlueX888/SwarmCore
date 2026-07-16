# 场景 Scenario Domain Empty Error Viewport Light/Dark Screenshot 评审清单

> DOCS-053 / G102 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 empty/error 独立截图抽检**，确保各域 section 在 empty/error 态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`（SDEE-01～05）、`scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`（SDDL-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 empty/error tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDEE 块 + `quality-rubric.md` |
| BI Analytics 指标 empty/error tablet/mobile light/dark 独立截图 | SDEE-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 empty/error tablet/mobile light/dark 独立截图 | SDEE-07 + `scenario-devops` |
| Gateway 端点 empty/error tablet/mobile light/dark 独立截图 | SDEE-08 + `scenario-gateway` |
| Governance 审计行 empty/error tablet/mobile light/dark 独立截图 | SDEE-09 + `scenario-governance` |
| 场景域 empty/error tablet/mobile light/dark 独立截图束缺门禁 | SDEE-10 + `verify:runtime` `scenarioDomainEmptyErrorViewportLightDarkScreenshotStates` + `verifyScenarioDomainEmptyErrorViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` SDEE-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{empty,error}.png` 共 40 张 empty/error 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark empty/error 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 empty/error tablet/mobile light/dark 独立截图（G102）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 empty/error tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDEE-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDEE-06 — BI Analytics 指标 empty/error tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-empty.png`、`scenario-bi-domain-mobile-dark-error.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark empty | `scenario-bi-domain-tablet-empty.png` + `scenario-bi-domain-tablet-dark-empty.png` empty framing 正常 | SDEE-06 · RESP-06 |
| 2 | mobile light/dark error | `scenario-bi-domain-mobile-error.png` + `scenario-bi-domain-mobile-dark-error.png` error framing 正常 | SDEE-06 · RESP-07 |
| 3 | 指标空态/错误 | 暂无指标数据空态 + 指标同步失败 error alert tablet/mobile light/dark 首屏可见 | SDEE-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 empty 虚线边框与 error alert 层级可辨认 | SDEE-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 empty/error 截图全过 | SDEE-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 empty 面板 → 点击「触发指标错误」→ 对照 tablet/mobile light/dark 八张 empty/error 截图。

## SDEE-07 — DevOps 阶段 empty/error tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-empty.png`、`scenario-devops-domain-mobile-dark-error.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark empty | `scenario-devops-domain-tablet-empty.png` + `scenario-devops-domain-tablet-dark-empty.png` empty framing 正常 | SDEE-07 · RESP-06 |
| 2 | mobile light/dark error | `scenario-devops-domain-mobile-error.png` + `scenario-devops-domain-mobile-dark-error.png` error framing 正常 | SDEE-07 · RESP-07 |
| 3 | 阶段空态/错误 | 暂无流水线空态 + 阶段查询失败 error alert tablet/mobile light/dark 首屏可见 | SDEE-07 · PAT-07 |
| 4 | error 态 | mobile dark 下 error 文案与重试按钮可辨认 | SDEE-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 empty/error 截图全过 | SDEE-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 empty 面板 → 点击「触发阶段错误」→ 对照 tablet/mobile light/dark 八张截图。

## SDEE-08 — Gateway 端点 empty/error tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-empty.png`、`scenario-gateway-domain-mobile-dark-error.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark empty | `scenario-gateway-domain-tablet-empty.png` + `scenario-gateway-domain-tablet-dark-empty.png` empty framing 正常 | SDEE-08 · RESP-06 |
| 2 | mobile light/dark error | `scenario-gateway-domain-mobile-error.png` + `scenario-gateway-domain-mobile-dark-error.png` error framing 正常 | SDEE-08 · RESP-07 |
| 3 | 端点空态/错误 | 暂无端点空态 + 端点探测失败 error alert tablet/mobile light/dark 首屏可见 | SDEE-08 · PAT-08 |
| 4 | empty 态 | mobile dark 下空态虚线边框对比度可辨认 | SDEE-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 empty/error 截图全过 | SDEE-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 empty 面板 → 点击「触发端点错误」→ 对照 tablet/mobile light/dark 八张截图。

## SDEE-09 — Governance 审计行 empty/error tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-empty.png`、`scenario-governance-domain-mobile-empty.png`、`scenario-governance-domain-mobile-dark-error.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark empty | `scenario-governance-domain-tablet-empty.png` + `scenario-governance-domain-tablet-dark-empty.png` empty framing 正常 | SDEE-09 · RESP-06 |
| 2 | mobile light/dark error | `scenario-governance-domain-mobile-error.png` + `scenario-governance-domain-mobile-dark-error.png` error framing 正常 | SDEE-09 · RESP-07 |
| 3 | 审计空态/错误 | 暂无审计记录空态 + 审计导出失败 error alert tablet/mobile light/dark 首屏可见 | SDEE-09 · PAT-09 |
| 4 | error 文案 | mobile dark 下「审计导出失败」文案可辨认 | SDEE-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 empty/error 截图全过 | SDEE-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 empty 面板 → 点击「触发审计错误」→ 对照 tablet/mobile light/dark 八张截图。

## SDEE-10 — 场景域 empty/error tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{empty,error}.png` + `scenarioDomainEmptyErrorViewportLightDarkScreenshotStates.emptyErrorStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × empty/error 全量 golden 存在 | SDEE-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainEmptyErrorViewportLightDarkScreenshots` 通过 | SDEE-10 · PREVIEW-* |
| 3 | empty 态 | 五域 `data-audit="scenario-domain-empty-overlay"` `data-state="empty"` 可见 | SDEE-10 · LOGIC-* |
| 4 | error 态 | 五域点击 error trigger 后 `role="alert"` + `data-state="error"` 可见 | SDEE-10 · ASYNC-* |
| 5 | 矩阵完整 | `emptyErrorStateMatrixComplete = true` | SDEE-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 empty/error 截图与门禁 JSON 输出。
