# 智能体业务开发功能设计文档

## 1. 需求概述

### 业务目标

建设“招采一致性与供应商风控智能体”，对招标/采购文件、投标/响应文件、中标通知书和
合同建立四方条款血缘，输出分级差异；同时获取真实多源风险、计算供应商绩效、执行准入
门禁，并形成预警、工单、不可变历史和审计闭环。

### 用户、输入与输出

- 用户：采购经办人、法务、供应商管理、风控复核人和审计人员。
- 必需输入：采购项目、供应商统一社会信用代码、四类业务文档、数据截止时点。
- 可选输入：澄清/变更、补充协议、订单/交付/验收/质量/投诉/整改、内部黑名单和授权
  风控 Provider。
- 输出：条款血缘与分级差异、风险与绩效、准入决策、证据引用、PDF 报告、预警、工单、
  历史变化、Run 过程和审计记录。

成功定义为“真实业务输入 → 真实数据获取 → Agent 处理 → Tool 执行 → 业务结果与动作 →
过程和依据可追溯”全部可观察，且不以模型意见覆盖确定性门禁。

## 2. 自主决策与关键假设

| 决策/假设 | 依据 | 影响 | 验证方式 |
|---|---|---|---|
| 地域按中国大陆招采场景实现 | 用户使用中文且要求招投标、统一信用代码和黑名单 | 首个内置公开源为中国政府采购网 | 用真实信用代码查询并冻结响应哈希 |
| 企业身份以统一社会信用代码为主键 | 名称存在同名、曾用名和录入差异 | 名称匹配不计分、不触发硬门禁 | `EXACT_CREDIT_CODE` 与 `NAME_ONLY` 单元/集成测试 |
| 模型只做语义提取与解释 | 金额、日期、计分、状态需要可重放 | 最终规则由确定性 Tool 执行 | 相同输入得到相同结果哈希 |
| 监控刷新由 Case Assessment 发起 | REST、MCP、Web 必须复用同一应用服务 | 不建立第二套业务执行链 | REST/MCP 契约和 Assessment 追溯 |
| “实时”定义为主动刷新或外部调度按频率触发 | 公共网站不提供面向普通调用者的推送订阅 | Demo 支持立即刷新，调度器可按小时/日/周调用 | 刷新后生成新 Evaluation 与快照 |
| 商业数据只能使用客户已授权的 Provider | 商业风控与司法数据存在授权和访问限制 | Demo 默认不伪造未授权结果 | Provider 失败输出 `FAILED` 并进入人工复核 |

## 3. Demo 范围

### 范围内

- 四类冻结文档的条款提取候选与确定性四方比对；
- `BLOCKER/HIGH/MEDIUM/LOW` 差异清单和证据定位；
- 中国政府采购网严重违法失信记录实时查询；
- 获授权 JSON HTTPS Provider、内部黑名单和绩效数据接入；
- 风险计分、硬门禁、绩效评分、历史变化；
- 监控、预警、工单状态机、Finding、Outbox、Audit、JSON/PDF；
- REST、MCP、Web 共用应用服务并可下钻 Run。

### Demo 边界

- 不替代法务结论、采购审批或监管机关认定；
- 不绕过验证码、访问控制或网站条款抓取 GSXT/司法/税务数据；
- 未授权来源失败时不生成替代事实；
- Demo 验收是本地实现证据，不等同生产资格。

## 4. 业务角色

| 角色 | 职责与目标 | 关键权限 |
|---|---|---|
| 采购经办人 | 建案、选择资料、发起评估、查看差异 | `case.create/read/assess`、`document.read` |
| 风控复核人 | 复核身份、来源冲突和硬门禁，处理预警 | `supplier-risk.read/review/refresh` |
| 法务/审批人 | 审批重大条款例外，但不能覆盖有效硬门禁 | `approval.respond` |
| 工单处理人 | 接单、调查、记录处置并关闭 | `supplier-risk.work-order` |
| 审计人员 | 只读结果、证据、版本、Run 和动作历史 | `procurement-risk.audit`、`report.read` |

## 5. 最小完整业务闭环

1. 用户创建采购与供应商业务对象，上传并绑定四类资料。
2. Workbench 冻结文档版本、SHA-256、主体和 Case revision。
3. 条款 Agent 提取四类文档的条款和语义匹配候选。
4. 风险采集 Tool 按信用代码查询真实来源，保存获取时点、记录号、URL 和响应哈希。
5. 确定性 Tool 并行完成四方比对、绩效计算、风险计分和硬门禁。
6. 风险 Agent 解释已冻结事实；证据质量 Agent 独立检查覆盖、身份和冲突。
7. 重大差异、同名记录、来源失败或证据缺口进入人工审批；有效硬门禁不能被审批覆盖。
8. Finalizer 生成结构化结果和哈希，报告 Tool 生成同源 PDF。
9. Recorder 幂等写入 Evaluation、Finding、Report、快照、Alert、Outbox 和 Audit。
10. 预警创建工单，按 `OPEN → IN_PROGRESS → RESOLVED/CLOSED` 受控流转。
11. 后续刷新重复获取真实数据，与上一不可变快照比较并展示变化。

完成状态为 `PASS`、`CONDITIONAL_PASS`、`REVIEW_REQUIRED` 或 `BLOCK`；采集失败仍以有证据
的 `REVIEW_REQUIRED` 收口，不伪造成功。

## 6. 功能清单

| 优先级 | 功能 | 使用者 | 输入/处理 | 输出与依赖 |
|---|---|---|---|---|
| P0 | 四方条款血缘 | 采购、法务 | 四类冻结文档；Agent 候选 + 确定性比对 | 血缘、变化类型、分级差异、证据 |
| P0 | 多源风控采集 | 风控 | 信用代码、来源配置、截止时点 | 来源状态、风险观察、响应哈希 |
| P0 | 身份与硬门禁 | 风控 | 精确身份风险观察 | 风险等级、分数、`BLOCK` |
| P0 | 结果与证据追溯 | 全角色 | 规则/模型/工具/文档/来源版本 | JSON、PDF、Finding、Run、Audit |
| P0 | 监控与预警 | 风控 | 刷新结果和上一快照 | 不可变快照、变化、Alert、Outbox |
| P0 | 风控工单 | 工单处理人 | Alert、负责人、处置结论 | 状态机和不可变动作历史 |
| P1 | 供应商绩效 | 供应商管理 | 订单、交付、质量、验收、服务、投诉 | 加权分、覆盖率、样本充分性 |
| P1 | 授权 Provider | 风控管理员 | HTTPS、字段映射、Vault `secretRef` | 标准化风险记录或显式失败 |

## 7. 真实数据与资料方案

| 用途 | 具体来源与访问地址 | 真实数据证明 | 接入/认证 | 字段、更新与缓存 | 替代和合规 |
|---|---|---|---|---|---|
| 政府采购严重违法失信 | [中国政府采购网记录查询](https://www.ccgp.gov.cn/cr/list) | 2026-07-28 用信用代码 `91310116740594799B` 获取记录 `2c8382ba9e61ca97019f83cfaaa205a6` | 内置 `CCGP_SERIOUS_ILLEGAL`，公共查询无凭据 | 名称、信用代码、事由、处罚、日期、执法单位；每次刷新保存响应哈希 | 页面变更时显式 `FAILED`，不绕过限制 |
| 政府采购数据接口 | [接口规范 v1.2](https://www.ccgp.gov.cn/sjbzjgf/202603/t20260316_26275504.htm) | 规范包含严重违法失信记录推送、撤销、查询和全量接口 | 主管部门授权后用 HTTPS Provider | 记录 ID、状态、撤销信息；按授权频率 | 无授权时使用公开查询 |
| 企业登记/异常/处罚 | [国家企业信用信息公示系统](https://www.gsxt.gov.cn/) | 国家法定企业信用公示入口 | 获授权接口或客户已采购 Provider | 登记状态、异常、处罚、严重违法；按来源更新 | 不绕验证码；人工核验回执 |
| 司法执行 | [中国执行信息公开网说明](https://www.court.gov.cn/zixun/xiangqing/101002.html) | 最高人民法院公开查询范围说明 | 获授权接口或人工核验 | 案号、立案/履行状态、发布时间 | 身份非精确时只进入复核 |
| 税收违法 | [国家税务总局规则](https://www.chinatax.gov.cn/chinatax/n810214/n810641/c102061/c102062/c5171873/content.html) | 官方公布主体规则和字段 | 省级公开查询或授权接口 | 主体、信用代码、事实、处罚 | 保存核验时点与来源 |
| 市场监管严重违法 | [市场监管总局管理办法](https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2026/art_3aadc26ec30e4bab9c16b5f953014172.html) | 官方管理规则 | 公示系统或授权接口 | 列入/移出原因和日期 | 不把规则页当企业命中记录 |
| 信用记录使用口径 | [财政部通知](https://www.ccgp.gov.cn/zcfg/mof/201608/t20160811_7169275.htm) | 要求明确查询渠道、截止时点和证据留存 | 作为规则依据，不直接采集 | 渠道、时点、联合体逐一查询 | 由采购人确认最终适用范围 |
| 内部绩效与黑名单 | ERP/SRM/QMS/工单系统 | 客户业务主数据和交易记录 | 授权 API/导入，最小读权限 | 订单、交付、质检、验收、投诉、整改；增量游标 | 来源失败不沿用过期事实为新事实 |

外部证据至少保存 `sourceRef/sourceRecordId/fetchedAt/sourceUrl/responseHash`。Provider 最多
10 个，响应最多 10 MiB，默认 30 秒超时；主机必须进入
`SWARMCORE_SUPPLIER_RISK_ALLOWED_HOSTS`。

## 8. 模型配置

| 模型职责 | 候选/能力要求 | 输入输出与参数 | 成本与降级 |
|---|---|---|---|
| 条款语义提取与匹配 | `model://general@1` 路由到支持长上下文和 JSON Schema 的托管模型 | 冻结条款片段；温度低；只输出候选、摘要、置信度和证据引用 | 文档分段与 Top-K 控制；失败进入规则比对和人工复核 |
| 风险解释 | 同一逻辑模型，运行时冻结 Provider/模型版本 | 只读标准化风险、绩效和历史；禁止重算分数 | 失败不影响确定性硬门禁 |
| 证据质量复核 | 同一逻辑模型的独立节点 | 只输出覆盖/冲突/身份问题和审批建议 | 失败时强制人工复核 |

单次运行预算上限为 120,000 tokens、3 USD、30 分钟；模型输出必须经过 Schema 校验。

## 9. 工具配置

| Tool | 调用时机与职责 | 权限/超时/幂等 | 失败回退 |
|---|---|---|---|
| `document/read-versions` | 冻结后读取文档版本 | 只读、版本哈希校验、幂等 | 资料缺失进入 Approval |
| `document/coverage-check` | 检查四类资料覆盖 | 只读、确定性 | 阻止无证据自动结论 |
| `evidence/search` | 在冻结文档中检索条款 | 只读、最多 50 条命中 | 返回空覆盖，不补造文本 |
| `procurement/consistency-compare` | Agent 候选后计算四方差异 | 纯函数、幂等 | 输入无效则运行失败 |
| `supplier/risk-collect` | 查询 CCGP/授权 Provider/内部事实 | HTTPS allowlist、Vault、30 秒、幂等读取 | 单源失败标记 `FAILED` |
| `supplier/performance-calculate` | 计算五维绩效 | 纯函数、最少 3 个订单/60% 权重 | 输出 `INSUFFICIENT_DATA` |
| `supplier/risk-decide` | 风险计分与硬门禁 | 纯函数、规则版本化 | 不允许 Agent 覆盖 |
| `supplier/history-diff` | 比较上一快照 | 纯函数、幂等 | 首次运行输出无实质变化 |
| `finalize/report/record` | 定案、PDF、持久化与事件 | 结果哈希、Effect、事务 Outbox | 重试不重复写入 |

## 10. 智能体设计

| Agent | 职责与上下文 | 可用 Tool | 禁止事项 |
|---|---|---|---|
| `clause-evidence-analyst` | 从编排器提供的四类冻结文档检索结果提取条款和语义匹配候选 | 无直接 Tool；只接收已冻结检索结果 | 不决定严重级别、不批准例外、不虚构文本 |
| `supplier-risk-analyst` | 解释已冻结的风险、绩效和历史变化 | 风险/绩效/历史结果只读 | 不创建黑名单事实、不改分数或门禁 |
| `evidence-quality-reviewer` | 独立复核证据覆盖、身份、时效与冲突 | 冻结证据只读 | 不修改 Finding 或最终决策 |

三者通过结构化 JSON 交接；最终业务事实只由确定性 Tool 生成。

## 11. 运行与协作策略

`strategy://procurement-supplier-risk/assess@5` 由 Temporal 耐久执行，网络、数据库、模型和文件 I/O
全部位于 Activity：

```text
冻结文档 ─ 覆盖/检索 ─ 条款 Agent ─ 条款比对 ───────────┐
真实风险采集 ─ 绩效计算 ─ 风险决策 ─ 历史比较 ─ 风险 Agent ─┤
证据质量 Agent ─ Router ─ Approval/自动继续 ─ Finalize ─ Report ─ Record
```

- 最大 3 个 Agent、并行度 3；
- Tool/Agent 失败按既有重试策略执行，副作用以 Effect/幂等键去重；
- 取消由 Run 控制面处理；未完成副作用不标成功；
- 状态与结果持久化到 PostgreSQL，事件通过事务 Outbox 发布；
- Provider 部分失败允许进入 `REVIEW_REQUIRED`，所有必需事实失败则失败收口。

## 12. 人工介入机制

触发条件：`BLOCKER/HIGH` 重大差异、同名身份、来源冲突/失败、资料缺失、绩效样本不足或
证据质量不合格。

审批界面必须展示差异前后文本、文档页码/哈希、外部记录号/URL/时点、规则版本、模型
解释和确定性结论。审批人可“确认、驳回、要求补证、批准条款例外”；有效供应商硬门禁
不能被条款例外覆盖。每次动作写 actor、时间、理由和恢复节点。

## 13. 异常处理

| 异常 | 检测与提示 | 自动处置 | 人工处置/终态 |
|---|---|---|---|
| 文档缺失/不可读 | 覆盖 Tool | 停止自动定案 | 补资料后重新评估 |
| 信用代码为空/不合法 | Schema/采集 Tool | 拒绝采集 | 修正主体档案 |
| 名称命中但代码不符 | `NAME_ONLY` | 不计分、不门禁 | 确认主体关系 |
| Provider 超时/非 2xx/解析失败 | 来源状态 | 有界重试后 `FAILED` | `REVIEW_REQUIRED` |
| 明文凭据或非 HTTPS/非 allowlist | 输入校验 | fail closed | 改用 Vault 与授权域名 |
| 模型输出不合 Schema | Model Gateway | 重试/降级 | 人工复核 |
| 重复刷新/写入 | 幂等键、结果哈希 | 返回既有 Evaluation/快照/工单 | 无需人工 |
| 非法工单流转 | 状态机 | 409/422 拒绝 | 按允许路径重试 |

## 14. 权限与结果追溯

- 所有业务表保留 tenant/project 字段并启用、强制 RLS；
- 商业 Provider 凭据只保存 Vault `secretRef`，Tool Gateway 运行时注入；
- 原始 `Authorization/x-api-key/cookie` 头禁止进入业务输入；
- 文档、外部响应、规则、策略、模型、报告和最终结果均冻结版本或哈希；
- 快照和工单动作由数据库触发器禁止更新/删除；
- 监控、快照、预警、工单动作、Finding、Report、Outbox 和 Audit 可通过 ID 串联；
- Demo 保留期沿用项目数据策略，生产保留期和法务保全由租户配置。

## 15. 核心数据结构与接口

核心实体：

- `SupplierRiskMonitor`：Case、供应商、频率、来源配置、最近快照；
- `SupplierRiskSnapshot`：Evaluation、时点、决策、分数、覆盖、变化、结果哈希；
- `SupplierRiskAlert`：类型、级别、证据、去重键、状态；
- `SupplierRiskWorkOrder`：优先级、负责人、状态、截止时间、处置结论；
- `SupplierRiskWorkOrderAction`：不可变的状态变更和备注。

REST 前缀 `/v1/projects/{projectId}/procurement-supplier-risk`，覆盖监控创建/读取/刷新、
历史、预警和工单列表/创建/更新。MCP 提供同等七个操作并复用
`ProcurementSupplierRiskService`。创建监控和工单要求 `Idempotency-Key`；刷新复用
Case Assessment 幂等语义。

关键枚举：

- 决策：`PASS/CONDITIONAL_PASS/REVIEW_REQUIRED/BLOCK`；
- 差异：`UNCHANGED/INTERMEDIATE_VARIANCE/MISSING/ADDED/CHANGED/WEAKENED/CONFLICT`；
- 工单：`OPEN/IN_PROGRESS/RESOLVED/REJECTED/CLOSED`。

## 16. Demo 演示流程

1. 在“业务工作”启用 `procurement-supplier-risk@1.0.4`。
2. 创建采购与供应商主体，上传四类真实业务文档并检查资料覆盖。
3. 默认来源选择 `official://ccgp/serious-illegal`，输入真实信用代码。
4. 发起办理；Run 中可见 3 个 Agent、风险采集和确定性 Tool 节点。
5. 展示四方条款链、分级差异、风险/绩效、身份匹配、记录号、URL、获取时间和哈希。
6. 命中硬门禁时展示 `BLOCK`、Finding 和 Alert。
7. 从 Alert 创建工单，执行“开始处理 → 关闭”，查看三条动作记录。
8. 点击“立即刷新”，查看新 Evaluation、不可变快照和历史变化。
9. 下钻 Run、PDF、Audit 和 Outbox，核对同一结果哈希。

真实公开源复验样例（2026-07-28）：供应商“上海龙田数码科技有限公司”，信用代码
`91310116740594799B`，获取记录 `2c8382ba9e61ca97019f83cfaaa205a6`，精确身份匹配，
风险类型 `GOVERNMENT_PROCUREMENT_BAN`，有效期 2026-07-12 至 2027-07-12。

### 真实系统链验收记录（2026-07-28）

- 输入项目为“泛血管全栈数智基座与智能体项目”（招案2026-1952）；系统从中国政府采购网
  实时获取中标公告和公开招标 DOCX 原件，原件 SHA-256 为
  `d9f2e2e3acd15ccc03f9d9072c5fc5a55ba93b058b1539c76c3d86da2eb0e0b2`。
- Run `019fa6f0-f69f-701d-bff4-1eec4a9da397` 通过 REST、Artifact Gateway、PostgreSQL、
  Temporal、外部 `DeepSeek-V4-Flash`、Agent Worker 和 Tool Worker 完成，Temporal 状态
  `COMPLETED`，业务状态 `SUCCEEDED`。
- 三次模型调用合计 44,104 tokens；11 个 Tool effect 全部 `SUCCEEDED`，88 条 Outbox
  事件全部 `DELIVERED`。两个人工审批均确认阻断，未覆盖硬门禁。
- 结果为 `BLOCK`、风险等级 D、政府采购禁入硬门禁；生成 8 条条款差异
  （4 `BLOCKER`、3 `HIGH`、1 `MEDIUM`），每条均有冻结证据引用。由于没有真实 ERP/SRM
  履约记录，绩效明确输出 `INSUFFICIENT_DATA`，不伪造评分。
- 系统生成 1 个不可变快照、2 个预警、JSON/PDF 各 1 份，并将 CRITICAL 工单按
  `OPEN → IN_PROGRESS → CLOSED` 闭环，处置结论为 `CONFIRM_BLOCK`。
- 完整证据保存在
  `output/procurement-supplier-risk-real-chain/real-chain-20260728T041707Z-ae86ed5f5c.json`，
  PDF 已完成 A4 渲染和目视检查。

证据边界：公开页面未发布供应商完整投标原件，也没有已签合同和企业内部绩效数据。本次
分别使用中标公告逐项摘录、招标文件内待签合同模板，并在输入和结果中显式标注限制，因此
验收证明的是公开资料条件下的真实系统闭环，不代表完整采购档案或生产资格。

## 17. 验收标准

- Given 四类真实文档，When 发起评估，Then 每个差异包含四方血缘、级别和冻结证据。
- Given 真实 CCGP 信用代码，When 刷新，Then 保存真实记录号、URL、时点和响应哈希。
- Given 有效且精确身份的政府采购禁入，When 风险决策，Then 输出 `BLOCK`、硬门禁和 Alert。
- Given 同名但代码不符记录，When 采集，Then 不计分且进入人工复核。
- Given 3 个以上真实订单且覆盖率不少于 60%，When 计算，Then 输出五维绩效分和来源引用。
- Given Provider 超时，When 重试耗尽，Then 来源为 `FAILED`，不得出现伪造观察。
- Given 同一幂等键和请求，When 重放，Then 返回同一监控/工单；不同请求复用该键被拒绝。
- Given Alert，When 创建、开始并关闭工单，Then 状态合法且动作历史不可变。
- Given 后续刷新，When 风险或决策变化，Then 新快照显示变化；旧快照禁止更新/删除。
- Given REST 与 MCP 相同操作，Then 二者调用同一应用服务并返回一致业务投影。
- Given 错误租户，When 读取监控，Then 返回不可见/404。
- Given 完成运行，Then 可查看 Agent/Tool 过程、文档/来源依据、规则/模型版本、结果哈希、
  PDF、Finding、Outbox 和 Audit。

## 18. 暂不实现内容

- 自动替代采购审批、法律意见或监管认定；
- 未授权商业数据库和绕验证码网页采集；
- 自动将供应商写入外部黑名单；
- 复杂股权穿透、集团关联图谱和跨境制裁筛查；
- 生产级高可用、容量、灾备、mTLS 和多区域资格。

这些内容不影响 Demo 的最小闭环，但生产上线前仍需相应资格验证。

## 19. 风险说明

| 风险 | 缓解 |
|---|---|
| 公共页面结构变化 | 独立适配器、响应哈希、显式失败和契约测试 |
| 企业身份误匹配 | 信用代码精确匹配；名称命中只复核 |
| 模型遗漏/幻觉 | 冻结证据、Schema、独立复核 Agent、确定性最终规则 |
| 供应商绩效样本偏差 | 最少样本和覆盖率门槛，不足则不评分 |
| 商业数据授权不清 | 只接客户授权 Provider，凭据使用 Vault |
| 误阻断业务 | 展示规则和证据，条款差异可审批；硬门禁由人工确认适用性 |
| 演示外部源不稳定 | 使用已核验信用代码；失败路径作为正式验收项 |
| 本地证据被误解为生产资格 | 开发计划明确 `IMPLEMENTED / LOCAL` 和未关闭门禁 |
