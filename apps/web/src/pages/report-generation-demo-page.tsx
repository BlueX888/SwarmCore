import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  CheckCircle2,
  Circle,
  ClipboardCheck,
  Download,
  FileCheck2,
  FileClock,
  FileOutput,
  Files,
  LoaderCircle,
  Printer,
  ReceiptText,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  WalletCards,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useWorkspaceScope } from "@/lib/demo-scope";
import { cn } from "@/lib/utils";

type DemoStage = "prepare" | "generating" | "report";

interface SourceGroup {
  name: string;
  count: number;
  coverage: "较完整" | "部分" | "测试样例";
  description: string;
  icon: LucideIcon;
}

interface DimensionResult {
  code: string;
  name: string;
  weight: number;
  score: number;
  summary: string;
  metric: string;
  evidence: string[];
}

const SOURCE_GROUPS: SourceGroup[] = [
  { name: "采购与合同", count: 7, coverage: "较完整", description: "采购公告、成交公告、合同及供应商承诺", icon: FileCheck2 },
  { name: "履约进度", count: 4, coverage: "部分", description: "月度计划、验收表、质保与移交资料", icon: FileClock },
  { name: "验收与质量", count: 7, coverage: "较完整", description: "验收报告、验收方案及质量检查规范", icon: ClipboardCheck },
  { name: "成本与付款", count: 2, coverage: "部分", description: "支付申请与财政绩效评价材料", icon: WalletCards },
  { name: "发票", count: 4, coverage: "测试样例", description: "官方票样、红字及作废规则资料", icon: ReceiptText },
  { name: "偏差与变更", count: 2, coverage: "较完整", description: "合同变更协议及工程变更单模板", icon: TrendingUp },
  { name: "风险与问题", count: 5, coverage: "较完整", description: "投诉、处罚、无投诉说明及廉政协议", icon: ShieldAlert },
];

const GENERATION_STEPS = [
  "识别 32 份公开文件并校验分类",
  "关联合同、履约、验收与变更证据",
  "执行七维确定性评分与风险检查",
  "生成摘要、关注项和可追溯报告",
];

const DIMENSIONS: DimensionResult[] = [
  {
    code: "DOCUMENT_COMPLETENESS",
    name: "文件完整性",
    weight: 10,
    score: 87.5,
    summary: "8 类必备资料中 7 类有效，真实交易发票原件缺失。",
    metric: "7 / 8 类有效",
    evidence: ["标段4合同", "成交公告", "履约验收报告"],
  },
  {
    code: "DELIVERY_TIMELINESS",
    name: "进度履约",
    weight: 20,
    score: 87.5,
    summary: "4 项到期义务中 3 项按期完成，1 项培训义务延期完成。",
    metric: "3 项按期 · 1 项延期",
    evidence: ["月度采购计划", "服务项目完成验收表"],
  },
  {
    code: "DELIVERY_QUALITY",
    name: "质量履约",
    weight: 15,
    score: 92.5,
    summary: "3 项交付物验收通过，1 项附条件通过，未发现拒收记录。",
    metric: "3 项通过 · 1 项附条件",
    evidence: ["履约验收报告", "质量监督检查指南"],
  },
  {
    code: "COST_CONTROL",
    name: "成本控制",
    weight: 15,
    score: 93.33,
    summary: "演示结构化记录显示实际成本较合同金额超支 1.33%。",
    metric: "超支 ¥12,000",
    evidence: ["项目资金支付申请表", "演示成本台账"],
  },
  {
    code: "INVOICE_COMPLIANCE",
    name: "发票合规",
    weight: 15,
    score: 88.89,
    summary: "3 条演示发票记录中 1 条缺少验收匹配，需付款前补核。",
    metric: "1 条匹配异常",
    evidence: ["数电票官方样式", "演示发票台账"],
  },
  {
    code: "DEVIATION_GOVERNANCE",
    name: "偏差治理",
    weight: 10,
    score: 68.1,
    summary: "3 项偏差已关闭 2 项，培训进度偏差仍处于处理中。",
    metric: "2 / 3 项已关闭",
    evidence: ["合同变更协议", "演示偏差台账"],
  },
  {
    code: "RISK_GOVERNANCE",
    name: "风险治理",
    weight: 15,
    score: 68.57,
    summary: "3 项风险已关闭 2 项，1 项整改措施逾期，需持续跟踪。",
    metric: "1 项措施逾期",
    evidence: ["供应商材料争议决定书", "演示风险台账"],
  },
];

const REPORT_RESULT = {
  schemaVersion: "schema://contract/post-evaluation-result@1",
  evaluationPeriod: { start: "2026-01-01", end: "2026-06-30" },
  contractId: "DEMO-CPE-2026-001",
  overallScore: 84.55,
  grade: "良好",
  riskLevel: "LOW",
  passed: true,
  reviewRequired: false,
  executiveSummary:
    "采购履约公开数据综合演示案例七维后评价得分84.55，等级良好，风险级别LOW；发现2项需关注事项。",
  dimensions: DIMENSIONS.map(({ code, name, weight, score, summary, evidence }) => ({
    code,
    name,
    weight,
    score,
    status: "EVALUATED",
    summary,
    evidenceRefs: evidence,
  })),
  findings: [
    {
      dimension: "DEVIATION_GOVERNANCE",
      severity: "MEDIUM",
      code: "DIMENSION_BELOW_TARGET",
      title: "偏差治理需关注",
      detail: "培训进度偏差尚未关闭，偏差治理得分低于80分关注线。",
      evidenceRefs: ["合同变更协议", "演示偏差台账"],
    },
    {
      dimension: "RISK_GOVERNANCE",
      severity: "MEDIUM",
      code: "DIMENSION_BELOW_TARGET",
      title: "风险治理需关注",
      detail: "整改跟踪措施已逾期，风险治理得分低于80分关注线。",
      evidenceRefs: ["供应商材料争议决定书", "演示风险台账"],
    },
  ],
};

export function ReportGenerationDemoPage() {
  const { workspacePath } = useWorkspaceScope();
  const [stage, setStage] = useState<DemoStage>("prepare");
  const [generationStep, setGenerationStep] = useState(0);

  useEffect(() => {
    if (stage !== "generating") return;
    const timers = GENERATION_STEPS.map((_, index) => window.setTimeout(
      () => setGenerationStep(index + 1),
      350 + index * 350,
    ));
    const completion = window.setTimeout(() => setStage("report"), 1750);
    return () => {
      timers.forEach(window.clearTimeout);
      window.clearTimeout(completion);
    };
  }, [stage]);

  const startGeneration = () => {
    setGenerationStep(0);
    setStage("generating");
  };

  const reset = () => {
    setGenerationStep(0);
    setStage("prepare");
  };

  return (
    <div className="min-w-0 space-y-6">
      <header className="report-demo-hide-on-print">
        <Link
          to={`${workspacePath}/business-works/report-generation`}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-500 transition hover:text-gray-900 dark:hover:text-white"
        >
          <ArrowLeft className="size-4" />
          返回报告生成智能体
        </Link>
        <div className="mt-5 overflow-hidden rounded-[28px] border border-gray-200/80 bg-gray-950 text-white shadow-theme-card dark:border-gray-800">
          <div className="relative p-6 md:p-8">
            <div className="absolute -right-16 -top-20 size-64 rounded-full bg-brand-500/25 blur-3xl" />
            <div className="absolute bottom-0 right-1/3 size-36 rounded-full bg-success-500/10 blur-3xl" />
            <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge color="primary">最小 Demo</Badge>
                  <span className="text-xs text-gray-400">公开测试文件包 · 七维后评价</span>
                </div>
                <h1 className="mt-4 text-2xl font-semibold tracking-tight md:text-3xl">报告生成智能体</h1>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-300">
                  汇总合同、履约、验收、成本、发票、偏差和风险数据，一键生成带评分、关注项和证据引用的后评价报告。
                </p>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <HeroMetric value="32" label="公开文件" />
                <HeroMetric value="7" label="评价维度" />
                <HeroMetric value="1" label="报告版本" />
              </div>
            </div>
          </div>
        </div>
      </header>

      <DemoSteps stage={stage} />

      {stage === "prepare" ? <PreparationView onGenerate={startGeneration} /> : null}
      {stage === "generating" ? <GeneratingView activeStep={generationStep} /> : null}
      {stage === "report" ? <ReportView onReset={reset} /> : null}
    </div>
  );
}

function HeroMetric({ value, label }: { value: string; label: string }) {
  return (
    <div className="min-w-20 rounded-2xl border border-white/10 bg-white/[0.06] px-3 py-3 backdrop-blur">
      <p className="text-xl font-semibold">{value}</p>
      <p className="mt-0.5 text-[11px] text-gray-400">{label}</p>
    </div>
  );
}

function DemoSteps({ stage }: { stage: DemoStage }) {
  const current = stage === "prepare" ? 0 : stage === "generating" ? 1 : 2;
  return (
    <ol aria-label="演示进度" className="report-demo-hide-on-print grid gap-2 sm:grid-cols-3">
      {["准备数据", "智能分析", "查看报告"].map((label, index) => (
        <li
          key={label}
          aria-current={current === index ? "step" : undefined}
          className={cn(
            "flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm font-medium transition",
            current === index
              ? "border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-300"
              : current > index
                ? "border-success-200 bg-success-50 text-success-700 dark:border-success-500/20 dark:bg-success-500/10"
                : "border-gray-200 bg-white text-gray-400 dark:border-gray-800 dark:bg-gray-900",
          )}
        >
          <span className={cn(
            "grid size-7 place-items-center rounded-full text-xs font-semibold",
            current === index ? "bg-brand-500 text-white" : current > index ? "bg-success-500 text-white" : "bg-gray-100 text-gray-500 dark:bg-gray-800",
          )}>
            {current > index ? <Check className="size-4" /> : index + 1}
          </span>
          {label}
        </li>
      ))}
    </ol>
  );
}

function PreparationView({ onGenerate }: { onGenerate: () => void }) {
  return (
    <div className="space-y-5">
      <Card>
        <CardContent className="p-5 md:p-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="flex items-start gap-3">
              <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-success-50 text-success-600 dark:bg-success-500/10">
                <CheckCircle2 className="size-5" />
              </span>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="font-semibold text-gray-900 dark:text-white">公开测试文件已载入</h2>
                  <Badge color="success">可生成</Badge>
                </div>
                <p className="mt-1 text-sm text-gray-500">采购履约后评价智能体_公开测试文件包</p>
                <p className="mt-2 max-w-3xl text-xs leading-5 text-gray-400">
                  包含 31 份分类材料和 1 份综合模板。核心项目证据与跨项目规则样本会分别使用，避免错误合并。
                </p>
              </div>
            </div>
            <Button onClick={onGenerate} size="sm" className="shrink-0">
              <Sparkles />
              开始生成七维报告
            </Button>
          </div>
        </CardContent>
      </Card>

      <section aria-labelledby="demo-data-title">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 id="demo-data-title" className="text-lg font-semibold text-gray-900 dark:text-white">数据覆盖</h2>
            <p className="mt-1 text-sm text-gray-500">按后评价七大数据域归集文件。</p>
          </div>
          <span className="text-xs text-gray-400">共 31 份分类材料</span>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {SOURCE_GROUPS.map((group) => {
            const Icon = group.icon;
            return (
              <Card key={group.name} className="min-w-0">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10">
                      <Icon className="size-4.5" />
                    </span>
                    <Badge color={group.coverage === "较完整" ? "success" : group.coverage === "部分" ? "warning" : "neutral"}>
                      {group.coverage}
                    </Badge>
                  </div>
                  <div className="mt-3 flex items-baseline justify-between gap-3">
                    <h3 className="font-semibold text-gray-900 dark:text-white">{group.name}</h3>
                    <span className="text-sm font-semibold text-brand-600">{group.count} 份</span>
                  </div>
                  <p className="mt-1 text-xs leading-5 text-gray-500">{group.description}</p>
                </CardContent>
              </Card>
            );
          })}
          <Card className="border-dashed border-brand-200 bg-brand-50/40 dark:border-brand-500/20 dark:bg-brand-500/5">
            <CardContent className="flex h-full flex-col justify-center p-4">
              <div className="flex items-center gap-2">
                <Sparkles className="size-4 text-brand-500" />
                <h3 className="font-semibold text-gray-900 dark:text-white">演示补充记录</h3>
              </div>
              <p className="mt-2 text-xs leading-5 text-gray-500">
                补充成本、发票、偏差和风险结构化记录，用于完整走通七维评分。
              </p>
              <p className="mt-3 text-xs font-semibold text-brand-600">仅用于演示 · 不冒充公开原件</p>
            </CardContent>
          </Card>
        </div>
      </section>

      <div className="flex items-start gap-3 rounded-2xl border border-warning-200 bg-warning-50 p-4 text-warning-800 dark:border-warning-500/20 dark:bg-warning-500/10 dark:text-warning-300">
        <AlertTriangle className="mt-0.5 size-5 shrink-0" />
        <div>
          <p className="text-sm font-semibold">演示边界</p>
          <p className="mt-1 text-xs leading-5">
            公开文件包不是同一真实项目的完整业务档案；真实发票、银行流水和完整风险台账通常不公开。报告中的补充记录均有“演示”标识，结果仅用于验证系统功能。
          </p>
        </div>
      </div>
    </div>
  );
}

function GeneratingView({ activeStep }: { activeStep: number }) {
  return (
    <Card>
      <CardContent className="flex min-h-[430px] flex-col items-center justify-center p-6">
        <span className="relative grid size-20 place-items-center rounded-[28px] bg-brand-50 text-brand-600 dark:bg-brand-500/10">
          <LoaderCircle className="size-9 animate-spin" />
          <span className="absolute -right-1 -top-1 grid size-7 place-items-center rounded-full bg-gray-950 text-white">
            <Sparkles className="size-3.5" />
          </span>
        </span>
        <h2 className="mt-6 text-xl font-semibold text-gray-900 dark:text-white">正在生成后评价报告</h2>
        <p aria-live="polite" className="mt-2 text-sm text-gray-500">
          {activeStep < GENERATION_STEPS.length ? GENERATION_STEPS[activeStep] : "正在整理最终报告…"}
        </p>
        <ol className="mt-7 w-full max-w-xl space-y-2">
          {GENERATION_STEPS.map((label, index) => {
            const complete = activeStep > index;
            const active = activeStep === index;
            return (
              <li key={label} className={cn(
                "flex items-center gap-3 rounded-xl border px-4 py-3 text-sm",
                complete
                  ? "border-success-200 bg-success-50 text-success-700 dark:border-success-500/20 dark:bg-success-500/10"
                  : active
                    ? "border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-500/20 dark:bg-brand-500/10"
                    : "border-gray-200 text-gray-400 dark:border-gray-800",
              )}>
                {complete ? <CheckCircle2 className="size-4.5" /> : active ? <LoaderCircle className="size-4.5 animate-spin" /> : <Circle className="size-4.5" />}
                {label}
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}

function ReportView({ onReset }: { onReset: () => void }) {
  return (
    <article className="report-demo-print space-y-5">
      <div className="report-demo-hide-on-print flex flex-wrap justify-end gap-2">
        <Button variant="outline" size="sm" onClick={onReset}><RefreshCw />重新生成</Button>
        <Button variant="outline" size="sm" onClick={downloadReport}><Download />下载 JSON</Button>
        <Button size="sm" onClick={() => window.print()}><Printer />打印 / 保存 PDF</Button>
      </div>

      <Card className="overflow-hidden">
        <CardContent className="p-0">
          <div className="border-b border-gray-200 bg-gray-950 px-6 py-7 text-white dark:border-gray-800 md:px-8">
            <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-300">Contract post-evaluation</p>
                <h1 className="mt-2 text-2xl font-semibold">采购履约后评价报告</h1>
                <p className="mt-2 text-sm text-gray-400">公开数据综合演示案例 · DEMO-CPE-2026-001</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge color="success">已生成</Badge>
                <Badge color="primary">版本 1</Badge>
              </div>
            </div>
          </div>
          <div className="grid gap-6 p-6 md:grid-cols-[220px_1fr] md:p-8">
            <div className="flex flex-col items-center justify-center rounded-3xl bg-gray-50 p-5 text-center dark:bg-gray-800/60">
              <div
                aria-label="综合得分 84.55 分"
                className="grid size-36 place-items-center rounded-full"
                style={{ background: "conic-gradient(#465fff 0 84.55%, #e4e7ec 84.55% 100%)" }}
              >
                <div className="grid size-28 place-items-center rounded-full bg-white dark:bg-gray-900">
                  <div>
                    <p className="text-3xl font-semibold text-gray-900 dark:text-white">84.55</p>
                    <p className="text-xs text-gray-400">综合得分</p>
                  </div>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <Badge color="success">良好</Badge>
                <Badge color="success">低风险</Badge>
              </div>
            </div>
            <div className="flex flex-col justify-center">
              <div className="flex items-center gap-2">
                <FileOutput className="size-5 text-brand-500" />
                <h2 className="font-semibold text-gray-900 dark:text-white">管理层摘要</h2>
              </div>
              <p className="mt-3 text-sm leading-7 text-gray-600 dark:text-gray-300">
                本演示按照平台七维评价口径完成综合分析，总体履约表现良好。质量履约与成本控制表现稳定；偏差治理和风险治理低于 80 分关注线，建议优先关闭培训进度偏差，并补齐逾期整改措施的责任人和完成时限。
              </p>
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <ReportMetric label="评价期间" value="2026.01—2026.06" />
                <ReportMetric label="评价维度" value="7 / 7 已完成" />
                <ReportMetric label="需关注事项" value="2 项" warning />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <section aria-labelledby="dimensions-title">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            <h2 id="dimensions-title" className="text-lg font-semibold text-gray-900 dark:text-white">七维评价结果</h2>
            <p className="mt-1 text-sm text-gray-500">评分由固定规则计算，报告叙述不改变确定性结果。</p>
          </div>
          <Badge color="primary">权重合计 100%</Badge>
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          {DIMENSIONS.map((dimension, index) => (
            <Card key={dimension.code} className={cn("min-w-0", index === DIMENSIONS.length - 1 && "lg:col-span-2")}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-semibold text-gray-400">{String(index + 1).padStart(2, "0")}</span>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{dimension.name}</h3>
                      <Badge color="neutral">权重 {dimension.weight}%</Badge>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-gray-500">{dimension.summary}</p>
                  </div>
                  <Score value={dimension.score} />
                </div>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
                  <div
                    className={cn("h-full rounded-full", dimension.score >= 80 ? "bg-brand-500" : "bg-warning-500")}
                    style={{ width: `${dimension.score}%` }}
                  />
                </div>
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs">
                  <span className="font-medium text-gray-600 dark:text-gray-300">{dimension.metric}</span>
                  <span className="text-gray-400">证据：{dimension.evidence.join("、")}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.15fr_.85fr]">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-5 text-warning-500" />
              <h2 className="font-semibold text-gray-900 dark:text-white">关注项与建议</h2>
            </div>
            <div className="mt-4 space-y-3">
              <Finding
                title="偏差治理需关注"
                detail="培训进度偏差尚未关闭。建议补充责任人、计划完成日期及关闭证据。"
                score="68.10"
              />
              <Finding
                title="风险治理需关注"
                detail="整改跟踪措施已逾期。建议升级提醒，并在复核前补充整改结果。"
                score="68.57"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2">
              <Files className="size-5 text-brand-500" />
              <h2 className="font-semibold text-gray-900 dark:text-white">证据使用说明</h2>
            </div>
            <ul className="mt-4 space-y-3 text-sm">
              <EvidenceRow label="同项目核心链路" value="4 份" detail="采购邀请、成交公告、标段4合同、履约验收报告" />
              <EvidenceRow label="规则与分类样本" value="28 份" detail="用于测试分类、抽取、缺口识别，不合并为同一项目事实" />
              <EvidenceRow label="演示补充记录" value="9 条" detail="成本、发票、偏差、风险结构化记录，均带演示标识" />
            </ul>
          </CardContent>
        </Card>
      </section>

      <div className="flex items-start gap-3 rounded-2xl border border-gray-200 bg-gray-50 p-4 text-gray-600 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-300">
        <AlertTriangle className="mt-0.5 size-4.5 shrink-0 text-gray-400" />
        <p className="text-xs leading-5">
          本报告用于验证报告生成智能体的最小用户流程，不代表任何公开文件所涉真实项目的正式履约结论。
        </p>
      </div>
    </article>
  );
}

function ReportMetric({ label, value, warning = false }: { label: string; value: string; warning?: boolean }) {
  return (
    <div className="rounded-2xl border border-gray-200 px-4 py-3 dark:border-gray-800">
      <p className="text-xs text-gray-400">{label}</p>
      <p className={cn("mt-1 text-sm font-semibold", warning ? "text-warning-600" : "text-gray-900 dark:text-white")}>{value}</p>
    </div>
  );
}

function Score({ value }: { value: number }) {
  return (
    <div className="shrink-0 text-right">
      <p className={cn("text-2xl font-semibold", value >= 80 ? "text-brand-600" : "text-warning-600")}>{value.toFixed(2)}</p>
      <p className="text-[11px] text-gray-400">/ 100</p>
    </div>
  );
}

function Finding({ title, detail, score }: { title: string; detail: string; score: string }) {
  return (
    <article className="rounded-2xl border border-warning-200 bg-warning-50/60 p-4 dark:border-warning-500/20 dark:bg-warning-500/5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-warning-800 dark:text-warning-300">{title}</h3>
          <p className="mt-1 text-xs leading-5 text-warning-700 dark:text-warning-400">{detail}</p>
        </div>
        <Badge color="warning">{score} 分</Badge>
      </div>
    </article>
  );
}

function EvidenceRow({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <li className="rounded-2xl border border-gray-200 p-3 dark:border-gray-800">
      <div className="flex items-center justify-between gap-3">
        <span className="font-medium text-gray-800 dark:text-gray-100">{label}</span>
        <Badge color="neutral">{value}</Badge>
      </div>
      <p className="mt-1 text-xs leading-5 text-gray-500">{detail}</p>
    </li>
  );
}

function downloadReport() {
  const blob = new Blob([JSON.stringify(REPORT_RESULT, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "采购履约后评价报告_DEMO-CPE-2026-001.json";
  anchor.click();
  URL.revokeObjectURL(url);
}
