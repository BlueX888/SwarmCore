# Scenario Domain Disabled Loading Viewport Light/Dark Screenshot 评审清单

> DOCS-052 / G101 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 disabled/loading 独立截图视觉回归抽检**，确保每个场景 section 在禁用态、加载态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md`（SDFK-01～05）、`scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md`（SDDL-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 disabled/loading tablet/mobile light/dark 独立截图抽检 | 对应 SDDL 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 disabled/loading tablet/mobile light/dark golden 对照 | SDDL-01 + `scenario-bi-domain-tablet-disabled.png` + `scenario-bi-domain-mobile-dark-loading.png` |
| DevOps 场景阶段 disabled/loading tablet/mobile light/dark golden 对照 | SDDL-02 + `scenario-devops-domain-tablet-disabled.png` + `scenario-devops-domain-mobile-dark-loading.png` |
| Gateway 场景端点 disabled/loading tablet/mobile light/dark golden 对照 | SDDL-03 + `scenario-gateway-domain-tablet-disabled.png` + `scenario-gateway-domain-mobile-dark-loading.png` |
| Governance 场景审计行 disabled/loading tablet/mobile light/dark golden 对照 | SDDL-04 + `scenario-governance-domain-tablet-disabled.png` + `scenario-governance-domain-mobile-dark-loading.png` |
| PaaS 场景容量 disabled/loading tablet/mobile light/dark golden 对照 | SDDL-05 + `scenario-paas-domain-tablet-disabled.png` + `scenario-paas-domain-mobile-dark-loading.png` |

## 通用前置

1. 先完成 `scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` SDFK-01～05（Focus/键盘导航独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{disabled,loading}.png` 四视口双主题 disabled/loading 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 disabled 与一张 loading 独立截图；disabled 主操作必须真实 `disabled`，loading 必须出现 spinner 与 `aria-busy`。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. disabled/loading 截图出现文案裁切、按钮仍可点击、loading 无 spinner 或 dark 对比度不足时，逻辑完备不得评 95+，交互与动效质量不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 disabled/loading tablet/mobile light/dark 独立截图（G101）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 disabled/loading tablet/mobile light/dark 独立截图抽检行。

## SDDL-01 — BI 场景指标 disabled/loading tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-disabled.png`、`scenario-bi-domain-tablet-dark-disabled.png`、`scenario-bi-domain-mobile-disabled.png`、`scenario-bi-domain-mobile-dark-disabled.png`、`scenario-bi-domain-tablet-loading.png`、`scenario-bi-domain-tablet-dark-loading.png`、`scenario-bi-domain-mobile-loading.png`、`scenario-bi-domain-mobile-dark-loading.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light disabled 截图 | `scenario-bi-domain-tablet-disabled.png` 存在且 disabled framing 正常 | SDDL-01 · RESP-06 |
| 2 | tablet dark disabled 截图 | `scenario-bi-domain-tablet-dark-disabled.png` 存在且禁用按钮可读 | SDDL-01 · VIS-05 |
| 3 | mobile light loading 截图 | `scenario-bi-domain-mobile-loading.png` loading spinner 首屏可见 | SDDL-01 · RESP-07 |
| 4 | mobile dark loading 截图 | `scenario-bi-domain-mobile-dark-loading.png` loading 对比度可辨认 | SDDL-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainDisabledLoadingViewportLightDarkScreenshots` biDomain 全过 | SDDL-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 disabled 面板与禁用按钮 → 点击「触发指标加载」→ 对照 tablet/mobile light/dark 八张 disabled/loading 截图。

## SDDL-02 — DevOps 场景阶段 disabled/loading tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-disabled.png`、`scenario-devops-domain-tablet-dark-disabled.png`、`scenario-devops-domain-mobile-disabled.png`、`scenario-devops-domain-mobile-dark-disabled.png`、`scenario-devops-domain-tablet-loading.png`、`scenario-devops-domain-tablet-dark-loading.png`、`scenario-devops-domain-mobile-loading.png`、`scenario-devops-domain-mobile-dark-loading.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light disabled 截图 | `scenario-devops-domain-tablet-disabled.png` 存在且 disabled framing 正常 | SDDL-02 · RESP-06 |
| 2 | tablet dark disabled 截图 | `scenario-devops-domain-tablet-dark-disabled.png` 存在且阶段禁用态可读 | SDDL-02 · VIS-05 |
| 3 | mobile light loading 截图 | `scenario-devops-domain-mobile-loading.png` 流水线 loading 首屏可见 | SDDL-02 · RESP-07 |
| 4 | mobile dark loading 截图 | `scenario-devops-domain-mobile-dark-loading.png` loading 对比度可辨认 | SDDL-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + disabled/loading tablet/mobile light/dark 可见 | SDDL-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 disabled 面板 → 点击「触发阶段加载」→ 对照 tablet/mobile light/dark 八张截图。

## SDDL-03 — Gateway 场景端点 disabled/loading tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-disabled.png`、`scenario-gateway-domain-tablet-dark-disabled.png`、`scenario-gateway-domain-mobile-disabled.png`、`scenario-gateway-domain-mobile-dark-disabled.png`、`scenario-gateway-domain-tablet-loading.png`、`scenario-gateway-domain-tablet-dark-loading.png`、`scenario-gateway-domain-mobile-loading.png`、`scenario-gateway-domain-mobile-dark-loading.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light disabled 截图 | `scenario-gateway-domain-tablet-disabled.png` 存在且 disabled framing 正常 | SDDL-03 · RESP-06 |
| 2 | tablet dark disabled 截图 | `scenario-gateway-domain-tablet-dark-disabled.png` 存在且端点禁用态可读 | SDDL-03 · VIS-05 |
| 3 | mobile light loading 截图 | `scenario-gateway-domain-mobile-loading.png` 端点 loading 首屏可见 | SDDL-03 · RESP-07 |
| 4 | mobile dark loading 截图 | `scenario-gateway-domain-mobile-dark-loading.png` loading 层级不丢失 | SDDL-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + disabled/loading tablet/mobile light/dark 可见 | SDDL-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 disabled 面板 → 点击「触发端点加载」→ 对照 tablet/mobile light/dark 八张截图。

## SDDL-04 — Governance 场景审计行 disabled/loading tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-disabled.png`、`scenario-governance-domain-tablet-dark-disabled.png`、`scenario-governance-domain-mobile-disabled.png`、`scenario-governance-domain-mobile-dark-disabled.png`、`scenario-governance-domain-tablet-loading.png`、`scenario-governance-domain-tablet-dark-loading.png`、`scenario-governance-domain-mobile-loading.png`、`scenario-governance-domain-mobile-dark-loading.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light disabled 截图 | `scenario-governance-domain-tablet-disabled.png` 存在且 disabled framing 正常 | SDDL-04 · RESP-06 |
| 2 | tablet dark disabled 截图 | `scenario-governance-domain-tablet-dark-disabled.png` 存在且审计禁用态可读 | SDDL-04 · VIS-05 |
| 3 | mobile light loading 截图 | `scenario-governance-domain-mobile-loading.png` 审计 loading 首屏可见 | SDDL-04 · RESP-07 |
| 4 | mobile dark loading 截图 | `scenario-governance-domain-mobile-dark-loading.png` loading 密度一致 | SDDL-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + disabled/loading tablet/mobile light/dark 可见 | SDDL-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 disabled 面板 → 点击「触发审计加载」→ 对照 tablet/mobile light/dark 八张截图。

## SDDL-05 — PaaS 场景容量 disabled/loading tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-disabled.png`、`scenario-paas-domain-tablet-dark-disabled.png`、`scenario-paas-domain-mobile-disabled.png`、`scenario-paas-domain-mobile-dark-disabled.png`、`scenario-paas-domain-tablet-loading.png`、`scenario-paas-domain-tablet-dark-loading.png`、`scenario-paas-domain-mobile-loading.png`、`scenario-paas-domain-mobile-dark-loading.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light disabled 截图 | `scenario-paas-domain-tablet-disabled.png` 存在且 disabled framing 正常 | SDDL-05 · RESP-06 |
| 2 | tablet dark disabled 截图 | `scenario-paas-domain-tablet-dark-disabled.png` 存在且容量禁用态可读 | SDDL-05 · VIS-05 |
| 3 | mobile light loading 截图 | `scenario-paas-domain-mobile-loading.png` 容量 loading 首屏可见 | SDDL-05 · RESP-07 |
| 4 | mobile dark loading 截图 | `scenario-paas-domain-mobile-dark-loading.png` loading 列表项可辨认 | SDDL-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + disabled/loading tablet/mobile light/dark 可见 | SDDL-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 disabled 面板 → 点击「触发容量加载」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-disabled-loading-viewport-light-dark-screenshot-review-checklist.md` SDDL-06～10
- Focus 前置：`scenario-domain-focus-keyboard-viewport-light-dark-screenshot-review-checklist.md` SDFK-01～05
- 选型表：`decision-matrix.md` G101 场景域 disabled/loading tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDDL-01～10
- Runtime 门禁：`verifyScenarioDomainDisabledLoadingViewportLightDarkScreenshots`
