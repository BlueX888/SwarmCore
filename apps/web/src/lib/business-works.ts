export type BusinessWorkCategory = "foundation" | "business" | "governance";

export const BUSINESS_WORK_QUERY_STALE_TIME = 30_000;
export const BUSINESS_WORK_QUERY_GC_TIME = 5 * 60_000;
export const BUSINESS_WORK_RUN_REFRESH_INTERVAL = 5_000;

export interface BusinessWorkFunction {
  name: string;
  description: string;
}

export interface BusinessWorkDefinition {
  key: string;
  name: string;
  shortName: string;
  category: BusinessWorkCategory;
  summary: string;
  functions: BusinessWorkFunction[];
}

export const BUSINESS_WORK_CATEGORIES: Array<{ value: "all" | BusinessWorkCategory; label: string }> = [
  { value: "all", label: "全部" },
  { value: "foundation", label: "基础能力" },
  { value: "business", label: "业务处理" },
  { value: "governance", label: "调度治理" },
];

export const BUSINESS_WORKS: BusinessWorkDefinition[] = [
  {
    key: "ai-foundation-quality",
    name: "基础 AI 能力集成与质量评测",
    shortName: "AI 基础与评测",
    category: "foundation",
    summary: "统一接入基础 AI 能力，并用样本、规则、置信度和人工复核建立质量闭环。",
    functions: [
      { name: "基础能力接入", description: "封装 LLM、Embedding、Vision、OCR、NLP、文档解析和结构化抽取。" },
      { name: "检索与问答", description: "提供向量检索、知识库索引和带证据的知识问答能力。" },
      { name: "规则与提示词", description: "版本化管理规则、Prompt、输出 Schema 和任务参数。" },
      { name: "置信度校准", description: "基于样本指标校准置信度，设置自动通过、降级和拦截阈值。" },
      { name: "人工复核", description: "对低置信度、证据不足和高风险结果发起人工确认。" },
      { name: "样本评测", description: "管理评测样本、指标、基线、回归结果和质量变化。" },
    ],
  },
  {
    key: "document-structuring",
    name: "文件结构化智能体",
    shortName: "文件结构化",
    category: "foundation",
    summary: "把多格式、大体量文件转换为可检索、可追溯、可人工确认的结构化数据。",
    functions: [
      { name: "格式自适应识别", description: "识别文件类型、编码、版式和处理路径。" },
      { name: "ODF 与办公文档解析", description: "解析 ODF、PDF、Word、Excel 等常见文档格式。" },
      { name: "大文件处理", description: "按页或分片并行处理，支持断点、重试和结果合并。" },
      { name: "OCR 与 NLP 抽取", description: "提取文字、实体、字段、关系及其原文证据。" },
      { name: "切片与表格提取", description: "生成语义切片，恢复表格结构并保留页码和坐标。" },
      { name: "自动整理与确认", description: "按业务 Schema 整理结果，并把疑点提交人工确认。" },
    ],
  },
  {
    key: "document-integrity",
    name: "文件完整性校验智能体",
    shortName: "文件完整性校验",
    category: "business",
    summary: "根据合同类型和资料规则检查文件是否齐全、有效、一致并可追踪。",
    functions: [
      { name: "资料清单匹配", description: "按合同类型、阶段和项目规则匹配应提交资料清单。" },
      { name: "多维完整性检查", description: "检查缺失、版本、签章、日期、附件和跨文件关联。" },
      { name: "缺失预警追踪", description: "形成缺失项、责任人、期限、提醒和闭环状态。" },
      { name: "规则可视化配置", description: "配置清单、条件、阈值、例外和人工复核要求。" },
      { name: "校验报告", description: "输出结论、缺失明细、证据引用和整改建议。" },
    ],
  },
  {
    key: "performance-plan-collection",
    name: "履约计划与执行采集智能体",
    shortName: "履约计划与采集",
    category: "business",
    summary: "从合同提取履约计划，并持续采集执行证据、里程碑状态和变更历史。",
    functions: [
      { name: "合同义务提取", description: "提取工期、交付、付款、服务标准和验收要求。" },
      { name: "里程碑与甘特图", description: "生成里程碑、依赖关系、计划日期和甘特视图。" },
      { name: "执行资料采集", description: "采集验收单、发货单、到货单、付款凭证和会议纪要。" },
      { name: "状态更新", description: "把执行证据关联至义务和里程碑并更新完成状态。" },
      { name: "变更历史", description: "记录计划调整、合同变更、责任主体和版本差异。" },
    ],
  },
  {
    key: "invoice-assurance",
    name: "发票一致性校验智能体",
    shortName: "发票一致性校验",
    category: "business",
    summary: "识别发票事实，并与合同、订单、履约和付款条件执行一致性及合规检查。",
    functions: [
      { name: "发票信息识别", description: "提取购买方、销售方、税号、金额、税率、品项和日期。" },
      { name: "多维一致性校验", description: "与合同、订单、收货、验收和付款计划进行交叉核验。" },
      { name: "合规性检查", description: "检查票面规范、重复发票、异常税率和关键字段风险。" },
      { name: "付款前置条件", description: "判断验收、交付、审批和资料完整性是否满足付款条件。" },
      { name: "报告与风险预警", description: "输出差异证据、风险等级、处置建议和校验报告。" },
    ],
  },
  {
    key: "deviation-analysis",
    name: "偏差分析智能体",
    shortName: "偏差分析",
    category: "business",
    summary: "对计划与实际执行进行时间、内容和成本偏差计算，并解释原因和趋势。",
    functions: [
      { name: "时间偏差", description: "计算计划与实际节点的提前、延迟和关键路径影响。" },
      { name: "内容偏差", description: "比对约定范围、交付内容、质量要求和实际完成情况。" },
      { name: "成本偏差", description: "分析合同金额、变更、支付和实际成本之间的差异。" },
      { name: "AI 根因分析", description: "结合证据生成结构化根因、影响和纠正建议。" },
      { name: "趋势与责任归属", description: "展示偏差趋势并记录责任主体、确认意见和处理状态。" },
    ],
  },
  {
    key: "report-generation",
    name: "报告生成智能体",
    shortName: "报告生成",
    category: "business",
    summary: "聚合文件、履约、偏差、发票和风险事实，生成可追溯的后评价报告。",
    functions: [
      { name: "多源结果聚合", description: "汇总结构化事实、规则结论、风险、问题和证据。" },
      { name: "七维评价", description: "按七大评价维度计算指标、分值、结论和改进项。" },
      { name: "AI 报告叙述", description: "基于已确认事实生成摘要、分析、建议和管理层结论。" },
      { name: "模板与版本", description: "管理报告模板、章节、样式、口径和版本。" },
      { name: "多格式输出", description: "输出结构化 JSON、在线预览和 PDF 等正式报告。" },
    ],
  },
  {
    key: "contract-post-evaluation",
    name: "合同后评价",
    shortName: "合同后评价",
    category: "business",
    summary: "围绕合同履约全过程聚合资料、履约、偏差、发票与风险事实，完成七维评价并生成可追溯报告。",
    functions: [
      { name: "资料与履约采集", description: "匹配合同、履约、偏差、发票和供应商等业务资料。" },
      { name: "七维评价", description: "按七大评价维度计算指标、分值、结论和改进项。" },
      { name: "风险与偏差分析", description: "识别履约偏差、发票差异和供应商风险关注项。" },
      { name: "综合结论", description: "输出总分、等级、风险等级和是否需要复核。" },
      { name: "报告与证据", description: "生成可追溯 JSON/PDF 报告，并冻结资料与决策快照。" },
    ],
  },
  {
    key: "swarm-calibration",
    name: "GitHub 工程问题调度校准智能体",
    shortName: "工程问题调度校准",
    category: "governance",
    summary: "基于冻结的公开 GitHub Issue、讨论、合并提交与沙箱验证，校准工程问题诊断的调度、降级与切换。",
    functions: [
      { name: "任务编排", description: "定义任务依赖、并行关系、输入输出和人工等待节点。" },
      { name: "智能体数据流转", description: "校验上游输出 Schema，向下游传递冻结数据和证据。" },
      { name: "结果质量校验", description: "检查结构、证据、置信度、规则结果和交叉一致性。" },
      { name: "备用智能体切换", description: "按策略建议重试、降级或切换备用 Agent 与模型。" },
      { name: "执行日志与监控", description: "查看运行状态、任务耗时、异常、成本和完整链路日志。" },
    ],
  },
  {
    key: "procurement-supplier-risk",
    name: "招采一致性与供应商风控智能体",
    shortName: "招采与供应商风控",
    category: "business",
    summary: "比对招投标与合同条款，结合多源风险和绩效数据持续识别供应商风险。",
    functions: [
      { name: "招采合同深度比对", description: "对招标文件、投标文件、中标结果和合同条款进行语义比对。" },
      { name: "分级差异清单", description: "按影响和风险输出新增、缺失、冲突及弱化条款。" },
      { name: "多源风险数据", description: "接入工商、司法、舆情、制裁和内部履约等风险数据。" },
      { name: "黑名单预警", description: "实时检查黑名单、关联方和高风险状态并触发预警。" },
      { name: "绩效与风控工单", description: "评估供应商绩效，形成责任明确、可跟踪的风控工单。" },
      { name: "历史变化追溯", description: "保留风险事实、评分、处置和供应商状态的版本历史。" },
    ],
  },
];

export const DOCUMENT_CATEGORY_LABELS: Record<string, string> = {
  CONTRACT: "合同文件",
  PERFORMANCE: "履约资料",
  ACCEPTANCE: "验收资料",
  DEVIATION: "偏差资料",
  INVOICE: "发票资料",
  PAYMENT: "付款资料",
  RISK: "风险资料",
  SUPPLIER: "供应商资料",
  PROCUREMENT: "招采资料",
  TENDER_DOCUMENT: "招标/采购文件",
  WINNING_BID: "中标投标/响应文件",
  AWARD_NOTICE: "中标/成交通知书",
  MASTER_CONTRACT: "待签或已签合同",
  PROCUREMENT_CHANGE: "澄清、变更和补充协议",
  SUPPLIER_PERFORMANCE: "供应商履约绩效资料",
  SUPPLEMENTAL_FACTS: "补充结构化事实",
  REPORT: "报告与成果",
  SCOPE_BASELINE: "范围基线",
  SCHEDULE_BASELINE: "进度基线",
  COST_BASELINE: "成本基线",
  PROGRESS_ACTUAL: "实际进度",
  DELIVERY_ACCEPTANCE: "交付与验收",
  COST_ACTUAL: "实际成本",
  APPROVED_CHANGE: "批准变更",
  CAUSE_EVIDENCE: "原因证据",
  RESPONSIBILITY_BASIS: "责任依据",
  INVOICE_ORIGINAL: "发票原件",
  CONTRACT_ORDER: "合同/订单",
  RECEIPT_ACCEPTANCE: "收货/验收",
  SUPPLIER_MASTER: "供应商主数据",
  AP_LEDGER: "应付台账",
  BUDGET_PAYMENT_POLICY: "预算与付款政策",
  TAX_ACCOUNT_EXPORT: "税务数字账户导出",
  BANK_CHANGE_EVIDENCE: "账户变更证据",
};

export function getBusinessWork(key: string | undefined) {
  return BUSINESS_WORKS.find((work) => work.key === key);
}
