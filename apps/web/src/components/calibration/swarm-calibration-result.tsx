import { ExternalLink, GitBranch, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

type Evidence = {
  evidenceId: string;
  sourceType: string;
  sourceUrl: string;
  retrievedAt: string;
  contentHash: string;
  commitSha?: string | null;
  security?: { promptInjectionSuspected?: boolean; handling?: string };
};

type CalibrationResult = {
  schemaVersion: "schema://swarm-calibration/result@1";
  status: string;
  issue: {
    url: string;
    objective: string;
    repository: string;
    number: number;
    commitSha: string;
  };
  route: {
    recommendedRoute?: string;
    selectedRoute?: string;
    reasonCodes?: string[];
    runtimeAuthoritative?: boolean;
    fallback?: { used?: boolean; error?: string };
  };
  diagnosis: {
    summary?: string;
    rootCause?: string;
    impact?: string;
    fixMechanism?: string;
    verificationPlan?: string;
    confidence?: number;
    acceptanceMapping?: Array<{ criterion?: string; result?: string; evidenceRefs?: string[] }>;
  };
  quality: {
    decision: string;
    score: number;
    threshold: number;
    components: Record<string, number>;
    hardFailures?: string[];
    evidenceCoverage?: number;
    acceptanceCoverage?: number;
  };
  sandbox: {
    status?: string;
    reasonCode?: string;
    command?: string[];
    exitCode?: number | null;
    tests?: { passed?: number; failed?: number; skipped?: number };
  };
  evidence: Evidence[];
  provenance: { evidenceManifestHash?: string; generatedAt?: string; externalWritePerformed?: boolean };
  resultHash: string;
};

export function asSwarmCalibration(value: unknown): CalibrationResult | null {
  if (!value || typeof value !== "object") return null;
  const result = value as Partial<CalibrationResult>;
  return result.schemaVersion === "schema://swarm-calibration/result@1" ? result as CalibrationResult : null;
}

export function SwarmCalibrationResultView({ result }: { result: CalibrationResult }) {
  const qualityPassed = result.quality.decision === "PASS";
  const sandboxPassed = result.sandbox.status === "PASSED";
  return <div className="space-y-4">
    <section className="grid gap-3 md:grid-cols-4" aria-label="调度校准摘要">
      <Metric label="质量得分" value={`${result.quality.score} / 100`} />
      <Metric label="执行路由" value={result.route.selectedRoute ?? "—"} />
      <Metric label="运行验证" value={result.sandbox.status ?? "UNVERIFIED"} />
      <Metric label="最终状态" value={result.status} />
    </section>

    <Card><CardContent className="space-y-4 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold text-gray-900 dark:text-white">调度与质量门</h2>
          <p className="mt-1 text-xs text-gray-500">Runtime 决定主备路由；质量监督 Agent 只提供建议，确定性评分 Tool 形成最终门槛。</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge color={qualityPassed ? "success" : "warning"}>{result.quality.decision}</Badge>
          <Badge color={sandboxPassed ? "success" : "warning"}>{result.sandbox.status ?? "UNVERIFIED"}</Badge>
          {result.route.fallback?.used ? <Badge color="warning">已切换备用 Agent</Badge> : null}
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {Object.entries(result.quality.components).map(([key, score]) => (
          <div key={key} className="rounded-xl bg-gray-50 px-4 py-3 dark:bg-gray-800/60">
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="text-gray-600 dark:text-gray-300">{key}</span>
              <span className="font-semibold">{score}</span>
            </div>
          </div>
        ))}
      </div>
      {result.quality.hardFailures?.length ? <p role="alert" className="rounded-xl border border-warning-200 bg-warning-50 p-3 text-sm text-warning-700 dark:border-warning-500/20 dark:bg-warning-500/10 dark:text-warning-300">阻断原因：{result.quality.hardFailures.join("、")}</p> : null}
      <div className="rounded-xl border border-gray-200 p-3 text-xs text-gray-500 dark:border-gray-800">
        <p>推荐路由：{result.route.recommendedRoute ?? "—"} · 实际路由：{result.route.selectedRoute ?? "—"}</p>
        <p className="mt-1">依据：{result.route.reasonCodes?.join("、") || "运行时就绪状态与冻结策略"}</p>
      </div>
    </CardContent></Card>

    <Card><CardContent className="space-y-4 p-5">
      <div className="flex items-center gap-3">
        <ShieldCheck className="size-5 text-brand-600" />
        <div><h2 className="font-semibold text-gray-900 dark:text-white">业务结论与依据</h2><p className="mt-1 text-xs text-gray-500">{result.issue.repository}#{result.issue.number} · {result.issue.objective}</p></div>
      </div>
      <ResultBlock label="问题摘要" value={result.diagnosis.summary} />
      <ResultBlock label="根因" value={result.diagnosis.rootCause} />
      <ResultBlock label="影响" value={result.diagnosis.impact} />
      <ResultBlock label="修复机制" value={result.diagnosis.fixMechanism} />
      <ResultBlock label="验证计划" value={result.diagnosis.verificationPlan} />
    </CardContent></Card>

    <Card><CardContent className="space-y-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h2 className="font-semibold text-gray-900 dark:text-white">真实数据证据链</h2><p className="mt-1 text-xs text-gray-500">来源 URL、抓取时间、内容哈希与完整合并提交均冻结保存。</p></div>
        <Badge color="neutral"><GitBranch className="size-3.5" />{result.issue.commitSha.slice(0, 12)}</Badge>
      </div>
      <ul className="space-y-3">
        {result.evidence.map((item) => <li key={item.evidenceId} className="rounded-xl border border-gray-200 p-3 dark:border-gray-800">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2"><Badge color="neutral">{item.evidenceId}</Badge><span className="text-sm font-medium">{item.sourceType}</span></div>
            <a className="inline-flex items-center gap-1 text-xs text-brand-600 hover:underline" href={item.sourceUrl} target="_blank" rel="noreferrer">查看来源<ExternalLink className="size-3.5" /></a>
          </div>
          <p className="mt-2 break-all font-mono text-[11px] text-gray-500">SHA-256 {item.contentHash}</p>
          <p className="mt-1 text-xs text-gray-400">{item.retrievedAt}{item.security?.promptInjectionSuspected ? " · 检测到提示注入并按纯数据隔离" : ""}</p>
        </li>)}
      </ul>
      <div className="rounded-xl bg-gray-950 p-3 font-mono text-[11px] text-gray-200">
        <p>evidence-manifest: {result.provenance.evidenceManifestHash}</p>
        <p className="mt-1">result: {result.resultHash}</p>
      </div>
    </CardContent></Card>
  </div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-white/[0.03]"><p className="text-xs text-gray-500">{label}</p><p className="mt-1 truncate font-semibold text-gray-900 dark:text-white" title={value}>{value}</p></div>;
}

function ResultBlock({ label, value }: { label: string; value?: string }) {
  return <div><h3 className="text-sm font-medium text-gray-800 dark:text-gray-200">{label}</h3><p className="mt-1 text-sm leading-6 text-gray-600 dark:text-gray-300">{value || "未提供"}</p></div>;
}
