import { CheckCircle2, FileJson, FileText, ShieldCheck, Table2 } from "lucide-react";
import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export const DOCUMENT_STRUCTURING_SCHEMA = "schema://document-structuring/package@1";

type StructuredField = {
  fieldPath?: string;
  displayName?: string;
  effectiveValue?: unknown;
  machineValue?: unknown;
  confidence?: number;
  reviewStatus?: string;
  qualityFlags?: string[];
};

type StructuredDocument = {
  documentId?: string;
  documentVersionId?: string;
  filename?: string;
  mediaType?: string;
  sections?: unknown[];
  chunks?: unknown[];
  tables?: unknown[];
  fields?: StructuredField[];
  classification?: Record<string, unknown>;
  organization?: {
    buyer?: { name?: string | null };
    supplier?: { name?: string | null };
  };
  qualityFlags?: string[];
};

export type DocumentStructuringResult = {
  schemaVersion: typeof DOCUMENT_STRUCTURING_SCHEMA;
  status: string;
  summary?: string;
  reviewRequired?: boolean;
  qualityFlags?: string[];
  contentHash?: string;
  documents: StructuredDocument[];
  artifacts?: Array<{ artifactId?: string; filename?: string; downloadRef?: string }>;
  humanReview?: {
    decision?: string;
    reason?: string;
    correctionCount?: number;
  };
  provenance?: {
    runId?: string;
    evaluationId?: string;
    agentRef?: string;
  };
};

export function asDocumentStructuring(value: unknown): DocumentStructuringResult | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const result = value as Partial<DocumentStructuringResult>;
  if (result.schemaVersion !== DOCUMENT_STRUCTURING_SCHEMA || !Array.isArray(result.documents)) return null;
  return result as DocumentStructuringResult;
}

export function DocumentStructuringResultView({
  result,
}: {
  result: DocumentStructuringResult;
}) {
  const sectionCount = sum(result.documents, "sections");
  const chunkCount = sum(result.documents, "chunks");
  const tableCount = sum(result.documents, "tables");
  const artifacts = result.artifacts ?? [];

  return <div className="space-y-4">
    <section className="grid gap-3 md:grid-cols-5" aria-label="结构化结果摘要">
      <Metric label="文档" value={result.documents.length} icon={<FileText />} />
      <Metric label="章节" value={sectionCount} icon={<FileText />} />
      <Metric label="语义切片" value={chunkCount} icon={<FileJson />} />
      <Metric label="结构化表格" value={tableCount} icon={<Table2 />} />
      <Metric label="可交付产物" value={artifacts.length} icon={<CheckCircle2 />} />
    </section>

    <Card>
      <CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">文档结构化结论</h2>
            <p className="mt-2 max-w-5xl text-sm leading-6 text-gray-600 dark:text-gray-300">
              {result.summary ?? "文档已完成结构化处理。"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge color={result.status === "READY" ? "success" : "warning"}>{result.status}</Badge>
            {result.reviewRequired ? <Badge color="warning">需要人工复核</Badge> : <Badge color="success">复核已完成</Badge>}
          </div>
        </div>
        {(result.qualityFlags ?? []).length ? <div className="flex flex-wrap gap-2" aria-label="质量标记">
          {(result.qualityFlags ?? []).map((flag) => <Badge key={flag} color="warning">{qualityFlagLabel(flag)}</Badge>)}
        </div> : null}
      </CardContent>
    </Card>

    <div className="grid gap-4 xl:grid-cols-2">
      {result.documents.map((document, index) => {
        const classification = document.classification ?? {};
        const fields = (document.fields ?? []).filter((field) => displayFieldValue(field) !== "—");
        return <Card key={document.documentVersionId ?? document.documentId ?? index}>
          <CardContent className="space-y-4 p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate font-semibold text-gray-900 dark:text-white">
                  {document.filename ?? `文档 ${index + 1}`}
                </h3>
                <p className="mt-1 text-xs text-gray-500">{document.mediaType ?? "未知格式"}</p>
              </div>
              <Badge color="primary">{text(classification["businessType"]) ?? text(classification["label"]) ?? "已分类"}</Badge>
            </div>

            <dl className="grid gap-3 sm:grid-cols-2">
              <Fact label="合同类型" value={text(classification["contractType"]) ?? text(classification["documentSubtype"])} />
              <Fact label="框架编号" value={text(classification["frameworkReference"])} />
              <Fact label="适用法律" value={text(classification["governingLaw"])} />
              <Fact label="买方 / 供应商" value={`${document.organization?.buyer?.name ?? "模板待填写"} / ${document.organization?.supplier?.name ?? "模板待填写"}`} />
            </dl>

            {fields.length ? <div>
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">已抽取字段</h4>
              <dl className="mt-2 divide-y divide-gray-100 rounded-xl border border-gray-200 px-3 dark:divide-gray-800 dark:border-gray-800">
                {fields.slice(0, 8).map((field, fieldIndex) => <div key={`${field.fieldPath ?? fieldIndex}`} className="grid gap-1 py-2 sm:grid-cols-[minmax(0,12rem)_1fr]">
                  <dt className="text-xs text-gray-500">{field.displayName || field.fieldPath || `字段 ${fieldIndex + 1}`}</dt>
                  <dd className="break-words text-xs text-gray-800 dark:text-gray-200">{displayFieldValue(field)}</dd>
                </div>)}
              </dl>
            </div> : null}
          </CardContent>
        </Card>;
      })}
    </div>

    <div className="grid gap-4 xl:grid-cols-2">
      <Card>
        <CardContent className="space-y-3 p-5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-5 text-brand-600" />
            <h2 className="font-semibold text-gray-900 dark:text-white">人工复核</h2>
          </div>
          {result.humanReview ? <>
            <div className="flex flex-wrap gap-2">
              <Badge color={result.humanReview.decision === "CONFIRM" ? "success" : "warning"}>
                {result.humanReview.decision ?? "已处理"}
              </Badge>
              <Badge color="neutral">修正 {result.humanReview.correctionCount ?? 0} 项</Badge>
            </div>
            <p className="text-sm leading-6 text-gray-600 dark:text-gray-300">{result.humanReview.reason ?? "复核已完成。"}</p>
          </> : <p className="text-sm text-gray-500">无人工复核记录。</p>}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-3 p-5">
          <h2 className="font-semibold text-gray-900 dark:text-white">交付产物</h2>
          {artifacts.length ? <ul className="grid gap-2 sm:grid-cols-2">
            {artifacts.map((artifact, index) => <li key={artifact.artifactId ?? index} className="flex min-w-0 items-center gap-2 rounded-xl border border-gray-200 px-3 py-2 dark:border-gray-800">
              <FileJson className="size-4 shrink-0 text-brand-600" />
              <span className="truncate text-xs text-gray-700 dark:text-gray-300">{artifact.filename ?? `产物 ${index + 1}`}</span>
            </li>)}
          </ul> : <p className="text-sm text-gray-500">暂无交付产物。</p>}
          {result.contentHash ? <p className="break-all font-mono text-[11px] text-gray-500">contentHash: {result.contentHash}</p> : null}
        </CardContent>
      </Card>
    </div>
  </div>;
}

function Metric({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: ReactNode;
}) {
  return <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-theme-xs dark:border-gray-800 dark:bg-white/[0.03]">
    <div className="flex items-center justify-between text-gray-500">
      <span className="text-xs">{label}</span>
      <span className="[&>svg]:size-4">{icon}</span>
    </div>
    <p className="mt-2 text-xl font-semibold text-gray-900 dark:text-white">{value}</p>
  </div>;
}

function Fact({ label, value }: { label: string; value?: string | null }) {
  return <div className="rounded-xl bg-gray-50 p-3 dark:bg-white/[0.04]">
    <dt className="text-xs text-gray-500">{label}</dt>
    <dd className="mt-1 text-sm text-gray-900 dark:text-white">{value || "—"}</dd>
  </div>;
}

function sum(documents: StructuredDocument[], key: "sections" | "chunks" | "tables") {
  return documents.reduce((total, document) => total + (document[key]?.length ?? 0), 0);
}

function text(value: unknown) {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function displayFieldValue(field: StructuredField) {
  const value = field.effectiveValue ?? field.machineValue;
  if (value == null || value === "") return "—";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function qualityFlagLabel(flag: string) {
  const labels: Record<string, string> = {
    DOCUMENT_IS_TEMPLATE: "模板文档",
    EXTRACTION_REVIEW_REQUIRED: "抽取结果已复核",
    PLACEHOLDER_VALUES_NORMALIZED: "占位字段已规范为空",
    AGENT_DOCUMENT_RESULT_MISSING: "Agent 结果缺失",
    AGENT_OUTPUT_SCHEMA_INVALID: "Agent 输出契约异常",
  };
  return labels[flag] ?? flag;
}
