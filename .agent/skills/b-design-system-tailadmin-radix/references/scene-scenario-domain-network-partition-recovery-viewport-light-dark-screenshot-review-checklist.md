# 场景 Scenario Domain Network Partition Recovery Viewport Light/Dark Screenshot 评审清单

> DOCS-060 / G109 产物。对 Agent 生成或人工改写的 **5 大业务场景域**（BI、DevOps、Gateway、Governance、PaaS）执行**可复现场景级 tablet/mobile light/dark 四主题 network partition/disconnect recovery 独立截图抽检**，确保各域 section 在网络分区检测态与连接恢复态、平板与移动视口下有 light + dark 独立 golden 截图矩阵，并与 `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md`（SDNPR-01～05）、`scene-scenario-domain-offline-sync-conflict-viewport-light-dark-screenshot-review-checklist.md`（SDOSC-06～10）、`decision-matrix.md` 及 example runtime 截图对照。

## 使用时机

| 时机 | 必读章节 |
|---|---|
| PR / MR 合并前场景域 network partition/recovery tablet/mobile light/dark 独立截图矩阵抽检 | 对应 SDNPR 块 + `quality-rubric.md` |
| BI Analytics 指标 network partition/recovery tablet/mobile light/dark 独立截图 | SDNPR-06 + `tailadmin-bi-analytics` |
| DevOps 阶段 network partition/recovery tablet/mobile light/dark 独立截图 | SDNPR-07 + `scenario-devops` |
| Gateway 端点 network partition/recovery tablet/mobile light/dark 独立截图 | SDNPR-08 + `scenario-gateway` |
| Governance 审计行 network partition/recovery tablet/mobile light/dark 独立截图 | SDNPR-09 + `scenario-governance` |
| 场景域 network partition/recovery tablet/mobile light/dark 独立截图束缺门禁 | SDNPR-10 + `verify:runtime` `scenarioDomainNetworkPartitionRecoveryViewportLightDarkScreenshotStates` + `verifyScenarioDomainNetworkPartitionRecoveryViewportLightDarkScreenshots` |

## 通用前置

1. 先完成 `scenario-domain-network-partition-recovery-viewport-light-dark-screenshot-review-checklist.md` SDNPR-01～05（控件级）。
2. 对照 `examples/b-design-system-tailadmin-radix/artifacts/runtime-verify/scenario-*-domain-{tablet,mobile}{,-dark}-{partitioned,recovered}.png` 共 40 张 network partition/recovery 独立截图。
3. 抽检至少 **BI 场景 + 1 个非 BI 场景域 + Gateway 或 DevOps** tablet/mobile light/dark network partition/recovery 独立截图。
4. 视口 **tablet 1024×768**、**mobile 390×844**；dark 截图必须通过 AppShell「切换主题」进入 `.app.dark`。
5. 组件/页面选型争议必须先读 `decision-matrix.md` **场景域 network partition/recovery tablet/mobile light/dark 独立截图（G109）** 选型表。
6. 检索路径见 `agent-retrieval-guide.md` 场景域 network partition/recovery tablet/mobile light/dark 独立截图抽检行。
7. 症状路由见 `upgrade-troubleshooting.md` SDNPR-01～10。
8. 业务部署验证交叉引用见 `business-validation-checklist.md` MS-09～13 场景冒烟检查项。

## SDNPR-06 — BI Analytics 指标 network partition/recovery tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-bi-domain-tablet-partitioned.png`、`scenario-bi-domain-mobile-dark-recovered.png`、`tailadmin-bi-analytics`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark partitioned | `scenario-bi-domain-tablet-partitioned.png` + `scenario-bi-domain-tablet-dark-partitioned.png` partitioned framing 正常 | SDNPR-06 · RESP-06 |
| 2 | mobile light/dark recovered | `scenario-bi-domain-mobile-recovered.png` + `scenario-bi-domain-mobile-dark-recovered.png` recovered framing 正常 | SDNPR-06 · RESP-07 |
| 3 | 指标 network partition/recovery | 分区 banner + 受影响节点摘要 + 恢复完成 banner tablet/mobile light/dark 首屏可见 | SDNPR-06 · PAT-06 |
| 4 | 主题对比 | mobile dark 下 partitioned banner 与 recovered banner 层级可辨认 | SDNPR-06 · VIS-06 |
| 5 | example runtime | BI 场景 section + 八视口双主题 partitioned/recovered 截图全过 | SDNPR-06 · PREVIEW-* |

**交互动作**：打开 BI 场景 → 对照 partitioned 面板 → 点击「触发指标网络恢复」→ 对照 tablet/mobile light/dark 八张 network partition/recovery 截图。

## SDNPR-07 — DevOps 阶段 network partition/recovery tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-devops-domain-tablet-partitioned.png`、`scenario-devops-domain-mobile-dark-recovered.png`、`scenario-devops`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark partitioned | `scenario-devops-domain-tablet-partitioned.png` + `scenario-devops-domain-tablet-dark-partitioned.png` partitioned framing 正常 | SDNPR-07 · RESP-06 |
| 2 | mobile light/dark recovered | `scenario-devops-domain-mobile-recovered.png` + `scenario-devops-domain-mobile-dark-recovered.png` recovered framing 正常 | SDNPR-07 · RESP-07 |
| 3 | 阶段 network partition/recovery | 流水线分区 banner + 恢复完成摘要 tablet/mobile light/dark 首屏可见 | SDNPR-07 · PAT-07 |
| 4 | recovered 态 | mobile dark 下 recovered 文案与查看详情按钮可辨认 | SDNPR-07 · INTER-07 |
| 5 | example runtime | DevOps 场景 section + 八视口双主题 partitioned/recovered 截图全过 | SDNPR-07 · PREVIEW-* |

**交互动作**：打开 DevOps 场景 → 对照 partitioned 面板 → 点击「触发阶段网络恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDNPR-08 — Gateway 端点 network partition/recovery tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-gateway-domain-tablet-partitioned.png`、`scenario-gateway-domain-mobile-dark-recovered.png`、`scenario-gateway`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark partitioned | `scenario-gateway-domain-tablet-partitioned.png` + `scenario-gateway-domain-tablet-dark-partitioned.png` partitioned framing 正常 | SDNPR-08 · RESP-06 |
| 2 | mobile light/dark recovered | `scenario-gateway-domain-mobile-recovered.png` + `scenario-gateway-domain-mobile-dark-recovered.png` recovered framing 正常 | SDNPR-08 · RESP-07 |
| 3 | 端点 network partition/recovery | 端点分区 banner + 恢复完成摘要 tablet/mobile light/dark 首屏可见 | SDNPR-08 · PAT-08 |
| 4 | partitioned 态 | mobile dark 下受影响节点与 banner 可辨认 | SDNPR-08 · A11Y-08 |
| 5 | example runtime | Gateway 场景 section + 八视口双主题 partitioned/recovered 截图全过 | SDNPR-08 · PREVIEW-* |

**交互动作**：打开 Gateway 场景 → 对照 partitioned 面板 → 点击「触发端点网络恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDNPR-09 — Governance 审计行 network partition/recovery tablet/mobile light/dark 独立截图矩阵

**对照 golden**：`scenario-governance-domain-tablet-partitioned.png`、`scenario-governance-domain-mobile-partitioned.png`、`scenario-governance-domain-mobile-dark-recovered.png`、`scenario-governance`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | tablet light/dark partitioned | `scenario-governance-domain-tablet-partitioned.png` + `scenario-governance-domain-tablet-dark-partitioned.png` partitioned framing 正常 | SDNPR-09 · RESP-06 |
| 2 | mobile light/dark recovered | `scenario-governance-domain-mobile-recovered.png` + `scenario-governance-domain-mobile-dark-recovered.png` recovered framing 正常 | SDNPR-09 · RESP-07 |
| 3 | 审计 network partition/recovery | 审计分区 banner + 恢复完成摘要 tablet/mobile light/dark 首屏可见 | SDNPR-09 · PAT-09 |
| 4 | recovered 文案 | mobile dark 下「网络连接已恢复，待提交策略已进入重放队列」文案可辨认 | SDNPR-09 · A11Y-09 |
| 5 | example runtime | Governance 场景 section + 八视口双主题 partitioned/recovered 截图全过 | SDNPR-09 · PREVIEW-* |

**交互动作**：打开 Governance 场景 → 对照 partitioned 面板 → 点击「触发审计网络恢复」→ 对照 tablet/mobile light/dark 八张截图。

## SDNPR-10 — 场景域 network partition/recovery tablet/mobile light/dark 独立截图束

**对照 golden**：40 张 `scenario-*-domain-{tablet,mobile}{,-dark}-{partitioned,recovered}.png` + `scenarioDomainNetworkPartitionRecoveryViewportLightDarkScreenshotStates.networkPartitionRecoveryStateMatrixComplete = true`

| # | 检查项 | 通过标准 | 失败写回 |
|---:|---|---|---|
| 1 | 40 张截图存在 | 五域 × tablet/mobile × light/dark × partitioned/recovered 全量 golden 存在 | SDNPR-10 · VAL-* |
| 2 | runtime 门禁 | `verifyScenarioDomainNetworkPartitionRecoveryViewportLightDarkScreenshots` 通过 | SDNPR-10 · PREVIEW-* |
| 3 | partitioned 态 | 五域 `data-audit="scenario-domain-partitioned-overlay"` `data-state="partitioned"` 可见 | SDNPR-10 · LOGIC-* |
| 4 | recovered 态 | 五域点击 recovery trigger 后 `role="status"` + `data-state="recovered"` 可见 | SDNPR-10 · ASYNC-* |
| 5 | 矩阵完整 | `networkPartitionRecoveryStateMatrixComplete = true` | SDNPR-10 · VAL-* |

**交互动作**：运行 `npm run verify:runtime -w examples/b-design-system-tailadmin-radix` → 确认 40 张 network partition/recovery 截图与门禁 JSON 输出。
