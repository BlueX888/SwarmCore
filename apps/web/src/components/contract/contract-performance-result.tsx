import { AlertTriangle, CalendarRange, CheckCircle2, FileSearch, History } from "lucide-react";
import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export const CONTRACT_PERFORMANCE_SCHEMA = "schema://contract-performance/result@1";

type MilestoneResult = {
  milestoneId: string;
  status: string;
  missingEvidenceTypes?: string[];
  evidenceIds?: string[];
};

type GanttMilestone = {
  id: string;
  title?: string;
  originalDueDate?: string | null;
  currentDueDate?: string | null;
  actualFinishDate?: string | null;
  forecastDate?: string | null;
  status?: string;
  evidenceStatus?: string;
};

export type ContractPerformanceResult = {
  schemaVersion: typeof CONTRACT_PERFORMANCE_SCHEMA;
  caseId: string;
  planVersion: number;
  asOf: string;
  status: string;
  collectionStatus: string;
  plan: {
    obligations?: Array<Record<string, unknown>>;
    milestones?: Array<Record<string, unknown>>;
    paymentConditions?: Array<Record<string, unknown>>;
    acceptanceCriteria?: Array<Record<string, unknown>>;
    serviceLevels?: Array<Record<string, unknown>>;
    changes?: Array<Record<string, unknown>>;
    [key: string]: unknown;
  };
  performance: {
    milestones?: MilestoneResult[];
    paymentGates?: Array<{
      paymentConditionId: string;
      gateStatus: string;
      paymentObserved?: boolean;
      acceptanceSatisfied?: boolean;
    }>;
    findings?: Array<{ code: string; severity?: string; targetId?: string }>;
  };
  gantt: { milestones?: GanttMilestone[]; criticalPath?: string[] | null; quality?: { status?: string; reasons?: string[] } };
  evidenceLedger: {
    evidence?: Array<Record<string, unknown>>;
    links?: Array<Record<string, unknown>>;
    unmatchedEvidenceIds?: string[];
    sourceResults?: Array<{
      sourceRef?: string;
      status?: string;
      recordCount?: number;
      attempts?: number;
      code?: string;
      nextCursor?: string | null;
    }>;
    cursors?: Record<string, string>;
  };
  changeHistory: {
    appliedChanges?: Array<Record<string, unknown>>;
    unapprovedChangeRisks?: Array<Record<string, unknown>>;
    differences?: Array<{ changeId?: string; path?: string; before?: unknown; after?: unknown }>;
  };
  approvals: Array<Record<string, unknown>>;
  provenance: Record<string, unknown>;
  resultHash: string;
};

export function asContractPerformance(value: unknown): ContractPerformanceResult | null {
  if (!value || typeof value !== "object") return null;
  const result = value as Partial<ContractPerformanceResult>;
  if (result.schemaVersion !== CONTRACT_PERFORMANCE_SCHEMA) return null;
  return result as ContractPerformanceResult;
}

export function ContractPerformanceResultView({ result }: { result: ContractPerformanceResult }) {
  const milestones = result.performance.milestones ?? [];
  const findings = result.performance.findings ?? [];
  const evidence = result.evidenceLedger.evidence ?? [];
  const unmatched = result.evidenceLedger.unmatchedEvidenceIds ?? [];
  const sourceResults = result.evidenceLedger.sourceResults ?? [];
  const changes = result.changeHistory.differences ?? [];
  const obligations = result.plan.obligations ?? [];
  const paymentConditions = result.plan.paymentConditions ?? [];

  return <div className="space-y-4">
    <section className="grid gap-3 md:grid-cols-4" aria-label="合同履约摘要">
      <Metric label="总体状态" value={result.status} tone={statusTone(result.status)} />
      <Metric label="采集状态" value={result.collectionStatus} tone={result.collectionStatus === "COMPLETE" ? "success" : "warning"} />
      <Metric label="义务 / 里程碑" value={`${obligations.length} / ${milestones.length}`} />
      <Metric label="证据 / 付款条件" value={`${evidence.length} / ${paymentConditions.length}`} />
    </section>

    {result.status === "REVIEW_REQUIRED" || unmatched.length ? <div role="alert" className="flex gap-3 rounded-2xl border border-warning-200 bg-warning-50 p-4 text-warning-800 dark:border-warning-500/20 dark:bg-warning-500/10 dark:text-warning-200">
      <AlertTriangle className="mt-0.5 size-5 shrink-0" />
      <div><p className="font-semibold">需要人工复核</p><p className="mt-1 text-sm">存在 {unmatched.length} 条未匹配证据或高影响异常，系统未据此确认验收或付款。</p></div>
    </div> : null}

    <Card><CardContent className="p-5">
      <SectionTitle icon={<CalendarRange />} title="原始基准 / 当前基准 / 实际" description={`截至 ${result.asOf} · 计划版本 ${result.planVersion}`} />
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-gray-200 text-xs text-gray-500 dark:border-gray-800"><tr><th className="pb-3">里程碑</th><th className="pb-3">原始日期</th><th className="pb-3">批准后日期</th><th className="pb-3">实际/预测</th><th className="pb-3">状态</th><th className="pb-3">证据</th></tr></thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {(result.gantt.milestones ?? []).map((item) => <tr key={item.id}>
              <td className="py-3 font-medium text-gray-900 dark:text-white">{item.title || item.id}</td>
              <td className="py-3 text-gray-500">{item.originalDueDate || "未知"}</td>
              <td className="py-3 text-gray-500">{item.currentDueDate || "未知"}</td>
              <td className="py-3 text-gray-500">{item.actualFinishDate || item.forecastDate || "—"}</td>
              <td className="py-3"><Badge color={statusTone(item.status || "UNKNOWN")}>{item.status || "UNKNOWN"}</Badge></td>
              <td className="py-3 text-gray-500">{item.evidenceStatus || "UNKNOWN"}</td>
            </tr>)}
          </tbody>
        </table>
      </div>
      {result.gantt.criticalPath === null ? <p className="mt-3 text-xs text-gray-500">资料不足，当前只展示里程碑甘特，不推断关键路径。</p> : null}
    </CardContent></Card>

    <div className="grid gap-4 xl:grid-cols-2">
      <Card><CardContent className="p-5">
        <SectionTitle icon={<FileSearch />} title="证据收件箱" description="发货、到货、验收、付款、服务与变更证据" />
        <div className="mt-4 space-y-2">
          {evidence.length ? evidence.slice(0, 20).map((item, index) => <div key={textField(item, "id", `evidence-${index}`)} className="rounded-xl border border-gray-200 p-3 dark:border-gray-800">
            <div className="flex items-center justify-between gap-3"><p className="font-medium text-gray-900 dark:text-white">{textField(item, "type", "EVIDENCE")}</p><Badge color="neutral">{textField(item, "sourceRef", "manual")}</Badge></div>
            <p className="mt-1 text-xs text-gray-500">{evidenceSummary(item)}</p>
            <p className="mt-1 truncate font-mono text-[11px] text-gray-400">{textField(item, "sourceRecordId", textField(item, "id", "—"))} · {textField(item, "contentHash", "无哈希")}</p>
          </div>) : <Empty text="尚无执行证据" />}
        </div>
      </CardContent></Card>
      <Card><CardContent className="p-5">
        <SectionTitle icon={<AlertTriangle />} title="风险、缺口与付款门禁" description="确定性规则结果，不能由模型覆盖" />
        <div className="mt-4 space-y-2">
          {findings.map((item, index) => <div key={`${item.code}-${index}`} className="flex items-center justify-between rounded-xl border border-gray-200 p-3 dark:border-gray-800"><div><p className="font-medium text-gray-900 dark:text-white">{item.code}</p><p className="text-xs text-gray-500">{item.targetId ?? "全局"}</p></div><Badge color={item.severity === "HIGH" ? "error" : "warning"}>{item.severity ?? "INFO"}</Badge></div>)}
          {(result.performance.paymentGates ?? []).map((gate) => <div key={gate.paymentConditionId} className="flex items-center justify-between rounded-xl border border-gray-200 p-3 dark:border-gray-800"><div><p className="font-medium text-gray-900 dark:text-white">付款条件 {gate.paymentConditionId}</p><p className="text-xs text-gray-500">验收 {gate.acceptanceSatisfied ? "已满足" : "未满足"} · 付款证据 {gate.paymentObserved ? "已发现" : "未发现"}</p></div><Badge color={gate.gateStatus === "ALLOWED" ? "success" : "error"}>{gate.gateStatus}</Badge></div>)}
          {!findings.length && !(result.performance.paymentGates ?? []).length ? <Empty text="未发现风险或付款门禁" /> : null}
        </div>
      </CardContent></Card>
    </div>

    {sourceResults.length ? <Card><CardContent className="p-5">
      <SectionTitle icon={<FileSearch />} title="采集源、游标与重试" description="只读源的本次实际获取结果；失败源不会推进游标" />
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        {sourceResults.map((source, index) => <div key={`${source.sourceRef}-${index}`} className="rounded-xl border border-gray-200 p-3 dark:border-gray-800">
          <div className="flex items-center justify-between gap-3">
            <p className="min-w-0 truncate font-medium text-gray-900 dark:text-white" title={source.sourceRef}>{source.sourceRef || `source-${index + 1}`}</p>
            <Badge color={source.status === "SUCCEEDED" ? "success" : "error"}>{source.status || "UNKNOWN"}</Badge>
          </div>
          <p className="mt-2 text-xs text-gray-500">记录 {source.recordCount ?? 0} · 尝试 {source.attempts ?? 1} 次{source.code ? ` · ${source.code}` : ""}</p>
          <p className="mt-1 truncate font-mono text-[11px] text-gray-400" title={source.nextCursor ?? undefined}>游标 {source.nextCursor || "未推进"}</p>
        </div>)}
      </div>
    </CardContent></Card> : null}

    <Card><CardContent className="p-5">
      <SectionTitle icon={<History />} title="变更历史与结果追溯" description="原始值不覆盖，批准变更与人工决定追加保存" />
      <div className="mt-4 space-y-2">
        {changes.length ? changes.map((item, index) => <div key={`${item.changeId}-${item.path}-${index}`} className="grid gap-2 rounded-xl border border-gray-200 p-3 text-sm md:grid-cols-[1fr_1fr_1fr] dark:border-gray-800"><p className="font-medium text-gray-900 dark:text-white">{item.path || "变更"}</p><p className="text-gray-500">原值：{display(item.before)}</p><p className="text-gray-500">新值：{display(item.after)}</p></div>) : <Empty text="当前基准没有已应用变更" />}
      </div>
      <div className="mt-4 rounded-xl bg-gray-50 p-3 text-xs text-gray-600 dark:bg-white/[0.04] dark:text-gray-400"><p className="font-semibold text-gray-900 dark:text-white">冻结结果哈希</p><p className="mt-1 break-all font-mono">{result.resultHash}</p><p className="mt-2 break-all">计划：{display(result.provenance.planHash)} · 规则：{display(result.provenance.ruleSetRef)}</p></div>
      <div className="mt-3 grid gap-3 text-xs md:grid-cols-3">
        <Trace label="模型 / Agent" value={traceValue(result.provenance, ["modelRef", "agentRefs"])} />
        <Trace label="工具版本" value={traceValue(result.provenance, ["toolRefs"])} />
        <Trace label="人工决定" value={`${result.approvals.length} 条`} />
      </div>
    </CardContent></Card>
  </div>;
}

function SectionTitle({ icon, title, description }: { icon: ReactNode; title: string; description: string }) {
  return <div className="flex items-start gap-3"><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 [&>svg]:size-4 dark:bg-brand-500/10 dark:text-brand-300">{icon}</span><div><h2 className="font-semibold text-gray-900 dark:text-white">{title}</h2><p className="mt-0.5 text-xs text-gray-500">{description}</p></div></div>;
}

function Metric({ label, value, tone = "neutral" }: { label: string; value: string; tone?: "neutral" | "success" | "warning" | "error" }) {
  return <Card><CardContent className="p-4"><p className="text-xs text-gray-500">{label}</p><div className="mt-2 flex items-center gap-2">{tone === "success" ? <CheckCircle2 className="size-4 text-success-500" /> : null}<Badge color={tone}>{value}</Badge></div></CardContent></Card>;
}

function Empty({ text }: { text: string }) {
  return <p className="rounded-xl border border-dashed border-gray-200 p-4 text-center text-sm text-gray-500 dark:border-gray-800">{text}</p>;
}

function Trace({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-gray-200 p-3 dark:border-gray-800"><p className="text-gray-400">{label}</p><p className="mt-1 break-all text-gray-700 dark:text-gray-200">{value}</p></div>;
}

function display(value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  return typeof value === "string" ? value : JSON.stringify(value);
}

function textField(value: Record<string, unknown>, key: string, fallback: string) {
  const item = value[key];
  return typeof item === "string" || typeof item === "number" ? String(item) : fallback;
}

function evidenceSummary(value: Record<string, unknown>) {
  const parts = [
    textField(value, "businessDate", ""),
    money(value.amount, textField(value, "currency", "")),
    nestedText(value, "contractKeys", "supplier"),
    nestedText(value, "contractKeys", "expenseArea"),
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : "暂无结构化业务摘要";
}

function money(value: unknown, currency: string) {
  if (typeof value !== "number") return "";
  return `${currency ? `${currency} ` : ""}${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function nestedText(value: Record<string, unknown>, parent: string, key: string) {
  const nested = value[parent];
  if (!nested || typeof nested !== "object" || Array.isArray(nested)) return "";
  return textField(nested as Record<string, unknown>, key, "");
}

function traceValue(value: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const item = value[key];
    if (Array.isArray(item) && item.length) return item.map(String).join("、");
    if (typeof item === "string" && item) return item;
  }
  return "见技术运行详情";
}

function statusTone(status: string): "neutral" | "success" | "warning" | "error" {
  if (["COMPLETED", "ACCEPTED", "ALLOWED", "COMPLETE"].includes(status)) return "success";
  if (["OVERDUE", "REJECTED", "BLOCKED"].includes(status)) return "error";
  if (["AT_RISK", "EVIDENCE_PENDING", "REVIEW_REQUIRED", "PARTIAL"].includes(status)) return "warning";
  return "neutral";
}
