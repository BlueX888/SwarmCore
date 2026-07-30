import { AlertTriangle, FileDiff, Gauge, History, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";

export const PROCUREMENT_SUPPLIER_RISK_SCHEMA =
  "schema://procurement-supplier-risk/result@1";

type EvidenceRef = Record<string, unknown>;

type ConsistencyFinding = {
  findingId: string;
  category: string;
  severity: string;
  changeType: string;
  title: string;
  summary: string;
  evidenceRefs?: EvidenceRef[];
};

type ClauseLineage = {
  matchKey: string;
  category: string;
  changeType: string;
  clauses: Partial<
    Record<
      "TENDER" | "BID" | "AWARD" | "CONTRACT",
      { clauseId?: string; text?: string; evidenceRefs?: EvidenceRef[] }
    >
  >;
};

export type ProcurementSupplierRiskResult = {
  schemaVersion: typeof PROCUREMENT_SUPPLIER_RISK_SCHEMA;
  caseId: string;
  monitorId?: string | null;
  assessmentId: string;
  asOf: string;
  supplier: { name?: string; creditCode?: string };
  decision: "PASS" | "CONDITIONAL_PASS" | "REVIEW_REQUIRED" | "BLOCK";
  riskLevel: string;
  consistency: {
    clauseLineages?: ClauseLineage[];
    findings?: ConsistencyFinding[];
    counts?: Record<string, number>;
    blocking?: boolean;
  };
  risk: {
    overallRiskScore?: number;
    externalRiskScore?: number;
    dataCoverage?: number;
    sourceStatuses?: Array<{
      sourceRef?: string;
      status?: string;
      fetchedAt?: string;
      errorCode?: string;
    }>;
    hardGates?: Array<{
      code?: string;
      sourceRef?: string;
      sourceRecordId?: string;
      effectiveTo?: string;
      evidenceRefs?: EvidenceRef[];
    }>;
    dimensionPoints?: Record<string, number>;
    identityReviewRequired?: boolean;
  };
  performance: {
    score?: number | null;
    coverage?: number;
    sampleSize?: number;
    status?: string;
    metrics?: Array<{
      key: string;
      value?: number | null;
      weight?: number;
      available?: boolean;
    }>;
  };
  history: {
    hasMaterialChange?: boolean;
    riskLevelChange?: { from?: string | null; to?: string | null };
    decisionChange?: { from?: string | null; to?: string | null };
    added?: Array<Record<string, unknown>>;
    removed?: Array<Record<string, unknown>>;
    changed?: Array<Record<string, unknown>>;
  };
  provenance: Record<string, unknown>;
  snapshotHash: string;
  resultHash: string;
};

export function asProcurementSupplierRisk(
  value: unknown,
): ProcurementSupplierRiskResult | null {
  if (!value || typeof value !== "object") return null;
  const result = value as Partial<ProcurementSupplierRiskResult>;
  if (result.schemaVersion !== PROCUREMENT_SUPPLIER_RISK_SCHEMA) return null;
  return result as ProcurementSupplierRiskResult;
}

export function ProcurementSupplierRiskResultView({
  result,
}: {
  result: ProcurementSupplierRiskResult;
}) {
  const findings = result.consistency.findings ?? [];
  const lineages = result.consistency.clauseLineages ?? [];
  const hardGates = result.risk.hardGates ?? [];
  const sources = result.risk.sourceStatuses ?? [];
  const metrics = result.performance.metrics ?? [];
  const historyCount =
    (result.history.added?.length ?? 0) +
    (result.history.removed?.length ?? 0) +
    (result.history.changed?.length ?? 0);

  return (
    <div className="space-y-4">
      <section className="grid gap-3 md:grid-cols-4" aria-label="招采与供应商风控摘要">
        <Metric label="签署建议" value={result.decision} tone={decisionTone(result.decision)} />
        <Metric label="风险等级" value={result.riskLevel} tone={riskTone(result.riskLevel)} />
        <Metric
          label="综合风险分"
          value={numberText(result.risk.overallRiskScore)}
          tone={riskTone(result.riskLevel)}
        />
        <Metric
          label="供应商绩效"
          value={
            result.performance.score == null
              ? "资料不足"
              : `${numberText(result.performance.score)} 分`
          }
          tone={result.performance.status === "SCORED" ? "success" : "warning"}
        />
      </section>

      {hardGates.length ? (
        <div
          role="alert"
          className="flex gap-3 rounded-2xl border border-error-200 bg-error-50 p-4 text-error-800 dark:border-error-500/20 dark:bg-error-500/10 dark:text-error-200"
        >
          <ShieldAlert className="mt-0.5 size-5 shrink-0" />
          <div>
            <p className="font-semibold">命中供应商准入硬性门禁</p>
            <p className="mt-1 text-sm">
              已命中 {hardGates.length} 条有效禁入或黑名单记录；硬性门禁不允许模型覆盖。
            </p>
          </div>
        </div>
      ) : null}

      <Card>
        <CardContent className="p-5">
          <SectionTitle
            icon={<FileDiff />}
            title="招标 / 投标 / 中标 / 合同四方条款链"
            description={`共 ${lineages.length} 条条款链，发现 ${findings.length} 项差异`}
          />
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="border-b border-gray-200 text-xs text-gray-500 dark:border-gray-800">
                <tr>
                  <th className="pb-3">条款</th>
                  <th className="pb-3">招标</th>
                  <th className="pb-3">投标</th>
                  <th className="pb-3">中标</th>
                  <th className="pb-3">合同</th>
                  <th className="pb-3">变化</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {lineages.map((item) => (
                  <tr key={item.matchKey}>
                    <td className="max-w-40 py-3 pr-3 font-medium text-gray-900 dark:text-white">
                      {item.category}
                      <p className="mt-1 break-all text-[11px] font-normal text-gray-400">
                        {item.matchKey}
                      </p>
                    </td>
                    {(["TENDER", "BID", "AWARD", "CONTRACT"] as const).map((role) => (
                      <td key={role} className="max-w-52 py-3 pr-3 text-xs text-gray-600 dark:text-gray-300">
                        <p className="line-clamp-3">{item.clauses[role]?.text ?? "缺失"}</p>
                        <p className="mt-1 text-[11px] text-gray-400">
                          证据 {item.clauses[role]?.evidenceRefs?.length ?? 0}
                        </p>
                      </td>
                    ))}
                    <td className="py-3">
                      <Badge color={item.changeType === "UNCHANGED" ? "success" : "warning"}>
                        {item.changeType}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!lineages.length ? <EmptyState compact tone="neutral" title="尚无可展示的条款链" /> : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardContent className="p-5">
            <SectionTitle
              icon={<AlertTriangle />}
              title="分级差异与硬性门禁"
              description="结论附带来源记录和文档页码证据"
            />
            <div className="mt-4 space-y-2">
              {hardGates.map((gate, index) => (
                <EvidenceRow
                  key={`${gate.code}-${gate.sourceRecordId}-${index}`}
                  title={gate.code ?? "HARD_GATE"}
                  detail={`${gate.sourceRef ?? "未知来源"} · ${gate.sourceRecordId ?? "无记录号"} · 有效至 ${gate.effectiveTo ?? "未提供"}`}
                  badge="BLOCKER"
                  tone="error"
                  evidenceCount={gate.evidenceRefs?.length ?? 0}
                />
              ))}
              {findings.map((finding) => (
                <EvidenceRow
                  key={finding.findingId}
                  title={finding.title}
                  detail={finding.summary}
                  badge={finding.severity}
                  tone={severityTone(finding.severity)}
                  evidenceCount={finding.evidenceRefs?.length ?? 0}
                />
              ))}
              {!hardGates.length && !findings.length ? <EmptyState compact tone="neutral" title="未发现差异或准入门禁" /> : null}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <SectionTitle
              icon={<Gauge />}
              title="真实数据覆盖与供应商绩效"
              description={`外部风险 ${numberText(result.risk.externalRiskScore)} · 数据覆盖 ${percentText(result.risk.dataCoverage)}`}
            />
            <div className="mt-4 space-y-2">
              {sources.map((source, index) => (
                <div
                  key={`${source.sourceRef}-${index}`}
                  className="flex items-start justify-between gap-3 rounded-xl border border-gray-200 p-3 dark:border-gray-800"
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {source.sourceRef ?? "未命名来源"}
                    </p>
                    <p className="mt-1 text-xs text-gray-500">
                      {source.fetchedAt ?? "未返回采集时间"}
                      {source.errorCode ? ` · ${source.errorCode}` : ""}
                    </p>
                  </div>
                  <Badge color={source.status === "SUCCEEDED" ? "success" : "error"}>
                    {source.status ?? "UNKNOWN"}
                  </Badge>
                </div>
              ))}
              {metrics.map((metric) => (
                <div
                  key={metric.key}
                  className="grid grid-cols-[1fr_auto_auto] items-center gap-3 rounded-xl bg-gray-50 px-3 py-2 text-sm dark:bg-white/[0.04]"
                >
                  <span>{metric.key}</span>
                  <span className="text-gray-500">权重 {metric.weight ?? 0}%</span>
                  <Badge color={metric.available ? "success" : "warning"}>
                    {metric.value == null ? "缺数据" : `${numberText(metric.value)}%`}
                  </Badge>
                </div>
              ))}
              {!sources.length && !metrics.length ? <EmptyState compact tone="neutral" title="尚无风控源或绩效记录" /> : null}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-5">
          <SectionTitle
            icon={<History />}
            title="历史变化与可追溯依据"
            description={`实质变化 ${result.history.hasMaterialChange ? "是" : "否"} · 记录变化 ${historyCount} 条`}
          />
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <TraceItem
              label="风险等级"
              value={`${result.history.riskLevelChange?.from ?? "首次"} → ${result.history.riskLevelChange?.to ?? result.riskLevel}`}
            />
            <TraceItem
              label="决策变化"
              value={`${result.history.decisionChange?.from ?? "首次"} → ${result.history.decisionChange?.to ?? result.decision}`}
            />
            <TraceItem
              label="供应商"
              value={`${result.supplier.name ?? "—"} · ${result.supplier.creditCode ?? "—"}`}
            />
          </div>
          <div className="mt-4 rounded-xl bg-gray-50 p-3 text-xs text-gray-600 dark:bg-white/[0.04] dark:text-gray-400">
            <p className="font-semibold text-gray-900 dark:text-white">冻结结果与依据</p>
            <p className="mt-2 break-all font-mono">resultHash: {result.resultHash}</p>
            <p className="mt-1 break-all font-mono">snapshotHash: {result.snapshotHash}</p>
            <p className="mt-2 break-all">规则：{display(result.provenance.ruleVersions)}</p>
            <p className="mt-1 break-all">资料：{display(result.provenance.documentContentHash)}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function SectionTitle({
  icon,
  title,
  description,
}: {
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600 [&>svg]:size-4 dark:bg-brand-500/10 dark:text-brand-300">
        {icon}
      </span>
      <div>
        <h2 className="font-semibold text-gray-900 dark:text-white">{title}</h2>
        <p className="mt-0.5 text-xs text-gray-500">{description}</p>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "neutral" | "success" | "warning" | "error";
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs text-gray-500">{label}</p>
        <div className="mt-2">
          <Badge color={tone}>{value}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}

function EvidenceRow({
  title,
  detail,
  badge,
  tone,
  evidenceCount,
}: {
  title: string;
  detail: string;
  badge: string;
  tone: "neutral" | "success" | "warning" | "error";
  evidenceCount: number;
}) {
  return (
    <div className="rounded-xl border border-gray-200 p-3 dark:border-gray-800">
      <div className="flex items-start justify-between gap-3">
        <p className="font-medium text-gray-900 dark:text-white">{title}</p>
        <Badge color={tone}>{badge}</Badge>
      </div>
      <p className="mt-1 text-xs leading-5 text-gray-500">{detail}</p>
      <p className="mt-2 text-[11px] text-gray-400">证据引用 {evidenceCount}</p>
    </div>
  );
}

function TraceItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-gray-200 p-3 dark:border-gray-800">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

function display(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return typeof value === "string" ? value : JSON.stringify(value);
}

function numberText(value: number | undefined): string {
  return value === undefined ? "—" : value.toFixed(1).replace(/\.0$/, "");
}

function percentText(value: number | undefined): string {
  if (value === undefined) return "—";
  return `${value <= 1 ? Math.round(value * 100) : Math.round(value)}%`;
}

function decisionTone(
  value: ProcurementSupplierRiskResult["decision"],
): "neutral" | "success" | "warning" | "error" {
  if (value === "PASS") return "success";
  if (value === "BLOCK") return "error";
  return "warning";
}

function riskTone(value: string): "neutral" | "success" | "warning" | "error" {
  if (value === "A") return "success";
  if (value === "B" || value === "C") return "warning";
  if (value === "D") return "error";
  return "neutral";
}

function severityTone(value: string): "neutral" | "success" | "warning" | "error" {
  if (value === "BLOCKER" || value === "HIGH") return "error";
  if (value === "MEDIUM") return "warning";
  return "neutral";
}
