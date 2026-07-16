# Scenario Domain Empty Error Viewport Light/Dark Screenshot 评审清单

> DOCS-053 / G102 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 empty/error 独立截图视觉回归抽检**，确保每个场景 section 在空态、错误态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`（SDDL-01～05）、`scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md`（SDEE-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 empty/error tablet/mobile light/dark 独立截图抽检 | 对应 SDEE 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 empty/error tablet/mobile light/dark golden 对照 | SDEE-01 + `scenario-bi-domain-tablet-empty.png` + `scenario-bi-domain-mobile-dark-error.png` |
| DevOps 场景阶段 empty/error tablet/mobile light/dark golden 对照 | SDEE-02 + `scenario-devops-domain-tablet-empty.png` + `scenario-devops-domain-mobile-dark-error.png` |
| Gateway 场景端点 empty/error tablet/mobile light/dark golden 对照 | SDEE-03 + `scenario-gateway-domain-tablet-empty.png` + `scenario-gateway-domain-mobile-dark-error.png` |
| Governance 场景审计行 empty/error tablet/mobile light/dark golden 对照 | SDEE-04 + `scenario-governance-domain-tablet-empty.png` + `scenario-governance-domain-mobile-dark-error.png` |
| PaaS 场景容量 empty/error tablet/mobile light/dark golden 对照 | SDEE-05 + `scenario-paas-domain-tablet-empty.png` + `scenario-paas-domain-mobile-dark-error.png` |

## 通用前置

1. 先完成 `scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` SDDL-01～05（disabled/loading 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{empty,error}.png` 四视口双主题 empty/error 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 empty 与一张 error 独立截图；empty 必须出现虚线边框空态面板，error 必须出现 `role="alert"` 与重试 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. empty/error 截图出现文案裁切、空态大面积无意义空白、error 无重试按钮或 dark 对比度不足时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 empty/error tablet/mobile light/dark 独立截图（G102）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 empty/error tablet/mobile light/dark 独立截图抽检行。

## SDEE-01 — BI 场景指标 empty/error tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-empty.png`、`scenario-bi-domain-tablet-dark-empty.png`、`scenario-bi-domain-mobile-empty.png`、`scenario-bi-domain-mobile-dark-empty.png`、`scenario-bi-domain-tablet-error.png`、`scenario-bi-domain-tablet-dark-error.png`、`scenario-bi-domain-mobile-error.png`、`scenario-bi-domain-mobile-dark-error.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light empty 截图 | `scenario-bi-domain-tablet-empty.png` 存在且 empty framing 正常 | SDEE-01 · RESP-06 |
| 2 | tablet dark empty 截图 | `scenario-bi-domain-tablet-dark-empty.png` 存在且空态文案可读 | SDEE-01 · VIS-05 |
| 3 | mobile light error 截图 | `scenario-bi-domain-mobile-error.png` error alert 首屏可见 | SDEE-01 · RESP-07 |
| 4 | mobile dark error 截图 | `scenario-bi-domain-mobile-dark-error.png` error 对比度可辨认 | SDEE-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainEmptyErrorViewportLightDarkScreenshots` biDomain 全过 | SDEE-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 empty 面板 → 点击「触发指标错误」→ 对照 tablet/mobile light/dark 八张 empty/error 截图。

## SDEE-02 — DevOps 场景阶段 empty/error tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-empty.png`、`scenario-devops-domain-tablet-dark-empty.png`、`scenario-devops-domain-mobile-empty.png`、`scenario-devops-domain-mobile-dark-empty.png`、`scenario-devops-domain-tablet-error.png`、`scenario-devops-domain-tablet-dark-error.png`、`scenario-devops-domain-mobile-error.png`、`scenario-devops-domain-mobile-dark-error.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light empty 截图 | `scenario-devops-domain-tablet-empty.png` 存在且 empty framing 正常 | SDEE-02 · RESP-06 |
| 2 | tablet dark empty 截图 | `scenario-devops-domain-tablet-dark-empty.png` 存在且阶段空态可读 | SDEE-02 · VIS-05 |
| 3 | mobile light error 截图 | `scenario-devops-domain-mobile-error.png` 流水线 error 首屏可见 | SDEE-02 · RESP-07 |
| 4 | mobile dark error 截图 | `scenario-devops-domain-mobile-dark-error.png` error 对比度可辨认 | SDEE-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + empty/error tablet/mobile light/dark 可见 | SDEE-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 empty 面板 → 点击「触发阶段错误」→ 对照 tablet/mobile light/dark 八张截图。

## SDEE-03 — Gateway 场景端点 empty/error tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-empty.png`、`scenario-gateway-domain-tablet-dark-empty.png`、`scenario-gateway-domain-mobile-empty.png`、`scenario-gateway-domain-mobile-dark-empty.png`、`scenario-gateway-domain-tablet-error.png`、`scenario-gateway-domain-tablet-dark-error.png`、`scenario-gateway-domain-mobile-error.png`、`scenario-gateway-domain-mobile-dark-error.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light empty 截图 | `scenario-gateway-domain-tablet-empty.png` 存在且 empty framing 正常 | SDEE-03 · RESP-06 |
| 2 | tablet dark empty 截图 | `scenario-gateway-domain-tablet-dark-empty.png` 存在且端点空态可读 | SDEE-03 · VIS-05 |
| 3 | mobile light error 截图 | `scenario-gateway-domain-mobile-error.png` 端点 error 首屏可见 | SDEE-03 · RESP-07 |
| 4 | mobile dark error 截图 | `scenario-gateway-domain-mobile-dark-error.png` error 层级不丢失 | SDEE-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + empty/error tablet/mobile light/dark 可见 | SDEE-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 empty 面板 → 点击「触发端点错误」→ 对照 tablet/mobile light/dark 八张截图。

## SDEE-04 — Governance 场景审计行 empty/error tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-empty.png`、`scenario-governance-domain-tablet-dark-empty.png`、`scenario-governance-domain-mobile-empty.png`、`scenario-governance-domain-mobile-dark-empty.png`、`scenario-governance-domain-tablet-error.png`、`scenario-governance-domain-tablet-dark-error.png`、`scenario-governance-domain-mobile-error.png`、`scenario-governance-domain-mobile-dark-error.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light empty 截图 | `scenario-governance-domain-tablet-empty.png` 存在且 empty framing 正常 | SDEE-04 · RESP-06 |
| 2 | tablet dark empty 截图 | `scenario-governance-domain-tablet-dark-empty.png` 存在且审计空态可读 | SDEE-04 · VIS-05 |
| 3 | mobile light error 截图 | `scenario-governance-domain-mobile-error.png` 审计 error 首屏可见 | SDEE-04 · RESP-07 |
| 4 | mobile dark error 截图 | `scenario-governance-domain-mobile-dark-error.png` error 密度一致 | SDEE-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + empty/error tablet/mobile light/dark 可见 | SDEE-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 empty 面板 → 点击「触发审计错误」→ 对照 tablet/mobile light/dark 八张截图。

## SDEE-05 — PaaS 场景容量 empty/error tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-empty.png`、`scenario-paas-domain-tablet-dark-empty.png`、`scenario-paas-domain-mobile-empty.png`、`scenario-paas-domain-mobile-dark-empty.png`、`scenario-paas-domain-tablet-error.png`、`scenario-paas-domain-tablet-dark-error.png`、`scenario-paas-domain-mobile-error.png`、`scenario-paas-domain-mobile-dark-error.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light empty 截图 | `scenario-paas-domain-tablet-empty.png` 存在且 empty framing 正常 | SDEE-05 · RESP-06 |
| 2 | tablet dark empty 截图 | `scenario-paas-domain-tablet-dark-empty.png` 存在且容量空态可读 | SDEE-05 · VIS-05 |
| 3 | mobile light error 截图 | `scenario-paas-domain-mobile-error.png` 容量 error 首屏可见 | SDEE-05 · RESP-07 |
| 4 | mobile dark error 截图 | `scenario-paas-domain-mobile-dark-error.png` error 列表项可辨认 | SDEE-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + empty/error tablet/mobile light/dark 可见 | SDEE-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 empty 面板 → 点击「触发容量错误」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-empty-error-viewport-light-dark-screenshot-review-checklist.md` SDEE-06～10
- disabled/loading 前置：`scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` SDDL-01～05
- 选型表：`decision-matrix.md` G102 场景域 empty/error tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDEE-01～10
- Runtime 门禁：`verifyScenarioDomainEmptyErrorViewportLightDarkScreenshots`
