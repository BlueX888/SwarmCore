import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  Bot,
  BrainCircuit,
  CheckCircle2,
  CircleGauge,
  Database,
  ExternalLink,
  FileSearch,
  GitBranch,
  Network,
  Play,
  Settings2,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link } from "react-router";
import { api } from "@/api/client";
import type { BusinessWorkSnapshot, BusinessWorkStatus } from "@/api/types";
import { BusinessWorkPageHeader } from "@/components/business-works/business-work-page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspaceScope } from "@/lib/demo-scope";

const WORK_KEY = "ai-foundation-quality";

const DATA_SOURCES = [
  {
    name: "GitHub REST API",
    use: "可执行 Demo：Issue、讨论、关联 PR 与合并提交",
    update: "运行时实时获取并冻结内容哈希",
    href: "https://docs.github.com/en/rest/issues/issues",
  },
  {
    name: "SQuAD 2.0",
    use: "LLM、NLP、结构化抽取与有据问答样本",
    update: "固定版本评测集，CC BY-SA 4.0",
    href: "https://rajpurkar.github.io/SQuAD-explorer/",
  },
  {
    name: "XFUND",
    use: "中文表单的 Vision、OCR 与键值抽取样本",
    update: "v1.0 人工标注数据，非商业评测使用",
    href: "https://github.com/doc-analysis/XFUND",
  },
  {
    name: "BEIR",
    use: "Embedding、向量检索与重排效果评测",
    update: "固定版本公开检索基准",
    href: "https://github.com/beir-cellar/beir",
  },
  {
    name: "NIST AI RMF",
    use: "质量风险、人工监督与结果追溯控制依据",
    update: "实施时按发布版本冻结",
    href: "https://www.nist.gov/itl/ai-risk-management-framework",
  },
];

const PIPELINE = [
  { title: "真实输入", detail: "GitHub Issue URL、目标与可测试验收标准", icon: GitBranch },
  { title: "获取真实数据", detail: "读取 Issue、讨论、PR 和完整合并提交 SHA", icon: Database },
  { title: "智能体处理", detail: "主诊断 Agent 分析；失败时由 Runtime 切换备用 Agent", icon: Bot },
  { title: "工具执行", detail: "冻结证据、隔离验证、规则评分和报告生成", icon: Wrench },
  { title: "质量决策", detail: "Schema、来源、证据、沙箱和验收覆盖共同判定", icon: CircleGauge },
  { title: "结果与依据", detail: "展示结论、得分、时间线、引用、哈希和人工意见", icon: ShieldCheck },
];

const MODEL_ROLES = [
  ["生成与推理模型", "LLM 负责诊断、问答和结构化输出；通过项目模型路由替换 Provider。"],
  ["向量与重排模型", "Embedding / Reranker 服务检索召回与证据排序，按 BEIR 样本回归。"],
  ["视觉与 OCR 模型", "Vision / OCR 处理扫描件和版式，按 XFUND 字段与坐标评测。"],
  ["质量监督模型", "Judge 只给一致性建议；最终阈值与路由由确定性 Tool / Runtime 决定。"],
];

const QUALITY_RULES = [
  ["Schema 合法", "20 分", "输出不符合版本化 Schema 时直接转复核"],
  ["来源完整", "15 分", "Issue、讨论、PR 三类证据缺失即拦截"],
  ["证据覆盖", "25 分", "关键结论覆盖率低于 90% 时转复核"],
  ["证据一致", "15 分", "监督判断存在冲突时不得自动通过"],
  ["运行验证", "15 分", "沙箱未通过时总分封顶 79"],
  ["验收映射", "10 分", "每条验收标准必须映射结论和证据"],
];

export function AiFoundationQualityPage() {
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const workQuery = useQuery({
    queryKey: ["business-work", tenantId, projectId, WORK_KEY],
    queryFn: () => api.getBusinessWork(tenantId, projectId, WORK_KEY),
  });
  const worksQuery = useQuery({
    queryKey: ["business-works", tenantId, projectId],
    queryFn: () => api.listBusinessWorks(tenantId, projectId),
  });
  const work = workQuery.data;
  const linkedWorks = useMemo(() => {
    const index = new Map((worksQuery.data?.items ?? []).map((item) => [item.workKey, item]));
    return {
      documents: index.get("document-structuring"),
      reports: index.get("report-generation"),
      calibration: index.get("swarm-calibration"),
    };
  }, [worksQuery.data?.items]);

  if (workQuery.isPending) {
    return <div className="space-y-4"><Skeleton className="h-44" /><Skeleton className="h-80" /></div>;
  }

  const runnable = work?.status === "runnable";
  const status = statusMeta(work?.status);
  const agents = work?.agents.length ?? 0;
  const tools = work?.tools.length ?? 0;
  const models = work?.models.length ?? 0;

  return <div className="min-w-0 space-y-5">
    <BusinessWorkPageHeader
      backTo={`${workspacePath}/overview`}
      icon={BrainCircuit}
      meta={<><Badge color={status.color}>{status.label}</Badge><span className="text-xs text-gray-400">基础能力 · 质量平面</span></>}
      title="基础 AI 能力集成与质量评测"
      description="统一接入 LLM、Embedding、Vision、OCR、NLP、文档解析、结构化抽取、向量检索与知识库问答，并用真实样本建立可追溯质量闭环。"
      summary={<dl className="grid gap-3 sm:grid-cols-3" aria-label="质量平面摘要">
        <Summary label="基础能力" value="9 类" />
        <Summary label="质量门" value="85 分 / 90% 证据" />
        <Summary label="当前绑定" value={`${agents} Agent · ${tools} Tool · ${models} Model`} />
      </dl>}
      actions={<>
        {runnable
          ? <Button asChild className="w-full justify-center"><Link to={`${workspacePath}/business-works/${WORK_KEY}/workbench`}><Play />运行真实样本评测</Link></Button>
          : <Button className="w-full justify-center" disabled><Play />质量运行尚未就绪</Button>}
        <Button asChild variant="outline" size="sm" className="w-full justify-center"><Link to={`${workspacePath}/business-works/${WORK_KEY}/settings`}><Settings2 />配置模型与策略</Link></Button>
      </>}
    />

    {workQuery.isError ? <p role="alert" className="rounded-xl border border-warning-200 bg-warning-50 px-4 py-3 text-sm text-warning-800 dark:border-warning-500/20 dark:bg-warning-500/10 dark:text-warning-300">
      无法读取项目运行状态：{workQuery.error.message}。下方仍展示已登记的集成与评测方案。
    </p> : null}

    <section aria-labelledby="acceptance-loop-title">
      <Card>
        <CardContent className="p-5">
          <SectionTitle
            id="acceptance-loop-title"
            icon={Sparkles}
            title="可验收的最小完整闭环"
            description="当前 Demo 使用公开 GitHub 工程事实，不用静态结果代替工具调用。"
            badge="真实数据"
          />
          <ol className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {PIPELINE.map((item, index) => {
              const Icon = item.icon;
              return <li key={item.title} className="rounded-xl border border-gray-100 bg-gray-50/70 p-4 dark:border-gray-800 dark:bg-gray-900/50">
                <div className="flex items-center gap-3">
                  <span className="grid size-9 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400"><Icon className="size-4" /></span>
                  <div><span className="text-[11px] font-semibold text-gray-400">STEP {index + 1}</span><h3 className="text-sm font-semibold text-gray-900 dark:text-white">{item.title}</h3></div>
                </div>
                <p className="mt-3 text-xs leading-5 text-gray-500">{item.detail}</p>
              </li>;
            })}
          </ol>
        </CardContent>
      </Card>
    </section>

    <section className="grid gap-4 xl:grid-cols-2" aria-label="基础能力与运行组件">
      <Card>
        <CardContent className="p-5">
          <SectionTitle icon={Network} title="基础能力接入矩阵" description="每类能力独立路由、独立评测，可替换但不改变业务契约。" badge="9 类" />
          <div className="mt-4 space-y-3">
            <CapabilityRow title="LLM · NLP · 结构化抽取" detail="生成、分类、实体关系与 JSON Schema 输出" status={work} />
            <CapabilityRow title="Vision · OCR · 文档解析" detail="扫描件、版式、表格、字段与原文坐标" status={linkedWorks.documents} />
            <CapabilityRow title="Embedding · 向量检索 · 知识问答" detail="切片、召回、重排与带引用回答" status={linkedWorks.reports} />
            <CapabilityRow title="规则 · Prompt · 置信度 · 人工复核" detail="版本冻结、确定性质量门和反馈回流" status={linkedWorks.calibration ?? work} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5">
          <SectionTitle icon={Bot} title="模型与智能体配置" description="优先单职责 Agent；Runtime 对路由、阈值和人工等待拥有最终决定权。" badge={`${agents || 4} Agent`} />
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {MODEL_ROLES.map(([title, detail]) => <div key={title} className="rounded-xl border border-gray-100 p-3 dark:border-gray-800">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h3>
              <p className="mt-1 text-xs leading-5 text-gray-500">{detail}</p>
            </div>)}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge color="primary">Primary Diagnostician</Badge>
            <Badge color="warning">Standby Diagnostician</Badge>
            <Badge color="success">Quality Supervisor</Badge>
            <Badge color="neutral">Scheduler</Badge>
          </div>
        </CardContent>
      </Card>
    </section>

    <section className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]" aria-label="质量规则与运行策略">
      <Card>
        <CardContent className="p-5">
          <SectionTitle icon={CircleGauge} title="规则、置信度与人工复核" description="置信度来自样本与证据校准，不采信模型自报概率。" badge="PASS ≥ 85" />
          <div className="mt-4 overflow-hidden rounded-xl border border-gray-100 dark:border-gray-800">
            {QUALITY_RULES.map(([name, score, rule]) => <div key={name} className="grid gap-1 border-b border-gray-100 px-3 py-2.5 last:border-b-0 sm:grid-cols-[7rem_4rem_1fr] dark:border-gray-800">
              <span className="text-sm font-semibold text-gray-800 dark:text-gray-100">{name}</span>
              <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">{score}</span>
              <span className="text-xs leading-5 text-gray-500">{rule}</span>
            </div>)}
          </div>
          <p className="mt-3 rounded-xl bg-warning-50 px-3 py-2.5 text-xs leading-5 text-warning-800 dark:bg-warning-500/10 dark:text-warning-300">
            自动修订一次后仍未通过，进入人工复核；复核人可批准降级接受、提交修正或拒绝，意见随运行留痕。
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5">
          <SectionTitle icon={Wrench} title="工具与运行策略" description="网络、模型、数据库和文件 I/O 均在 Tool / Activity 中执行。" badge={`${tools || 11} Tool`} />
          <ul className="mt-4 space-y-2 text-xs leading-5 text-gray-600 dark:text-gray-300">
            {[
              "GitHub Tool：读取 Issue、讨论、PR 与合并证据；只读、超时重试。",
              "Evidence Tool：按来源 URL、获取时间和 SHA-256 冻结证据清单。",
              "Sandbox Tool：在完整合并提交上执行隔离测试，失败不得自动通过。",
              "Quality Tool：确定性计算六项指标，并路由 PASS / REVIEW_REQUIRED。",
              "Report Tool：输出 JSON / PDF、引用索引、模型与 Prompt 版本。",
              "Temporal：耐久状态、重试、取消、预算、主备切换和人工等待。",
            ].map((item) => <li key={item} className="flex gap-2 rounded-xl bg-gray-50 px-3 py-2.5 dark:bg-gray-900/50"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success-500" /><span>{item}</span></li>)}
          </ul>
        </CardContent>
      </Card>
    </section>

    <section aria-labelledby="data-sources-title">
      <Card>
        <CardContent className="p-5">
          <SectionTitle id="data-sources-title" icon={FileSearch} title="真实资料与评测样本" description="Demo 运行源与离线回归集分开管理；访问失败时保留失败状态，不伪造替代结果。" badge="5 个来源" />
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {DATA_SOURCES.map((source) => <a key={source.name} href={source.href} target="_blank" rel="noreferrer" className="group rounded-xl border border-gray-100 p-4 transition hover:border-brand-200 hover:bg-brand-50/30 dark:border-gray-800 dark:hover:border-brand-500/30 dark:hover:bg-brand-500/5">
              <div className="flex items-center justify-between gap-3"><h3 className="text-sm font-semibold text-gray-900 dark:text-white">{source.name}</h3><ExternalLink className="size-4 text-gray-400 transition group-hover:text-brand-500" /></div>
              <p className="mt-2 text-xs leading-5 text-gray-600 dark:text-gray-300">{source.use}</p>
              <p className="mt-1 text-[11px] text-gray-400">{source.update}</p>
            </a>)}
          </div>
        </CardContent>
      </Card>
    </section>

    <div className="flex flex-wrap justify-end gap-2">
      <Button asChild variant="outline"><Link to={`${workspacePath}/business-works/document-structuring`}>查看文档能力<ArrowRight /></Link></Button>
      <Button asChild variant="outline"><Link to={`${workspacePath}/business-works/swarm-calibration`}>查看调度校准<ArrowRight /></Link></Button>
      {runnable ? <Button asChild><Link to={`${workspacePath}/business-works/${WORK_KEY}/workbench`}><Play />开始真实评测</Link></Button> : null}
    </div>
  </div>;
}

function Summary({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-[11px] font-medium uppercase tracking-wide text-gray-400">{label}</dt><dd className="mt-0.5 text-sm font-semibold text-gray-900 dark:text-white">{value}</dd></div>;
}

function SectionTitle({ id, icon: Icon, title, description, badge }: { id?: string; icon: LucideIcon; title: string; description: string; badge: string }) {
  return <div className="flex flex-wrap items-start justify-between gap-3">
    <div className="flex items-start gap-3">
      <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400"><Icon className="size-4" /></span>
      <div><h2 id={id} className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h2><p className="mt-1 text-xs leading-5 text-gray-500">{description}</p></div>
    </div>
    <Badge color="primary">{badge}</Badge>
  </div>;
}

function CapabilityRow({ title, detail, status }: { title: string; detail: string; status?: BusinessWorkSnapshot }) {
  const meta = statusMeta(status?.status);
  return <div className="flex items-center justify-between gap-3 rounded-xl border border-gray-100 px-3 py-3 dark:border-gray-800">
    <div className="min-w-0"><h3 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h3><p className="mt-0.5 text-xs text-gray-500">{detail}</p></div>
    <Badge color={meta.color}>{meta.label}</Badge>
  </div>;
}

function statusMeta(status?: BusinessWorkStatus): { label: string; color: "neutral" | "success" | "warning" | "error" } {
  if (status === "runnable") return { label: "可运行", color: "success" };
  if (status === "not_configured" || status === "incomplete") return { label: "待配置", color: "warning" };
  if (status === "unavailable") return { label: "不可用", color: "error" };
  return { label: "方案已登记", color: "neutral" };
}
