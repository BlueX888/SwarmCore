import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, FileText, Link2 } from "lucide-react";
import { Link, useParams } from "react-router";
import { api } from "@/api/client";
import type { PostEvaluationResult } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { BackLink } from "@/components/ui/back-link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  asInvoiceAssurance,
  InvoiceAssuranceResultView,
} from "@/components/invoice/invoice-assurance-result";
import { useWorkspaceScope } from "@/lib/demo-scope";

const TERMINAL = new Set(["SUCCEEDED", "FAILED", "COMPLETED", "CANCELLED", "REJECTED"]);

export function AssessmentPage() {
  const { assessmentId = "" } = useParams();
  const { tenantId, projectId, workspacePath } = useWorkspaceScope();
  const assessment = useQuery({
    queryKey: ["assessment", tenantId, projectId, assessmentId],
    queryFn: () => api.getAssessment(tenantId, projectId, assessmentId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && !TERMINAL.has(status) ? 2000 : false;
    },
  });
  const run = useQuery({
    queryKey: ["run", tenantId, projectId, assessment.data?.runId],
    queryFn: () => {
      const runId = assessment.data?.runId;
      if (!runId) throw new Error("缺少关联 Run");
      return api.getRun(tenantId, projectId, runId);
    },
    enabled: Boolean(assessment.data?.runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && !TERMINAL.has(status) ? 2000 : false;
    },
  });
  const findings = useQuery({
    queryKey: ["case-findings", tenantId, projectId, assessment.data?.caseId],
    queryFn: () => {
      const caseId = assessment.data?.caseId;
      if (!caseId) throw new Error("缺少案件 ID");
      return api.listCaseFindings(tenantId, projectId, caseId);
    },
    enabled: Boolean(assessment.data?.caseId),
  });
  const reports = useQuery({
    queryKey: ["evaluation-reports", tenantId, projectId, assessmentId],
    queryFn: () => api.listEvaluationReports(tenantId, projectId, assessmentId),
    enabled: Boolean(assessmentId),
  });
  const snapshots = useQuery({
    queryKey: ["assessment-document-snapshots", tenantId, projectId, assessmentId],
    queryFn: () => api.listAssessmentDocumentSnapshots(tenantId, projectId, assessmentId),
    enabled: Boolean(assessmentId),
  });

  if (assessment.isPending) return <div className="space-y-4"><Skeleton className="h-28" /><Skeleton className="h-80" /></div>;
  if (assessment.isError || !assessment.data) {
    return <Card><CardContent className="flex min-h-72 flex-col items-center justify-center gap-3 p-6 text-center">
      <AlertTriangle className="size-8 text-gray-400" />
      <h1 className="text-lg font-semibold">Assessment 无法加载</h1>
      <p className="text-sm text-gray-500">{assessment.error?.message ?? "未找到评估结果"}</p>
      <Button onClick={() => void assessment.refetch()}>重试</Button>
    </CardContent></Card>;
  }

  const detail = assessment.data;
  const invoiceResult = asInvoiceAssurance(detail.result);
  const deviationResult = invoiceResult ? null : asDeviationAnalysis(detail.result);
  const result = invoiceResult || deviationResult ? null : asPostEvaluation(detail.result);
  const inProgress = !TERMINAL.has(detail.status) && !TERMINAL.has(run.data?.status ?? "");
  const snapshotItems = (snapshots.data?.items ?? []).map((item, index) => ({
    id: stringField(item, "documentUsageSnapshotId")
      ?? stringField(item, "businessDocumentVersionId")
      ?? `snapshot-${index + 1}`,
    label: stringField(item, "businessWorkKey")
      ?? stringField(item, "sha256")
      ?? `snapshot-${index + 1}`,
  }));

  return <div className="min-w-0 space-y-6">
    <header>
      <BackLink to={`${workspacePath}/business-works`}>返回业务工作</BackLink>
      <div className="mt-5 flex flex-col gap-4 rounded-[24px] border border-gray-200/80 bg-white/90 p-6 shadow-theme-card md:flex-row md:items-start md:justify-between dark:border-gray-800 dark:bg-white/[0.035]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-brand-500">Assessment</p>
            <Badge color={statusColor(detail.status)}>{detail.status}</Badge>
            {run.data ? <Badge color="neutral">Run · {run.data.status}</Badge> : null}
          </div>
          <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">评估结果</h1>
          <p className="mt-2 text-sm text-gray-500">案件 {detail.caseId}{detail.scenarioType ? ` · ${detail.scenarioType}` : ""}{detail.owner ? ` · ${detail.owner}` : ""}</p>
        </div>
        <Button asChild variant="outline"><Link to={`${workspacePath}/runs/${detail.runId}`}><Activity />查看技术运行详情</Link></Button>
      </div>
    </header>

    {inProgress ? <Card><CardContent className="border border-brand-200 bg-brand-50/60 p-5 text-sm text-brand-800 dark:border-brand-500/20 dark:bg-brand-500/10 dark:text-brand-300">评估仍在进行中，正在同步关联 Run 状态（{run.data?.status ?? detail.status}）…</CardContent></Card> : null}

    <section className="grid gap-3 md:grid-cols-4" aria-label="评估摘要">
      <Metric label="评估状态" value={detail.status} />
      <Metric label="案件状态" value={detail.caseStatus ?? "—"} />
      <Metric label="发起时间" value={formatTime(detail.createdAt)} />
      <Metric label="完成时间" value={run.data?.completedAt ? formatTime(run.data.completedAt) : inProgress ? "进行中" : "—"} />
    </section>

    {invoiceResult ? <InvoiceAssuranceResultView result={invoiceResult} /> : deviationResult ? <DeviationAnalysisResult result={deviationResult} /> : result ? <div className="space-y-4">
      {result.readabilityGate || result.reportQuality ? <Card><CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">报告质量状态</h2>
            <p className="mt-1 text-xs text-gray-500">正式报告门槛为资料正文可读取率 80%，并通过章节、分数与证据引用校验。</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {result.readabilityGate ? <Badge color={result.readabilityGate.formalEligible ? "success" : "warning"}>
              {result.readabilityGate.reportMode === "FORMAL_REPORT" ? "正式报告" : "资料质量预审"}
            </Badge> : null}
            {result.reportQuality ? <Badge color={result.reportQuality.passed ? "success" : "error"}>
              {result.reportQuality.passed ? "质量门已通过" : "质量门未通过"}
            </Badge> : null}
          </div>
        </div>
        {result.readabilityGate ? <div className="grid gap-3 md:grid-cols-3">
          <Metric label="资料可读率" value={formatPercent(result.readabilityGate.readabilityRate)} />
          <Metric label="可读资料" value={`${result.readabilityGate.readableDocumentCount} / ${result.readabilityGate.documentCount}`} />
          <Metric label="报告编号" value={result.reportDocument?.reportNumber ?? "—"} />
        </div> : null}
        {result.reportQuality?.blockingIssues.length ? <p className="rounded-xl bg-error-50 p-3 text-sm text-error-700 dark:bg-error-500/10 dark:text-error-300">{result.reportQuality.blockingIssues.join("；")}</p> : null}
        {result.reportQuality?.warnings.length ? <p className="rounded-xl bg-warning-50 p-3 text-sm text-warning-700 dark:bg-warning-500/10 dark:text-warning-300">{result.reportQuality.warnings.join("；")}</p> : null}
      </CardContent></Card> : null}
      <Card><CardContent className="space-y-4 p-5">
      <h2 className="font-semibold text-gray-900 dark:text-white">综合结论</h2>
      <p className="text-sm leading-6 text-gray-600 dark:text-gray-300">{result.executiveSummary}</p>
      <div className="flex flex-wrap gap-2">
        <Badge color={result.passed ? "success" : "warning"}>总分 {result.overallScore} · {result.grade}</Badge>
        <Badge color="neutral">风险 {result.riskLevel}</Badge>
        {result.reviewRequired ? <Badge color="warning">需要复核</Badge> : null}
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {result.dimensions.map((dimension) => <article key={dimension.code} className="rounded-xl border border-gray-200 p-4 dark:border-gray-800">
          <div className="flex items-center justify-between gap-2"><h3 className="font-medium text-gray-900 dark:text-white">{dimension.name}</h3><Badge color="neutral">{dimension.score ?? "—"}</Badge></div>
          <p className="mt-2 text-xs leading-5 text-gray-500">{dimension.summary}</p>
        </article>)}
      </div>
    </CardContent></Card></div> : detail.result ? <Card><CardContent className="p-5"><h2 className="font-semibold">综合结论</h2><pre className="mt-3 overflow-auto rounded-xl bg-gray-950 p-4 text-xs text-gray-100">{JSON.stringify(detail.result, null, 2)}</pre></CardContent></Card> : null}

    <div className="grid gap-4 xl:grid-cols-2">
      <Card><CardContent className="space-y-4 p-5">
        <h2 className="font-semibold text-gray-900 dark:text-white">Findings</h2>
        {findings.isPending ? <Skeleton className="h-32" /> : findings.data?.items.length ? <ul className="space-y-3">{findings.data.items.map((finding) => <li key={finding.findingId} className="rounded-xl border border-gray-200 p-3 dark:border-gray-800">
          <div className="flex flex-wrap items-center gap-2"><Badge color="warning">{finding.severity}</Badge><Badge color="neutral">{finding.status}</Badge><span className="text-sm font-medium text-gray-900 dark:text-white">{finding.title}</span></div>
          <p className="mt-2 text-xs text-gray-500">{finding.detail}</p>
        </li>)}</ul> : <p className="text-sm text-gray-500">暂无 Finding。</p>}
      </CardContent></Card>

      <Card><CardContent className="space-y-4 p-5">
        <h2 className="font-semibold text-gray-900 dark:text-white">Reports</h2>
        {reports.isPending ? <Skeleton className="h-32" /> : reports.data?.items.length ? <ul className="space-y-3">{reports.data.items.map((report) => <li key={report.reportId} className="flex items-center justify-between gap-3 rounded-xl border border-gray-200 p-3 dark:border-gray-800">
          <div className="flex items-center gap-2"><FileText className="size-4 text-brand-600" /><div><p className="text-sm font-medium">{report.format}</p><p className="text-xs text-gray-500">{formatTime(report.createdAt)}</p></div></div>
          <Badge color="neutral">{report.templateVersion}</Badge>
        </li>)}</ul> : <p className="text-sm text-gray-500">暂无报告。</p>}
      </CardContent></Card>
    </div>

    <Card><CardContent className="space-y-4 p-5">
      <h2 className="font-semibold text-gray-900 dark:text-white">使用的资料快照</h2>
      {snapshots.isPending ? <Skeleton className="h-24" /> : snapshotItems.length ? <ul className="space-y-2">{snapshotItems.map((item) => <li key={item.id} className="flex items-center gap-2 rounded-xl bg-gray-50 px-3 py-2 text-sm dark:bg-gray-800/60"><Link2 className="size-4 text-gray-400" /><span>{item.label}</span></li>)}</ul> : <p className="text-sm text-gray-500">暂无资料快照。</p>}
    </CardContent></Card>

    {detail.casePayload ? <Card><CardContent className="space-y-3 p-5">
      <h2 className="font-semibold text-gray-900 dark:text-white">案件基本信息</h2>
      <pre className="overflow-auto rounded-xl bg-gray-950 p-4 text-xs text-gray-100">{JSON.stringify(detail.casePayload, null, 2)}</pre>
    </CardContent></Card> : null}
  </div>;
}

type DeviationDimension = {
  status: "OK" | "DATA_INSUFFICIENT" | "CONFLICTED" | "NOT_APPLICABLE";
  metrics: Record<string, unknown>;
  reasons: string[];
  evidenceRefs: string[];
};

type DeviationAnalysisResult = {
  schemaVersion: "schema://deviation-analysis/result@1";
  title: string;
  asOf: string | null;
  qualityStatus: "READY" | "REVIEW_REQUIRED" | "BLOCKED";
  reviewRequired: boolean;
  dimensions: Partial<Record<"TIME" | "CONTENT" | "COST", DeviationDimension>>;
  rootCauses: Record<string, unknown>[];
  trends: { status?: string; summary?: string; points?: Record<string, unknown>[] };
  responsibility: {
    status: string;
    humanConfirmationRequired: boolean;
    proposals: Record<string, unknown>[];
    decisions: Record<string, unknown>[];
  };
  evidenceReview: Record<string, unknown>;
  narrative: { executiveSummary?: string; recommendations?: string[] };
  provenance: Record<string, unknown>;
};

function DeviationAnalysisResult({ result }: { result: DeviationAnalysisResult }) {
  const points = result.trends.points ?? [];
  return <div className="space-y-4">
    <Card><CardContent className="space-y-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-gray-900 dark:text-white">{result.title}</h2>
          <p className="mt-1 text-xs text-gray-500">评估时点 {result.asOf ?? "—"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge color={result.qualityStatus === "READY" ? "success" : result.qualityStatus === "BLOCKED" ? "error" : "warning"}>{result.qualityStatus}</Badge>
          {result.reviewRequired ? <Badge color="warning">需要人工复核</Badge> : null}
        </div>
      </div>
      <p className="text-sm leading-6 text-gray-600 dark:text-gray-300">{result.narrative.executiveSummary ?? "已完成结构化偏差分析。"}</p>
      <div className="grid gap-3 md:grid-cols-3">
        {(["TIME", "CONTENT", "COST"] as const).map((code) => {
          const dimension = result.dimensions[code];
          return <article key={code} className="rounded-xl border border-gray-200 p-4 dark:border-gray-800">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-medium text-gray-900 dark:text-white">{dimensionName(code)}</h3>
              <Badge color={dimension?.status === "OK" ? "success" : dimension?.status === "CONFLICTED" ? "error" : "warning"}>{dimension?.status ?? "未请求"}</Badge>
            </div>
            {dimension ? <DimensionMetrics code={code} metrics={dimension.metrics} /> : null}
            {dimension?.reasons.length ? <p className="mt-2 text-xs leading-5 text-warning-600">{dimension.reasons.join("；")}</p> : null}
          </article>;
        })}
      </div>
    </CardContent></Card>

    <Card><CardContent className="space-y-4 p-5">
      <div>
        <h2 className="font-semibold text-gray-900 dark:text-white">同口径趋势</h2>
        <p className="mt-1 text-xs text-gray-500">{result.trends.summary ?? "暂无趋势说明"}</p>
      </div>
      {points.length >= 2 ? <div className="grid gap-4 lg:grid-cols-3">
        <TrendChart title="最大时间偏差（天）" points={points} field="timeVarianceDays" />
        <TrendChart title="内容偏差率" points={points} field="contentVarianceRate" percent />
        <TrendChart title="成本偏差率" points={points} field="costVarianceRate" percent />
      </div> : <p className="rounded-xl bg-gray-50 p-4 text-sm text-gray-500 dark:bg-gray-800/60">首次评估或没有同基线、同配置历史结果，暂不判断趋势。</p>}
    </CardContent></Card>

    <div className="grid gap-4 xl:grid-cols-2">
      <Card><CardContent className="space-y-4 p-5">
        <h2 className="font-semibold text-gray-900 dark:text-white">AI 根因分析</h2>
        {result.rootCauses.length ? <ul className="space-y-3">{result.rootCauses.map((cause, index) => <li key={displayValue(cause.causeId, String(index))} className="rounded-xl border border-gray-200 p-3 dark:border-gray-800">
          <p className="text-sm font-medium text-gray-900 dark:text-white">{displayValue(cause.title, displayValue(cause.cause, `根因 ${index + 1}`))}</p>
          <p className="mt-1 text-xs leading-5 text-gray-500">{displayValue(cause.rationale, displayValue(cause.description, "详见证据引用"))}</p>
        </li>)}</ul> : <p className="text-sm text-gray-500">未形成有充分证据支持的根因假设。</p>}
      </CardContent></Card>
      <Card><CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-semibold text-gray-900 dark:text-white">责任归属建议</h2>
          <Badge color="warning">待人工确认</Badge>
        </div>
        <p className="text-xs leading-5 text-gray-500">AI 只提供建议；正式状态只能由人工确认为 CONFIRMED 或 DISPUTED。</p>
        {result.responsibility.proposals.length ? <ul className="space-y-3">{result.responsibility.proposals.map((item, index) => <li key={displayValue(item.proposalId, String(index))} className="rounded-xl border border-gray-200 p-3 dark:border-gray-800">
          <div className="flex flex-wrap items-center gap-2"><span className="text-sm font-medium">{displayValue(item.party, "待确认")}</span><Badge color="neutral">{displayValue(item.scope, "UNSPECIFIED")}</Badge><Badge color="warning">{displayValue(item.status, "PROPOSED")}</Badge></div>
          <p className="mt-2 text-xs leading-5 text-gray-500">{displayValue(item.rationale, "证据不足")}</p>
        </li>)}</ul> : <p className="text-sm text-gray-500">暂无责任归属建议。</p>}
      </CardContent></Card>
    </div>
  </div>;
}

function DimensionMetrics({ code, metrics }: { code: "TIME" | "CONTENT" | "COST"; metrics: Record<string, unknown> }) {
  const values = code === "TIME"
    ? [["最大延期", formatMetric(metrics.maximumDelayDays, " 天")], ["按时率", formatPercent(metrics.onTimeRate)], ["SPI", formatMetric(metrics.spi)]]
    : code === "CONTENT"
      ? [["实际完成率", formatPercent(metrics.actualCompletionRate)], ["内容偏差率", formatPercent(metrics.contentVarianceRate)], ["等权回退", metrics.equalWeightFallback === true ? "是" : "否"]]
      : [["当前 BAC", formatMoney(metrics.currentBAC, metrics.currency)], ["EAC", formatMoney(metrics.eac, metrics.currency)], ["成本偏差率", formatPercent(metrics.costVarianceRate)]];
  return <dl className="mt-3 space-y-2">{values.map(([label, value]) => <div key={label} className="flex items-center justify-between gap-3 text-xs"><dt className="text-gray-500">{label}</dt><dd className="font-medium text-gray-800 dark:text-gray-200">{value}</dd></div>)}</dl>;
}

function TrendChart({ title, points, field, percent = false }: { title: string; points: Record<string, unknown>[]; field: string; percent?: boolean }) {
  const values = points.map((point) => {
    const value = point[field];
    return typeof value === "number" ? value : null;
  });
  const numeric = values.filter((value): value is number => value !== null);
  if (!numeric.length) return <figure className="rounded-xl border border-gray-200 p-4 dark:border-gray-800"><figcaption className="text-xs font-medium text-gray-700 dark:text-gray-300">{title}</figcaption><p className="mt-6 text-center text-xs text-gray-400">无可比数值</p></figure>;
  const minimum = Math.min(...numeric);
  const maximum = Math.max(...numeric);
  const range = maximum - minimum || 1;
  const coordinates = values.map((value, index) => {
    const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100;
    const y = value === null ? 50 : 88 - ((value - minimum) / range) * 76;
    return `${x},${y}`;
  }).join(" ");
  return <figure className="rounded-xl border border-gray-200 p-4 dark:border-gray-800">
    <figcaption className="text-xs font-medium text-gray-700 dark:text-gray-300">{title}</figcaption>
    <svg viewBox="0 0 100 100" className="mt-3 h-28 w-full overflow-visible" role="img" aria-label={`${title}趋势图`}>
      <line x1="0" y1="88" x2="100" y2="88" stroke="currentColor" className="text-gray-200 dark:text-gray-700" strokeWidth="1" />
      <polyline points={coordinates} fill="none" stroke="currentColor" className="text-brand-500" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
      {coordinates.split(" ").map((coordinate, index) => {
        const [cx, cy] = coordinate.split(",");
        return <circle key={`${cx}-${index}`} cx={cx} cy={cy} r="3" fill="currentColor" className="text-brand-600" />;
      })}
    </svg>
    <div className="mt-1 flex justify-between text-[10px] text-gray-400">
      <span>{displayValue(points[0]?.asOf, "")}</span>
      <span>{values.at(-1) === null ? "—" : percent ? formatPercent(values.at(-1)) : formatMetric(values.at(-1))}</span>
      <span>{displayValue(points.at(-1)?.asOf, "")}</span>
    </div>
  </figure>;
}

function asDeviationAnalysis(value: unknown): DeviationAnalysisResult | null {
  if (!value || typeof value !== "object") return null;
  const result = value as Partial<DeviationAnalysisResult>;
  if (result.schemaVersion !== "schema://deviation-analysis/result@1" || !result.dimensions || !result.responsibility) return null;
  return result as DeviationAnalysisResult;
}

function dimensionName(code: "TIME" | "CONTENT" | "COST") {
  return code === "TIME" ? "时间偏差" : code === "CONTENT" ? "内容偏差" : "成本偏差";
}

function formatMetric(value: unknown, suffix = "") {
  return typeof value === "number" ? `${new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 4 }).format(value)}${suffix}` : "—";
}

function formatPercent(value: unknown) {
  return typeof value === "number" ? new Intl.NumberFormat("zh-CN", { style: "percent", maximumFractionDigits: 2 }).format(value) : "—";
}

function formatMoney(value: unknown, currency: unknown) {
  if (typeof value !== "number") return "—";
  try {
    return new Intl.NumberFormat("zh-CN", { style: "currency", currency: typeof currency === "string" && currency ? currency : "CNY" }).format(value);
  } catch {
    return formatMetric(value);
  }
}

function displayValue(value: unknown, fallback: string) {
  return typeof value === "string" || typeof value === "number" ? String(value) : fallback;
}

function asPostEvaluation(value: unknown): PostEvaluationResult | null {
  if (!value || typeof value !== "object") return null;
  const result = value as Partial<PostEvaluationResult>;
  if (typeof result.executiveSummary !== "string" || !Array.isArray(result.dimensions)) return null;
  return result as PostEvaluationResult;
}

function stringField(item: Record<string, unknown>, key: string): string | null {
  const value = item[key];
  return typeof value === "string" || typeof value === "number" ? String(value) : null;
}

function statusColor(status: string): "success" | "warning" | "error" | "neutral" | "primary" {
  if (status === "SUCCEEDED" || status === "COMPLETED") return "success";
  if (status === "FAILED" || status === "REJECTED" || status === "CANCELLED") return "error";
  if (status === "RUNNING" || status === "ACCEPTED") return "primary";
  return "warning";
}

function formatTime(value: string) {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function Metric({ label, value }: { label: string; value: string }) {
  return <Card><CardContent className="p-4"><p className="text-xs text-gray-500">{label}</p><p className="mt-2 truncate text-sm font-semibold text-gray-900 dark:text-white" title={value}>{value}</p></CardContent></Card>;
}
