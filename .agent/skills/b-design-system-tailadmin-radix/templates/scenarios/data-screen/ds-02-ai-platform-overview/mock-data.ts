export const ds02Mock = {
  totalTokens: "79,959k",
  heroTitle: "智能知识平台",
  heroSubtitle: "AI 推理与知识库运营总览",
  orbitItems: [
    { label: "总会话数", value: "12,846", unit: "次" },
    { label: "活跃应用", value: 18, unit: "个" },
    { label: "今日 Token", value: "2.4M" },
    { label: "文档总数", value: "3,562", unit: "篇" },
    { label: "模型调用", value: "8,920", unit: "次" },
    { label: "平均响应", value: "1.2", unit: "秒" },
  ],
  sessionSummary: [
    { label: "今日会话", value: "1,284" },
    { label: "7 日峰值", value: "2,156" },
    { label: "平均时长", value: "4.6 分钟" },
    { label: "满意度", value: "96.2%" },
  ],
  applications: [
    { name: "客服问答", value: 32 },
    { name: "知识检索", value: 28 },
    { name: "文档摘要", value: 18 },
    { name: "代码助手", value: 12 },
    { name: "其他", value: 10 },
  ],
  tokenByApp: {
    categories: ["客服问答", "知识检索", "文档摘要", "代码助手"],
    series: [
      { name: "输入 Token", data: [4200, 3800, 2100, 1600] },
      { name: "输出 Token", data: [2800, 2400, 1500, 1100] },
    ],
  },
  wordCloud: [
    { text: "大模型", weight: 100 },
    { text: "知识库", weight: 88 },
    { text: "RAG", weight: 76 },
    { text: "向量检索", weight: 72 },
    { text: "Prompt", weight: 65 },
    { text: "微调", weight: 58 },
    { text: "推理", weight: 52 },
    { text: "评测", weight: 48 },
    { text: "标注", weight: 42 },
    { text: "安全", weight: 38 },
  ],
  documentDistribution: [
    { name: "技术文档", value: 38 },
    { name: "产品手册", value: 26 },
    { name: "政策法规", value: 18 },
    { name: "FAQ", value: 12 },
    { name: "其他", value: 6 },
  ],
  modelTokens: {
    categories: ["GPT-4o", "Claude", "Qwen", "DeepSeek"],
    series: [{ name: "Token 消耗（千）", data: [32, 24, 18, 12] }],
  },
  sessionTrend: {
    categories: ["06-22", "06-23", "06-24", "06-25", "06-26", "06-27", "06-28"],
    series: [
      { name: "会话量", data: [1420, 1580, 1650, 1720, 1890, 2010, 2156] },
      { name: "Token 消耗（千）", data: [680, 720, 750, 810, 860, 920, 980] },
    ],
  },
} as const;

export const {
  totalTokens: ds02TotalTokens,
  heroTitle: ds02HeroTitle,
  heroSubtitle: ds02HeroSubtitle,
  orbitItems: ds02OrbitItems,
  sessionSummary: ds02SessionSummary,
  applications: ds02Applications,
  tokenByApp: ds02TokenByApp,
  wordCloud: ds02WordCloud,
  documentDistribution: ds02DocumentDistribution,
  modelTokens: ds02ModelTokens,
  sessionTrend: ds02SessionTrend,
} = ds02Mock;
