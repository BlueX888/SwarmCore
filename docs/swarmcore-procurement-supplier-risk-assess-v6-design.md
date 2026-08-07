# 智能体业务开发功能设计文档

## 1. 需求概述

目标是把“招采一致性”和“供应商风控”改造成两个独立判断、一个统一业务动作：

- 招采一致性：合同是否偏离有效采购基线。
- 供应商准入：供应商在指定时点、指定项目中是否具备参与资格。
- 供应商风险：非直接禁入风险及履约表现，需要哪些控制措施。
- 最终动作：`PROCEED / PROCEED_WITH_CONTROLS / HOLD / BLOCK`。

智能体只处理开放文本的语义理解；身份、金额、日期、有效期、适用性、严重级别、准入和最终动作均由确定性工具及人工审批决定。

## 2. 自主决策与关键假设

### 现有方案应保留的部分

- 冻结文档版本、来源响应和结果哈希。
- Temporal 耐久执行，I/O 放在 Activity。
- 确定性风险门禁、幂等、Outbox、审计。
- REST、MCP、Web 复用应用服务。
- 精确信用代码匹配，名称命中只进入复核。

### 需要纠正的核心问题

| 问题 | 当前表现 | 优化方向 |
|---|---|---|
| 模型间接参与裁决 | 智能体输出 `changeType/severity`，规则工具采纳模型提出的升级级别，与“模型不决定严重性”冲突。[Agent 定义](C:/Project/SwarmCore/packages/registry/src/swarmcore_registry/models.py:3246)、[比较规则](C:/Project/SwarmCore/packages/application/src/swarmcore_application/procurement_supplier_risk.py:223) | Agent 只输出语义映射候选；严重级别由版本化规则矩阵计算 |
| 四方比较过度简化 | 当前优先使用“中标→投标→招标”作为参考值，未形成经过澄清、变更后的有效基线 | 新增“有效采购基线解析”工具 |
| 固定数量限制可能漏项 | 全文最多检索 50 条、提取 16 条关键条款 | 按条款域和文档角色设覆盖配额，不用总条数代表完整性 |
| 准入、风险、绩效混为一体 | 一个风险分数同时影响准入和风险等级 | 拆分资格门禁、控制型风险、绩效评价 |
| 来源完整性判断不可靠 | “所请求来源全部成功”即 `COMPLETE`，但请求方可能只配置一个来源 | 按策略规定的必查来源矩阵计算覆盖率 |
| 来源信任边界过宽 | `riskSources` 输入 Schema 仅定义为任意数组，[输入契约](C:/Project/SwarmCore/packages/capability-procurement-supplier-risk/src/swarmcore_capability_procurement_supplier_risk/input.schema.json:26) | 客户端只能提交已注册的 `providerConfigId`，禁止直接提交风险事实 |
| 审批语义过宽 | Finalizer 主要读取 `approved` 布尔值；“要求补证”也可能被错误解释为批准。[Finalizer](C:/Project/SwarmCore/packages/application/src/swarmcore_application/procurement_supplier_risk.py:657) | 使用类型化审批结果，每类动作有确定状态转换 |
| 绩效统计不完整 | 时间范围未实际过滤，重复订单仍可能参与指标，样本充分性偏粗 | 增加期间过滤、去重、数据质量及置信等级 |
| 监控可能产生假“风险解除” | 来源刷新失败时，上一期记录可能表现为消失 | 区分“确认移除”和“本次未观测” |

建议将新策略定义为 `strategy://procurement-supplier-risk/assess@6`，而不是原地改变 `@5`。

## 3. Demo 范围

范围内：

- 支持投标评审、合同签署前、合同签署后三个业务阶段。
- 处理招标文件、澄清/更正、投标文件、中标结果、合同及批准变更。
- 建立有效基线和条款血缘。
- 接入中国政府采购网、内部主数据及已授权风险 Provider。
- 输出资格、风险、绩效、一致性和最终动作。
- 支持补证、事实纠正、条款例外和职责分离审批。
- 生成快照、预警、工单、JSON/PDF 和审计记录。

边界：

- 公共资料缺少完整投标文件或已签合同，不得展示为“一致性通过”。
- 不自动形成法律意见。
- 不绕过验证码、访问限制或商业数据库授权。
- 不自动写入外部黑名单或执行供应商冻结。

## 4. 业务角色

| 角色 | 职责 | 不允许 |
|---|---|---|
| 采购经办人 | 建案、选资料、补证、发起评估 | 审批自己发起的重大例外 |
| 法务复核人 | 判断条款适用性和例外 | 修改外部风险事实 |
| 供应商管理人员 | 复核绩效、内部风险和控制措施 | 覆盖法定禁入 |
| 风控/合规人员 | 确认主体、风险记录及适用性 | 无证据解除门禁 |
| 审批人 | 对可例外差异执行 maker-checker 审批 | 用通用“批准”覆盖所有问题 |
| 审计人员 | 查看证据、策略、审批及历史 | 修改业务结果 |

## 5. 最小完整业务闭环

1. 创建采购项目、标段、评估阶段和供应商主体。
2. 冻结资料版本、SHA-256、来源、签署状态和法律效力状态。
3. 工具按阶段检查必需资料；缺失时直接生成补证任务，不浪费模型预算。
4. 身份工具验证统一社会信用代码及内部主数据映射。
5. 并行执行一致性、准入风险和绩效三个通道。
6. 条款智能体只提取、归一化和关联条款候选。
7. 基线工具合并招标要求、有效澄清、投标承诺和中标结果。
8. 规则工具比较合同与有效基线，计算差异及严重性。
9. 风险工具查询真实来源，验证身份、有效期、撤销状态和项目适用性。
10. 证据质量工具执行覆盖、时效、冲突和来源校验。
11. 按问题类型创建人工任务；审批后从检查点恢复。
12. Finalizer 分别形成一致性、资格、风险和最终动作。
13. 写入不可变快照、Finding、预警、工单、报告、Outbox 和 Audit。
14. 后续刷新只比较成功获取的同源快照。

## 6. 功能清单

| 优先级 | 功能 | 处理方式 |
|---|---|---|
| P0 | 阶段化资料检查 | Tool |
| P0 | 供应商精确身份解析 | Tool |
| P0 | 条款提取与语义映射 | Agent |
| P0 | 有效采购基线解析 | Tool |
| P0 | 一致性差异及严重级别 | Tool |
| P0 | 必查风险源采集与归一化 | Tool |
| P0 | 资格门禁与适用性判断 | Tool + 必要人工复核 |
| P0 | 证据充分性门禁 | Tool |
| P0 | 类型化人工审批 | Approval |
| P0 | 最终决策、报告和审计 | Tool |
| P1 | 供应商绩效 | Tool |
| P1 | 监控、预警和工单 | Tool/Application Service |
| P2 | 面向用户的自然语言解释 | 可选 Agent，不参与裁决 |

## 7. 真实数据与资料方案

| 用途 | 来源 | 接入策略 |
|---|---|---|
| 政府采购严重违法失信 | [中国政府采购网记录名单](https://www.ccgp.gov.cn/cr/list) | 按信用代码查询，保存记录号、查询条件、原始响应、哈希和时点 |
| 政府采购数据接口 | [中国政府采购网接口规范 v1.2](https://www.ccgp.gov.cn/sjbzjgf/202603/t20260316_26275504.htm) | 仅在取得主管部门授权时接入；普通 Demo 使用公共查询 |
| 信用记录使用口径 | [财政部财库〔2016〕125号解读](https://m.mof.gov.cn/zcjd/201608/t20160812_2387070.htm) | 策略需保存查询渠道、截止时点和证据；不能把所有不良记录自动等同法定禁入 |
| 企业登记、经营异常、严重违法 | [国家企业信用信息公示系统](https://bt.gsxt.gov.cn/) | 授权接口或人工核验回执；不绕验证码。该系统支持名称或信用代码查询，并包含经营异常、严重违法失信等信息 |
| 司法执行 | [最高人民法院执行信息公开说明](https://www.court.gov.cn/zixun/xiangqing/101002.html) | 授权 Provider 或人工核验；名称命中不得直接绑定主体 |
| 内部黑名单 | SRM/供应商主数据 | 只读 API；必须包含生效、审批、解除和适用范围 |
| 履约绩效 | ERP/SRM/QMS/验收及工单系统 | 按供应商、合同、订单和期间读取，保留源记录引用 |

每个策略配置必须声明“必查、选查、不可用时动作”。来源覆盖率按必查矩阵计算，不能按用户传入的来源数量计算。

## 8. 模型配置

主流程只保留一个智能体模型调用角色：

`agent://procurement/clause-evidence-analyst@4`

输入：

- 已冻结、按条款域检索的证据片段；
- 文档角色和效力状态；
- 项目类型、评估阶段；
- 条款字段 Schema。

输出只允许：

- `clauseFacts`：原文、类别、结构化值、证据引用；
- `mappingCandidates`：跨文档候选关系、置信度、理由；
- `ambiguities`：歧义和缺口。

禁止输出：

- `severity`；
- `BLOCK/PASS`；
- 法律适用结论；
- 条款例外批准；
- 无证据推断。

建议参数：`temperature=0`、严格 JSON Schema、一次 Schema 修复、最多 60,000 输入 tokens、8,000 输出 tokens、1.5 USD。模型失败时保留确定性可处理结果，其余进入人工复核。

## 9. 工具配置

| Tool | 职责 | 关键约束 |
|---|---|---|
| `document/read-versions@1` | 读取冻结文档 | 复用现有实现 |
| `document/provenance-validate@1` | 校验原件、版本、签署及代理资料状态 | 确定性 |
| `procurement/stage-coverage-check@1` | 按阶段检查资料 | 缺失即补证 |
| `evidence/search@2` | 按条款域和文档角色检索 | 每域独立配额，输出覆盖情况 |
| `agent-output/schema-validate@1` | 校验 Agent 输出 | 拒绝严重级别和无引用条款 |
| `procurement/baseline-resolve@1` | 生成有效采购基线 | 纳入澄清、更正和批准变更 |
| `procurement/consistency-compare@2` | 计算方向、金额、范围和条款差异 | 规则版本化，模型不能定级 |
| `supplier/identity-resolve@1` | 信用代码、主数据和名称关系 | 名称匹配只复核 |
| `supplier/risk-collect@2` | 调用服务端注册 Provider | 客户端不得提交原始风险记录或任意 endpoint |
| `supplier/risk-decide@2` | 判断有效性、适用性和资格门禁 | 资格与风险评分分离 |
| `supplier/performance-calculate@2` | 绩效计算 | 期间过滤、去重、质量和置信等级 |
| `supplier/history-diff@2` | 同源历史比较 | 来源失败不视为风险解除 |
| `procurement/evidence-gate@1` | 证据覆盖、时效、冲突检查 | 替代证据复核 Agent |
| `finalize/report/record` | 定案、报告和留痕 | 复用现有事务及幂等机制 |

## 10. 智能体设计

只保留一个主流程智能体。

| 智能体 | 负责 | 不负责 |
|---|---|---|
| 条款证据分析智能体 | 开放文本提取、条款分类、字段归一化、跨文档语义映射候选 | 严重性、准入、评分、审批、法律结论 |

删除主流程中的：

- `supplier-risk-analyst`：风险解释可由规则结果和模板报告完成。
- `evidence-quality-reviewer`：覆盖、时效、身份、冲突均应由确定性 Tool 验证。

如确实需要自然语言报告，可在最终结果生成后按需调用“结果解释智能体”，其输出明确标记为非权威叙述，不回写决策字段。

## 11. 运行与协作策略

```text
输入校验
  → 文档冻结 + 主体验证
  → 阶段资料检查
      ├─ 不足：补证任务 → HOLD
      └─ 通过：
          ├─ 条款检索 → 条款 Agent → Schema 校验
          │              → 有效基线 → 一致性规则
          ├─ 风险源采集 → 身份/时效/适用性 → 资格与风险规则
          └─ 绩效读取 → 去重/期间过滤 → 绩效规则
  → 证据质量门禁
  → 类型化人工任务
  → 最终动作 → 报告 → 快照/预警/审计
```

运行预算：

- `maxAgents: 1`
- `maxParallelism: 4`
- `maxDuration: 20 分钟`
- 只读外部查询最多重试 2 次；
- 模型 Schema 修复最多 1 次；
- 写入通过 Effect 和业务幂等键去重；
- `asOf` 必填，禁止缺失时回退到系统当前日期。

## 12. 人工介入机制

人工任务不得再使用通用 `approved: true/false`，应采用类型化动作：

| 任务类型 | 可选动作 |
|---|---|
| `IDENTITY_REVIEW` | 确认主体、排除同名、要求补充主数据 |
| `SOURCE_FACT_REVIEW` | 确认记录、提交撤销/更正证据、要求重新查询 |
| `CLAUSE_MAPPING_REVIEW` | 确认映射、拆分映射、标记不可比较 |
| `CLAUSE_EXCEPTION_APPROVAL` | 批准例外、驳回例外、要求修改合同 |
| `EVIDENCE_REQUEST` | 提交资料、维持等待、终止评估 |

规则：

- `REQUEST_EVIDENCE` 必须保持 `HOLD`，不能转为条件通过。
- 法定或策略定义的不可例外门禁不能被直接批准覆盖。
- 风控人员可以基于新证据认定“记录不适用”，但必须留下事实纠正链。
- 重大条款例外至少采购/法务双角色审批，发起人不得审批自己的申请。

## 13. 异常处理

| 异常 | 自动结果 |
|---|---|
| 必需资料缺失 | `HOLD + EVIDENCE_REQUEST` |
| 合同模板冒充已签合同 | `INVALID_DOCUMENT_ROLE` |
| 名称相同但信用代码不同 | 不计分、不门禁，进入身份复核 |
| 必查来源失败 | `eligibility=UNKNOWN`，政府采购默认 `HOLD` |
| Provider 返回无来源哈希记录 | 丢弃记录并记录来源质量异常 |
| 模型输出严重级别 | Schema 拒绝并修复一次 |
| 模型无法判断弱化关系 | `RELATION_UNCONFIRMED`，人工复核 |
| 历史来源本次失败 | `NOT_OBSERVED`，不生成“已解除” |
| 绩效样本不足 | `PERFORMANCE_UNKNOWN`，不伪造分数 |
| 非法审批或工单流转 | 409/422，写安全审计 |

## 14. 权限与结果追溯

- Provider 配置、域名和凭据由服务端管理，业务输入只能引用配置 ID。
- 所有读取保持 tenant/project/case 边界。
- 保存文档版本、来源响应、规则、策略、模型、Prompt、审批和结果哈希。
- 原始外部证据与标准化观察分开存储。
- Agent 结论必须能回到具体 `documentVersionId + evidenceSpan`。
- 每个最终动作保存 `decisionReasonCodes`，避免只留自然语言。
- 结果保留旧策略版本，不将 `@5` 历史结果用 `@6` 规则重新解释。

## 15. 核心数据结构与接口

建议增加或调整：

- `DocumentSnapshot`：文档角色、效力、签署状态、版本、哈希。
- `ClauseFact`：条款类别、原文、结构化值、证据。
- `ClauseMappingCandidate`：Agent 候选，不是业务事实。
- `ApplicableBaseline`：生效基线及来源优先级。
- `ConsistencyFinding`：规则计算的差异、级别、可否例外。
- `SupplierIdentityResolution`：信用代码和主数据解析。
- `RiskSourceRequirement`：策略规定的必查来源。
- `RiskSourceSnapshot`：原始响应、查询条件、哈希。
- `RiskObservation`：标准化记录、有效期、适用范围。
- `ReviewTask`：类型、所需角色、动作、证据。
- `FinalDecision`：

```json
{
  "evidenceStatus": "COMPLETE",
  "consistencyDecision": "EXCEPTION_REQUIRED",
  "eligibilityDecision": "ELIGIBLE",
  "riskTier": "MEDIUM",
  "performanceStatus": "SCORED",
  "action": "PROCEED_WITH_CONTROLS",
  "reasonCodes": []
}
```

REST 和 MCP 继续复用 `ProcurementSupplierRiskService`。创建评估、刷新、审批和工单写入均要求幂等键。

## 16. Demo 演示流程

建议演示“合同签署前审查”：

1. 上传真实招标文件、澄清更正、投标响应、中标结果和待签合同。
2. 系统展示每份资料的真实性和效力状态。
3. 使用一个存在付款条件弱化的合同版本。
4. Agent 提取并关联付款条款，但不输出严重级别。
5. 规则工具判定合同相对有效基线发生重大弱化。
6. 使用真实信用代码查询中国政府采购网。
7. 如存在有效且适用的禁入记录，资格输出 `INELIGIBLE`，最终 `BLOCK`。
8. 创建法务条款例外任务，展示条款例外不能覆盖供应商资格门禁。
9. 提交更正合同后重跑，从检查点恢复。
10. 展示结果哈希、证据、审批、快照、预警、工单和审计链。

如果只有公开招标文件、中标公告和合同模板，演示终态应为 `HOLD/INSUFFICIENT_EVIDENCE`，不能冒充完整一致性验收。

## 17. 验收标准

- Given Agent 输出 `severity`，When Schema 校验，Then 拒绝该输出。
- Given 合同价格降低但范围、数量和质量不变，Then 不因文本不同自动判为 `BLOCKER`。
- Given 有效澄清文件，Then 基线使用澄清后的要求。
- Given 客户端直接提交风险 `records` 或任意 endpoint，Then 请求被拒绝。
- Given 只配置一个非完整来源，Then 来源状态不得为 `COMPLETE`。
- Given 精确主体、有效期间、项目适用的禁入记录，Then 输出 `INELIGIBLE + BLOCK`。
- Given 同名不同代码，Then 不得触发门禁。
- Given 审批动作是 `REQUEST_EVIDENCE`，Then 最终动作保持 `HOLD`。
- Given 上一期存在风险、本次来源失败，Then 不得生成“风险已解除”。
- Given 重复订单或期间外记录，Then 不参与绩效计算。
- Given 不同租户读取评估，Then 返回不可见并记录安全审计。
- Given REST 与 MCP 发起相同业务操作，Then 产生一致结果和同一应用服务追溯。

实施后至少运行专项单元测试、API 集成测试、Web 结果页测试，并根据影响范围执行 Ruff、mypy、完整单元测试和 Web lint/test/build。

## 18. 暂不实现内容

- 股权穿透和集团关联图谱。
- 跨境制裁及出口管制筛查。
- 预测供应商破产或违约的机器学习模型。
- 自动冻结供应商、自动修改合同或自动发送监管通知。
- 替代律师、采购委员会或监管机构作出正式认定。

## 19. 风险说明

| 风险 | 缓解 |
|---|---|
| 条款语义映射错误 | Agent 仅给候选；证据引用、Schema、规则和人工复核共同控制 |
| 法律适用口径变化 | 资格规则按地域、采购方式、阶段和版本配置 |
| 公共来源页面变化 | Provider 适配器、原始响应哈希、契约测试和显式失败 |
| 风险记录误绑定 | 信用代码精确匹配；名称匹配不触发门禁 |
| 缺资料却错误放行 | `UNKNOWN` 默认映射为 `HOLD` |
| 审批错误覆盖门禁 | 类型化动作、可例外矩阵和职责分离 |
| 成本过高 | 单主智能体、先规则预检、按条款域检索、失败不反复调用模型 |

本方案的核心调整是：从“3 个智能体串行解释结果”改为“1 个智能体处理非结构化语义，确定性工具负责全部业务裁决”。

## 20. 相对 `@5` 的文件级变更清单（实施盘点）

| 区域 | `@5` 现状 | `@6` 目标变更 |
|---|---|---|
| 策略图 | `packages/.../strategy.json`：3 Agent + 11 Tool | 新增 `strategy.v6.json`：仅 `clause-evidence-analyst@4`；去掉主流程 risk-analyst / evidence-quality-reviewer |
| Agent 契约 | `models.py` `@3` 输出含 `severity`/`changeType` | 新增 `@4`：仅 `clauseFacts` / `mappingCandidates` / `ambiguities` |
| 输出校验 | 依赖 Adapter Schema | 新增 `tool://agent-output/schema-validate@1`，拒绝裁决字段 |
| 基线 | `compare_procurement_clauses` 用中标→投标→招标 | 新增 `baseline-resolve@1` + `consistency-compare@2` |
| 风险采集 | 客户端可传 `records`/`endpoint` | `risk-collect@2` 仅接受已注册 `providerConfigId` |
| 准入/风险 | `risk-decide@1` 混分 | `risk-decide@2` 拆分 `eligibilityDecision` 与 `riskTier` |
| 审批/定案 | `approved` 布尔 + PASS/CONDITIONAL… | 类型化动作；`REQUEST_EVIDENCE→HOLD`；`FinalDecision.action` |
| 能力包 | `assess@5` / 1.0.4 | Pack `1.0.5` 默认执行 `assess@6`，保留 `assess@5` 可解析 |

P0 本轮优先竖切：Agent 契约 → 类型化定案 → providerConfigId 门禁 → 基线/比较骨架 → eligibility 拆分 → `@6` 注册且不破坏 `@5`。
