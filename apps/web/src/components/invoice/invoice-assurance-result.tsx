import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export const INVOICE_ASSURANCE_SCHEMA = "schema://invoice-assurance/result@1";

export type InvoiceAssuranceOutcome = "PAYMENT_READY" | "REVIEW_REQUIRED" | "PAYMENT_BLOCKED";

export type InvoiceAssuranceDimensionStatus =
  | "PASS"
  | "WARN"
  | "FAIL"
  | "UNKNOWN"
  | "NOT_APPLICABLE"
  | "OK"
  | "DATA_INSUFFICIENT"
  | "CONFLICTED";

export type InvoiceAssuranceDimension = {
  status?: string;
  summary?: string;
  reasons?: string[];
  severity?: string;
  evidenceRefs?: string[];
};

export type InvoiceAssuranceFinding = {
  findingId?: string;
  title?: string;
  detail?: string;
  severity?: string;
  status?: string;
  category?: string;
};

export type InvoiceAssuranceResult = {
  schemaVersion: typeof INVOICE_ASSURANCE_SCHEMA;
  title?: string;
  asOf?: string | null;
  outcome: string;
  score?: number | null;
  reviewRequired?: boolean;
  dimensions: Partial<Record<InvoiceAssuranceDimensionKey, InvoiceAssuranceDimension>>;
  findings?: InvoiceAssuranceFinding[];
  narrative?: { executiveSummary?: string; recommendations?: string[] } | string;
  resultHash?: string;
  provenance?: Record<string, unknown>;
  invoiceFactSet?: Record<string, unknown>;
  enterprisePublicStatus?: {
    status?: string;
    requiresHumanReview?: boolean;
    evidence?: { verifiedAt?: string; operator?: string; sourceUrl?: string };
  };
};

export type InvoiceAssuranceDimensionKey =
  | "officialVerification"
  | "faceCompliance"
  | "parties"
  | "commercialMatch"
  | "fulfillment"
  | "duplication"
  | "paymentGates";

const DIMENSION_ORDER: Array<{ key: InvoiceAssuranceDimensionKey; label: string }> = [
  { key: "officialVerification", label: "官方查验" },
  { key: "faceCompliance", label: "票面合规" },
  { key: "parties", label: "主体" },
  { key: "commercialMatch", label: "合同/订单" },
  { key: "fulfillment", label: "履约/验收" },
  { key: "duplication", label: "重复" },
  { key: "paymentGates", label: "付款条件" },
];

/** Mask bank account numbers for display, keeping only the last 4 digits. */
export function maskBankAccount(value: string): string {
  const digits = value.replace(/\D/g, "");
  if (!digits) return "****";
  if (digits.length <= 4) return `****${digits}`;
  return `****${digits.slice(-4)}`;
}

export function asInvoiceAssurance(value: unknown): InvoiceAssuranceResult | null {
  if (!value || typeof value !== "object") return null;
  const result = value as Partial<InvoiceAssuranceResult>;
  if (result.schemaVersion !== INVOICE_ASSURANCE_SCHEMA) return null;
  if (typeof result.outcome !== "string" || !result.dimensions || typeof result.dimensions !== "object") {
    return null;
  }
  return result as InvoiceAssuranceResult;
}

export function InvoiceAssuranceResultView({ result }: { result: InvoiceAssuranceResult }) {
  const narrativeText = narrativeSummary(result.narrative);
  const resultHash = stringValue(result.resultHash)
    ?? stringValue(result.provenance?.resultHash)
    ?? stringValue(result.provenance?.contentHash);
  const bankAccount = extractBankAccount(result.invoiceFactSet);
  const findings = Array.isArray(result.findings) ? result.findings : [];

  return (
    <div className="space-y-4" aria-label="发票一致性校验结果">
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">{result.title ?? "发票一致性校验"}</h2>
              <p className="mt-1 text-xs text-gray-500">评估时点 {result.asOf ?? "—"}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge color={outcomeColor(result.outcome)}>{result.outcome}</Badge>
              {typeof result.score === "number" ? <Badge color="neutral">得分 {result.score}</Badge> : null}
              {result.reviewRequired ? <Badge color="warning">需要人工复核</Badge> : null}
              {result.enterprisePublicStatus?.status ? (
                <Badge color={result.enterprisePublicStatus.status === "ACTIVE" ? "success" : "warning"}>
                  企业状态 {result.enterprisePublicStatus.status}
                </Badge>
              ) : null}
            </div>
          </div>
          <p className="text-sm leading-6 text-gray-600 dark:text-gray-300">
            {narrativeText ?? "已完成发票一致性校验。"}
          </p>
          {bankAccount ? (
            <p className="text-xs text-gray-500">
              收款账户 <span className="font-mono text-gray-800 dark:text-gray-200">{maskBankAccount(bankAccount)}</span>
            </p>
          ) : null}
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4" aria-label="校验维度">
            {DIMENSION_ORDER.map(({ key, label }) => {
              const dimension = result.dimensions[key];
              const status = dimension?.status ?? "未知";
              return (
                <article key={key} className="rounded-xl border border-gray-200 p-4 dark:border-gray-800">
                  <div className="flex items-center justify-between gap-2">
                    <h3 className="font-medium text-gray-900 dark:text-white">{label}</h3>
                    <Badge color={dimensionStatusColor(status)}>{status}</Badge>
                  </div>
                  {dimension?.summary ? (
                    <p className="mt-2 text-xs leading-5 text-gray-500">{dimension.summary}</p>
                  ) : null}
                  {dimension?.reasons?.length ? (
                    <p className="mt-2 text-xs leading-5 text-warning-600">{dimension.reasons.join("；")}</p>
                  ) : null}
                </article>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {findings.length ? (
        <Card>
          <CardContent className="space-y-4 p-5">
            <h2 className="font-semibold text-gray-900 dark:text-white">结果 Findings</h2>
            <ul className="space-y-3">
              {findings.map((finding, index) => (
                <li
                  key={finding.findingId ?? `finding-${index}`}
                  className="rounded-xl border border-gray-200 p-3 dark:border-gray-800"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    {finding.severity ? <Badge color="warning">{finding.severity}</Badge> : null}
                    {finding.status ? <Badge color="neutral">{finding.status}</Badge> : null}
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {finding.title ?? `风险项 ${index + 1}`}
                    </span>
                  </div>
                  {finding.detail ? <p className="mt-2 text-xs text-gray-500">{maskSensitiveText(finding.detail)}</p> : null}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardContent className="space-y-3 p-5">
          <h2 className="font-semibold text-gray-900 dark:text-white">溯源与哈希</h2>
          <dl className="grid gap-3 md:grid-cols-2">
            <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-800/60">
              <dt className="text-xs text-gray-500">resultHash</dt>
              <dd className="mt-1 break-all font-mono text-xs text-gray-800 dark:text-gray-200">{resultHash ?? "—"}</dd>
            </div>
            <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-800/60">
              <dt className="text-xs text-gray-500">provenance</dt>
              <dd className="mt-1 break-all font-mono text-xs text-gray-800 dark:text-gray-200">
                {provenanceSummary(result.provenance)}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}

function narrativeSummary(narrative: InvoiceAssuranceResult["narrative"]): string | null {
  if (typeof narrative === "string" && narrative.trim()) return narrative;
  if (narrative && typeof narrative === "object" && typeof narrative.executiveSummary === "string") {
    return narrative.executiveSummary;
  }
  return null;
}

function outcomeColor(outcome: string): "success" | "warning" | "error" | "neutral" {
  if (outcome === "PAYMENT_READY") return "success";
  if (outcome === "PAYMENT_BLOCKED") return "error";
  if (outcome === "REVIEW_REQUIRED") return "warning";
  return "neutral";
}

function dimensionStatusColor(status: string): "success" | "warning" | "error" | "neutral" {
  const normalized = status.toUpperCase();
  if (normalized === "PASS" || normalized === "OK") return "success";
  if (normalized === "FAIL" || normalized === "CONFLICTED") return "error";
  if (normalized === "WARN" || normalized === "UNKNOWN" || normalized === "DATA_INSUFFICIENT") return "warning";
  return "neutral";
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function extractBankAccount(factSet: Record<string, unknown> | undefined): string | null {
  if (!factSet) return null;
  const seller = factSet.seller;
  if (seller && typeof seller === "object") {
    const account = (seller as Record<string, unknown>).bankAccount
      ?? (seller as Record<string, unknown>).bankAccountNumber
      ?? (seller as Record<string, unknown>).accountNumber;
    if (typeof account === "string" && account.trim()) return account;
  }
  const direct = factSet.bankAccount ?? factSet.bankAccountNumber ?? factSet.payeeAccount;
  return typeof direct === "string" && direct.trim() ? direct : null;
}

/** Mask contiguous digit runs that look like bank accounts (12+ digits). */
export function maskSensitiveText(text: string): string {
  return text.replace(/\d[\d\s-]{10,}\d/g, (match) => maskBankAccount(match));
}

function provenanceSummary(provenance: Record<string, unknown> | undefined): string {
  if (!provenance || !Object.keys(provenance).length) return "—";
  const keys = ["configurationHash", "businessSnapshotHash", "documentContentHash", "attachmentManifestHash"]
    .map((key) => {
      const value = provenance[key];
      return typeof value === "string" && value ? `${key}=${value.slice(0, 12)}…` : null;
    })
    .filter(Boolean);
  return keys.length ? keys.join(" · ") : JSON.stringify(provenance).slice(0, 120);
}
