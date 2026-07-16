# Scenario Domain Network Partition Recovery Viewport Light/Dark Screenshot 评审清单

> DOCS-060 / G109 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现 tablet/mobile light/dark 四主题 network partition/disconnect recovery 独立截图视觉回归抽检**，确保每个场景 section 在网络分区检测态、连接恢复态、平板与移动视口、浅色与深色主题下均有独立 golden 截图，并与 `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`（SDOSC-01～05）、`scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDNPR-06～10）及 `examples/b-design-system-tailadmin-radix` runtime 证据对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 network partition/recovery tablet/mobile light/dark 独立截图抽检 | 对应 SDNPR 块 + `quality-rubric.md` 逻辑完备 |
| BI 场景指标 network partition/recovery tablet/mobile light/dark golden 对照 | SDNPR-01 + `scenario-bi-domain-tablet-partitioned.png` + `scenario-bi-domain-mobile-dark-recovered.png` |
| DevOps 场景阶段 network partition/recovery tablet/mobile light/dark golden 对照 | SDNPR-02 + `scenario-devops-domain-tablet-partitioned.png` + `scenario-devops-domain-mobile-dark-recovered.png` |
| Gateway 场景端点 network partition/recovery tablet/mobile light/dark golden 对照 | SDNPR-03 + `scenario-gateway-domain-tablet-partitioned.png` + `scenario-gateway-domain-mobile-dark-recovered.png` |
| Governance 场景审计行 network partition/recovery tablet/mobile light/dark golden 对照 | SDNPR-04 + `scenario-governance-domain-tablet-partitioned.png` + `scenario-governance-domain-mobile-dark-recovered.png` |
| PaaS 场景容量 network partition/recovery tablet/mobile light/dark golden 对照 | SDNPR-05 + `scenario-paas-domain-tablet-partitioned.png` + `scenario-paas-domain-mobile-dark-recovered.png` |

## 通用前置

1. 先完成 `scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` SDOSC-01～05（offline/sync conflict 独立截图）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{partitioned,recovered}.png` 四视口双主题 network partition/recovery 独立截图。
3. 每个场景域在 tablet 与 mobile 视口下必须有 **light + dark** 各一张 partitioned 与一张 recovered 独立截图；partitioned 必须出现 partitioned banner 与受影响节点摘要，recovered 必须出现 recovered banner 与查看恢复详情 CTA。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. network partition/recovery 截图出现文案裁切、分区 banner 对比度不足、recovered banner 层级丢失或 dark 主题不可辨认时，逻辑完备不得评 95+，约束遵守不得评 95+。
6. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 network partition/recovery tablet/mobile light/dark 独立截图（G109）** 选型表。
7. 检索路径见 `agent-retrieval-guide.md` 场景域 network partition/recovery tablet/mobile light/dark 独立截图抽检行。

## SDNPR-01 — BI 场景指标 network partition/recovery tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-bi-domain-tablet-partitioned.png`、`scenario-bi-domain-tablet-dark-partitioned.png`、`scenario-bi-domain-mobile-partitioned.png`、`scenario-bi-domain-mobile-dark-partitioned.png`、`scenario-bi-domain-tablet-recovered.png`、`scenario-bi-domain-tablet-dark-recovered.png`、`scenario-bi-domain-mobile-recovered.png`、`scenario-bi-domain-mobile-dark-recovered.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partitioned 截图 | `scenario-bi-domain-tablet-partitioned.png` 存在且 partitioned framing 正常 | SDNPR-01 · RESP-06 |
| 2 | tablet dark partitioned 截图 | `scenario-bi-domain-tablet-dark-partitioned.png` 存在且分区 banner 可读 | SDNPR-01 · VIS-05 |
| 3 | mobile light recovered 截图 | `scenario-bi-domain-mobile-recovered.png` recovered banner 首屏可见 | SDNPR-01 · RESP-07 |
| 4 | mobile dark recovered 截图 | `scenario-bi-domain-mobile-dark-recovered.png` recovered 对比度可辨认 | SDNPR-01 · VIS-06 |
| 5 | example runtime | `verifyScenarioDomainNetworkPartitionRecoveryViewportLightDarkScreenshots` biDomain 全过 | SDNPR-01 · PREVIEW-* |

**交互动作**：打开「BI 场景」→ 对照 partitioned 面板 → 点击「触发指标网络恢复」→ 对照 tablet/mobile light/dark 八张 partitioned/recovered 截图。

## SDNPR-02 — DevOps 场景阶段 network partition/recovery tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-devops-domain-tablet-partitioned.png`、`scenario-devops-domain-tablet-dark-partitioned.png`、`scenario-devops-domain-mobile-partitioned.png`、`scenario-devops-domain-mobile-dark-partitioned.png`、`scenario-devops-domain-tablet-recovered.png`、`scenario-devops-domain-tablet-dark-recovered.png`、`scenario-devops-domain-mobile-recovered.png`、`scenario-devops-domain-mobile-dark-recovered.png`、`devops-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partitioned 截图 | `scenario-devops-domain-tablet-partitioned.png` 存在且 partitioned framing 正常 | SDNPR-02 · RESP-06 |
| 2 | tablet dark partitioned 截图 | `scenario-devops-domain-tablet-dark-partitioned.png` 存在且网络分区可读 | SDNPR-02 · VIS-05 |
| 3 | mobile light recovered 截图 | `scenario-devops-domain-mobile-recovered.png` 流水线 recovered 首屏可见 | SDNPR-02 · RESP-07 |
| 4 | mobile dark recovered 截图 | `scenario-devops-domain-mobile-dark-recovered.png` recovered 对比度可辨认 | SDNPR-02 · VIS-07 |
| 5 | example runtime | `data-audit="scenario-devops"` + network partition/recovery tablet/mobile light/dark 可见 | SDNPR-02 · PREVIEW-* |

**交互动作**：打开「DevOps 场景」→ 对照 partitioned 面板 → 点击「触发阶段网络恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDNPR-03 — Gateway 场景端点 network partition/recovery tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-gateway-domain-tablet-partitioned.png`、`scenario-gateway-domain-tablet-dark-partitioned.png`、`scenario-gateway-domain-mobile-partitioned.png`、`scenario-gateway-domain-mobile-dark-partitioned.png`、`scenario-gateway-domain-tablet-recovered.png`、`scenario-gateway-domain-tablet-dark-recovered.png`、`scenario-gateway-domain-mobile-recovered.png`、`scenario-gateway-domain-mobile-dark-recovered.png`、`gateway-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partitioned 截图 | `scenario-gateway-domain-tablet-partitioned.png` 存在且 partitioned framing 正常 | SDNPR-03 · RESP-06 |
| 2 | tablet dark partitioned 截图 | `scenario-gateway-domain-tablet-dark-partitioned.png` 存在且网络分区可读 | SDNPR-03 · VIS-05 |
| 3 | mobile light recovered 截图 | `scenario-gateway-domain-mobile-recovered.png` 端点 recovered 首屏可见 | SDNPR-03 · RESP-07 |
| 4 | mobile dark recovered 截图 | `scenario-gateway-domain-mobile-dark-recovered.png` recovered 层级不丢失 | SDNPR-03 · RESP-08 |
| 5 | example runtime | `data-audit="scenario-gateway"` + network partition/recovery tablet/mobile light/dark 可见 | SDNPR-03 · PREVIEW-* |

**交互动作**：打开「Gateway 场景」→ 对照 partitioned 面板 → 点击「触发端点网络恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDNPR-04 — Governance 场景审计行 network partition/recovery tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-governance-domain-tablet-partitioned.png`、`scenario-governance-domain-tablet-dark-partitioned.png`、`scenario-governance-domain-mobile-partitioned.png`、`scenario-governance-domain-mobile-dark-partitioned.png`、`scenario-governance-domain-tablet-recovered.png`、`scenario-governance-domain-tablet-dark-recovered.png`、`scenario-governance-domain-mobile-recovered.png`、`scenario-governance-domain-mobile-dark-recovered.png`、`governance-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partitioned 截图 | `scenario-governance-domain-tablet-partitioned.png` 存在且 partitioned framing 正常 | SDNPR-04 · RESP-06 |
| 2 | tablet dark partitioned 截图 | `scenario-governance-domain-tablet-dark-partitioned.png` 存在且网络分区可读 | SDNPR-04 · VIS-05 |
| 3 | mobile light recovered 截图 | `scenario-governance-domain-mobile-recovered.png` 审计 recovered 首屏可见 | SDNPR-04 · RESP-07 |
| 4 | mobile dark recovered 截图 | `scenario-governance-domain-mobile-dark-recovered.png` recovered 密度一致 | SDNPR-04 · VIS-09 |
| 5 | example runtime | `data-audit="scenario-governance"` + network partition/recovery tablet/mobile light/dark 可见 | SDNPR-04 · PREVIEW-* |

**交互动作**：打开「治理场景」→ 对照 partitioned 面板 → 点击「触发审计网络恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDNPR-05 — PaaS 场景容量 network partition/recovery tablet/mobile light/dark 独立截图

**对照 golden**：`scenario-paas-domain-tablet-partitioned.png`、`scenario-paas-domain-tablet-dark-partitioned.png`、`scenario-paas-domain-mobile-partitioned.png`、`scenario-paas-domain-mobile-dark-partitioned.png`、`scenario-paas-domain-tablet-recovered.png`、`scenario-paas-domain-tablet-dark-recovered.png`、`scenario-paas-domain-mobile-recovered.png`、`scenario-paas-domain-mobile-dark-recovered.png`、`paas-template.md`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light partitioned 截图 | `scenario-paas-domain-tablet-partitioned.png` 存在且 partitioned framing 正常 | SDNPR-05 · RESP-06 |
| 2 | tablet dark partitioned 截图 | `scenario-paas-domain-tablet-dark-partitioned.png` 存在且网络分区可读 | SDNPR-05 · VIS-05 |
| 3 | mobile light recovered 截图 | `scenario-paas-domain-mobile-recovered.png` 容量 recovered 首屏可见 | SDNPR-05 · RESP-07 |
| 4 | mobile dark recovered 截图 | `scenario-paas-domain-mobile-dark-recovered.png` recovered 列表项可辨认 | SDNPR-05 · RESP-05 |
| 5 | example runtime | `data-audit="scenario-paas"` + network partition/recovery tablet/mobile light/dark 可见 | SDNPR-05 · PREVIEW-* |

**交互动作**：打开「PaaS 场景」→ 对照 partitioned 面板 → 点击「触发容量网络恢复」→ 对照 tablet/mobile light/dark 八张截图。

## 交叉引用

- 场景级矩阵抽检：`scene-scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` SDNPR-06～10
- offline/sync conflict 前置：`scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md` SDOSC-01～05
- 选型表：`decision-matrix.md` G109 场景域 network partition/recovery tablet/mobile light/dark 独立截图
- 症状路由：`upgrade-troubleshooting.md` SDNPR-01～10
- Runtime 门禁：`verifyScenarioDomainNetworkPartitionRecoveryViewportLightDarkScreenshots`
