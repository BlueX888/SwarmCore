import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, CircleAlert, Download, FileText, LoaderCircle, Table2, Upload, X } from "lucide-react";
import { ApiError, api } from "@/api/client";
import type {
  DocumentRequirementSnapshot,
  DocumentSnapshot,
  UploadBatchSnapshot,
} from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const fieldClass =
  "h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900";

export type DocumentUploadContext = {
  businessWorkKey?: string;
  businessObjectIds?: string[];
  caseId?: string | null;
  processingProfileRef?: string;
  extractionSchemaRef?: string;
  classificationLabels?: Array<{ label: string; displayName?: string }>;
  businessWorkKeys?: string[];
  category?: string;
};

async function sha256File(file: File) {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
}

function uploadErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return "上传服务接口不可用。请确认 API 已重启并完成数据库迁移（0014/0015）。";
    }
    if (error.status >= 500) {
      return "上传处理失败（服务器错误）。若刚更新代码，请确认已执行数据库迁移并重启 API。";
    }
    if (error.message && error.message !== "Not Found" && !error.message.startsWith("<!")) {
      return error.message;
    }
  }
  if (error instanceof Error && error.message && error.message !== "Not Found" && error.message !== "Internal Server Error") {
    return error.message;
  }
  return "上传失败，请稍后重试。";
}

export function DocumentUploadPanel({
  tenantId,
  projectId,
  context,
  onClose,
  onCompleted,
  multiple = true,
}: {
  tenantId: string;
  projectId: string;
  context?: DocumentUploadContext;
  onClose?: () => void;
  onCompleted?: (documents: DocumentSnapshot[]) => Promise<void> | void;
  multiple?: boolean;
}) {
  const [files, setFiles] = useState<File[]>([]);
  const [batch, setBatch] = useState<UploadBatchSnapshot | null>(null);
  const [progress, setProgress] = useState<Array<{ name: string; status: string; error?: string }>>([]);
  const upload = useMutation({
    mutationFn: async () => {
      if (!files.length) throw new Error("请选择要上传的文件。");
      let batchId: string | undefined;
      try {
        const created = await api.createUploadBatch(tenantId, projectId, {
          source: "web",
          context: {
            businessWorkKey: context?.businessWorkKey,
            businessObjectIds: context?.businessObjectIds ?? [],
            caseId: context?.caseId ?? null,
            processingProfileRef: context?.processingProfileRef,
            extractionSchemaRef: context?.extractionSchemaRef,
            classificationLabels: context?.classificationLabels ?? [],
          },
        });
        batchId = created.batchId;
        setBatch(created);
      } catch {
        // Batch tracking is optional; keep uploading through the existing document APIs.
        batchId = undefined;
        setBatch(null);
      }
      const uploaded: DocumentSnapshot[] = [];
      const nextProgress: Array<{ name: string; status: string; error?: string }> = [];
      for (const file of files) {
        nextProgress.push({ name: file.name, status: "上传中" });
        setProgress([...nextProgress]);
        try {
          const digest = await sha256File(file);
          const handle = await api.initiateDocument(tenantId, projectId, {
            name: file.name,
            category: context?.category || context?.classificationLabels?.[0]?.label || "OTHER",
            tags: [],
            filename: file.name,
            mediaType: file.type || "application/octet-stream",
            sizeBytes: file.size,
            sha256: digest,
            businessObjectIds: context?.businessObjectIds ?? [],
            businessWorkKeys: context?.businessWorkKeys
              ?? (context?.businessWorkKey ? [context.businessWorkKey] : []),
          });
          await api.uploadDocumentContent(handle, file);
          const document = await api.completeDocument(tenantId, projectId, handle.uploadId, digest, {
            uploadBatchId: batchId,
            profileRef: context?.processingProfileRef,
            extractionSchemaRef: context?.extractionSchemaRef,
            classificationLabels: context?.classificationLabels,
          });
          uploaded.push(document);
          nextProgress[nextProgress.length - 1] = { name: file.name, status: "已完成" };
        } catch (error) {
          nextProgress[nextProgress.length - 1] = {
            name: file.name,
            status: "失败",
            error: uploadErrorMessage(error),
          };
        }
        setProgress([...nextProgress]);
      }
      if (batchId) {
        try {
          const latest = await api.getUploadBatch(tenantId, projectId, batchId);
          setBatch(latest);
        } catch {
          // Ignore batch status refresh failures after files already uploaded.
        }
      }
      if (!uploaded.length) {
        const firstError = nextProgress.find((item) => item.error)?.error;
        throw new Error(firstError || "所有文件上传失败。");
      }
      return uploaded;
    },
    onSuccess: async (documents) => {
      await onCompleted?.(documents);
    },
  });

  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">上传业务资料</h2>
            <p className="mt-1 text-sm text-gray-500">支持多文件拖拽上传。系统会自动解析、分类并抽取字段，无需编辑 JSON。</p>
          </div>
          {onClose ? <Button variant="ghost" size="icon" aria-label="关闭上传" onClick={onClose}><X /></Button> : null}
        </div>
        <label className="block rounded-xl border border-dashed border-gray-300 p-5 text-sm dark:border-gray-700">
          <span className="font-medium text-gray-800 dark:text-gray-200">选择文件{multiple ? "（可多选）" : ""}</span>
          <input
            aria-label="选择业务资料文件"
            type="file"
            multiple={multiple}
            className="mt-3 block w-full text-sm text-gray-500 file:mr-3 file:rounded-lg file:border-0 file:bg-brand-50 file:px-3 file:py-2 file:text-brand-700"
            onChange={(event) => {
              setFiles(Array.from(event.target.files ?? []));
              setProgress([]);
              upload.reset();
            }}
          />
          {files.length ? (
            <span className="mt-2 block text-xs text-gray-500">
              已选择 {files.length} 个文件：{files.map((file) => file.name).join("、")}
            </span>
          ) : (
            <span className="mt-2 block text-xs text-gray-500">支持 ODT、ODS、ODP、PDF、DOCX、XLSX、PPTX、CSV、JSON、文本和常见图片</span>
          )}
        </label>
        <UploadBatchProgress batch={batch} items={progress} />
        {upload.isError ? <p role="alert" className="text-sm text-error-600">{uploadErrorMessage(upload.error)}</p> : null}
        <div className="flex justify-end gap-2">
          {onClose ? <Button variant="outline" onClick={onClose}>取消</Button> : null}
          <Button loading={upload.isPending} disabled={!files.length} onClick={() => upload.mutate()}>
            <Upload />开始上传
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function UploadBatchProgress({
  batch,
  items,
}: {
  batch: UploadBatchSnapshot | null;
  items: Array<{ name: string; status: string; error?: string }>;
}) {
  if (!batch && !items.length) return null;
  return (
    <div className="space-y-2 rounded-xl border border-gray-200 p-4 text-sm dark:border-gray-800">
      {batch ? (
        <p className="text-gray-600 dark:text-gray-300">
          批次 {batch.status} · 成功 {batch.succeededCount} / 失败 {batch.failedCount} / 总计 {batch.fileCount || items.length}
        </p>
      ) : null}
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item.name} className="flex items-center justify-between gap-3">
            <span className="truncate">{item.name}</span>
            <span className={item.status === "失败" ? "text-error-600" : "text-gray-500"}>
              {item.status}{item.error ? `：${item.error}` : ""}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function DocumentRequirementChecklist({
  items,
}: {
  items: DocumentRequirementSnapshot[];
}) {
  if (!items.length) {
    return <p className="text-sm text-gray-500">当前业务工作没有额外资料要求。</p>;
  }
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.key}
          className={`rounded-lg border p-3 text-sm ${item.satisfied ? "border-success-200 bg-success-50/60 dark:border-success-500/20" : "border-warning-200 bg-warning-50/50 dark:border-warning-500/20"}`}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">{item.displayName}</p>
              <p className="mt-1 text-xs text-gray-500">{item.description || (item.required ? "必需资料" : "建议资料")}</p>
            </div>
            <span className="text-xs text-gray-600 dark:text-gray-300">
              {item.satisfiedCount}/{item.minCount}{item.satisfied ? " 已满足" : " 未满足"}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function DocumentProcessingStatus({
  tenantId,
  projectId,
  documentId,
}: {
  tenantId: string;
  projectId: string;
  documentId: string;
}) {
  const processing = useQuery({
    queryKey: ["document-processing", tenantId, projectId, documentId],
    queryFn: () => api.getDocumentProcessing(tenantId, projectId, documentId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ["READY", "FAILED", "CANCELLED", "REVIEW_REQUIRED"].includes(status) ? false : 2000;
    },
    retry: false,
  });
  const events = useQuery({
    queryKey: ["document-processing-events", tenantId, projectId, documentId],
    queryFn: () => api.getDocumentProcessingEvents(tenantId, projectId, documentId),
    enabled: Boolean(processing.data),
    refetchInterval: () => {
      const status = processing.data?.status;
      return status && ["READY", "FAILED", "CANCELLED", "REVIEW_REQUIRED"].includes(status) ? false : 2000;
    },
    retry: false,
  });
  const result = useQuery({
    queryKey: ["document-processing-result", tenantId, projectId, documentId],
    queryFn: () => api.getDocumentProcessingResult(tenantId, projectId, documentId),
    enabled: Boolean(processing.data && ["READY", "REVIEW_REQUIRED"].includes(processing.data.status)),
    retry: false,
  });
  const structured = useQuery({
    queryKey: ["document-structured-package", tenantId, projectId, documentId],
    queryFn: () => api.getDocumentStructuredPackage(tenantId, projectId, documentId),
    enabled: processing.data?.status === "READY",
    retry: false,
  });
  const cancel = useMutation({
    mutationFn: () => api.cancelDocumentProcessing(tenantId, projectId, documentId),
    onSuccess: async () => {
      await Promise.all([processing.refetch(), events.refetch()]);
    },
  });
  if (processing.isError) {
    return <p className="text-sm text-gray-500">暂无处理进度。</p>;
  }
  if (processing.isPending || !processing.data) {
    return <p className="inline-flex items-center gap-2 text-sm text-gray-500"><LoaderCircle className="size-4 animate-spin" />加载处理状态…</p>;
  }
  const Icon = processing.data.status === "READY" ? Check : processing.data.status === "FAILED" ? CircleAlert : LoaderCircle;
  const plan = (
    processing.data.provenance?.processingPlan
    && typeof processing.data.provenance.processingPlan === "object"
  ) ? processing.data.provenance.processingPlan as Record<string, unknown> : null;
  const content = result.data?.result.content;
  const packageResult = structured.data?.result;
  const artifacts = packageResult?.artifacts ?? result.data?.result.artifacts ?? [];
  return (
    <div className="space-y-4 rounded-lg border border-gray-200 p-4 text-sm dark:border-gray-800">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="inline-flex items-center gap-2 font-medium text-gray-800 dark:text-gray-200">
            <Icon className={`size-4 ${!["READY", "FAILED", "CANCELLED", "REVIEW_REQUIRED"].includes(processing.data.status) ? "animate-spin" : ""}`} />
            {processing.data.stageLabel}
          </p>
          <p className="mt-1 text-xs text-gray-500">
            第 {processing.data.attempt} 次处理 · {processing.data.profileRef}
            {processing.data.errorDetail ? ` · ${processing.data.errorDetail}` : ""}
          </p>
        </div>
        {!["READY", "FAILED", "CANCELLED", "REVIEW_REQUIRED"].includes(processing.data.status) ? (
          <Button
            size="sm"
            variant="outline"
            loading={cancel.isPending}
            onClick={() => cancel.mutate()}
          >
            <X />取消处理
          </Button>
        ) : null}
      </div>
      {cancel.isError ? <p role="alert" className="text-xs text-error-600">{cancel.error.message}</p> : null}
      {plan ? (
        <div className="grid gap-2 sm:grid-cols-4">
          <Metric label="处理路径" value={plan.largeDocument ? "大文件分片" : "普通文件"} />
          <Metric label="页数" value={displayScalar(plan.pageCount)} />
          <Metric label="页组" value={displayScalar(plan.groupCount ?? (Array.isArray(plan.pageBatches) ? plan.pageBatches.length : undefined))} />
          <Metric label="最大并行" value={displayScalar(plan.maxParallelism)} />
        </div>
      ) : null}
      {events.data?.items.length ? (
        <div>
          <p className="mb-2 font-medium text-gray-800 dark:text-gray-200">处理过程与依据</p>
          <ol className="space-y-2 border-l border-gray-200 pl-4 dark:border-gray-700">
            {events.data.items.slice(-12).map((event) => (
              <li key={event.eventId}>
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {event.eventSeq}. {event.type} · {event.stage}
                </p>
                <p className="mt-0.5 text-[11px] text-gray-500">
                  {event.toolRef || "系统"}
                  {event.outputHash ? ` · 输出 ${event.outputHash.slice(0, 12)}…` : ""}
                  {` · ${new Date(event.occurredAt).toLocaleString()}`}
                </p>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
      {content ? (
        <div className="grid gap-2 sm:grid-cols-3">
          <Metric icon={<FileText className="size-4" />} label="章节 / 切片" value={`${content.sections?.length ?? 0} / ${content.chunks?.length ?? 0}`} />
          <Metric icon={<Table2 className="size-4" />} label="表格 / 工作表" value={`${content.tables?.length ?? 0} / ${content.sheets?.length ?? 0}`} />
          <Metric label="质量标记" value={String(result.data?.result.qualityFlags?.length ?? 0)} />
        </div>
      ) : null}
      {artifacts.length ? (
        <div>
          <p className="mb-2 font-medium text-gray-800 dark:text-gray-200">结构化产物</p>
          <ul className="grid gap-2 sm:grid-cols-2">
            {artifacts.map((artifact, index) => {
              const artifactId = typeof artifact.artifactId === "string" ? artifact.artifactId : null;
              const filename = typeof artifact.filename === "string"
                ? artifact.filename
                : (typeof artifact.kind === "string" ? artifact.kind : `产物 ${index + 1}`);
              const artifactRef = typeof artifact.artifactRef === "string" ? artifact.artifactRef : "";
              return (
                <li key={`${artifactId ?? filename}-${index}`} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-900">
                  <span className="truncate text-xs">{filename}</span>
                  {artifactId ? (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        void api.downloadArtifact(tenantId, projectId, artifactId).then((blob) => {
                          const url = URL.createObjectURL(blob);
                          const anchor = document.createElement("a");
                          anchor.href = url;
                          anchor.download = filename;
                          anchor.click();
                          URL.revokeObjectURL(url);
                        });
                      }}
                    >
                      <Download />下载
                    </Button>
                  ) : <span className="text-xs text-gray-400">{artifactRef}</span>}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function Metric({ label, value, icon }: { label: string; value: string; icon?: ReactNode }) {
  return (
    <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-900">
      <p className="flex items-center gap-1 text-xs text-gray-500">{icon}{label}</p>
      <p className="mt-1 font-medium text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

function displayScalar(value: unknown): string {
  return typeof value === "string" || typeof value === "number" ? String(value) : "—";
}

export function DocumentClassificationReview({
  tenantId,
  projectId,
  documentId,
  onConfirmed,
}: {
  tenantId: string;
  projectId: string;
  documentId: string;
  onConfirmed?: () => Promise<void> | void;
}) {
  const result = useQuery({
    queryKey: ["document-processing-result", tenantId, projectId, documentId],
    queryFn: () => api.getDocumentProcessingResult(tenantId, projectId, documentId),
    retry: false,
  });
  const [label, setLabel] = useState("");
  const [notice, setNotice] = useState("");
  const confirm = useMutation({
    mutationFn: async () => {
      if (!result.data) throw new Error("处理结果尚未就绪");
      const next = label.trim() || result.data.result.documentType?.label || "";
      if (!next) throw new Error("请选择或输入分类");
      return api.confirmDocumentClassification(tenantId, projectId, documentId, {
        label: next,
        displayName: next,
        expectedResultVersion: result.data.resultVersion,
      });
    },
    onSuccess: async () => {
      setNotice("分类已确认保存。");
      await result.refetch();
      await onConfirmed?.();
    },
  });
  const documentType = result.data?.result.documentType;
  const options = useMemo(() => {
    const values = [
      ...(documentType?.label ? [{ label: documentType.label, displayName: documentType.displayName }] : []),
      ...(documentType?.alternatives ?? []),
    ];
    return values;
  }, [documentType]);
  if (result.isError) return <p className="text-sm text-gray-500">暂无分类结果。</p>;
  if (!documentType) {
    return (
      <div className="space-y-2 rounded-lg border border-warning-200 bg-warning-50/40 p-4 text-sm dark:border-warning-500/20">
        <p className="font-medium text-gray-900 dark:text-white">文档分类待确认</p>
        <p className="text-xs text-gray-500">当前没有可用的机器分类（例如未配置 OCR 的扫描件）。请重新处理或补充分类后再确认。</p>
      </div>
    );
  }
  return (
    <div className="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
      <div>
        <p className="text-sm font-medium text-gray-900 dark:text-white">文档分类</p>
        <p className="mt-1 text-xs text-gray-500">
          机器结果：{documentType.displayName || documentType.label}（置信度 {Math.round((documentType.confidence ?? 0) * 100)}%）
          {documentType.confirmedLabel ? ` · 已确认 ${documentType.confirmedLabel}` : " · 确认后才可变为可用"}
        </p>
      </div>
      <select
        aria-label="确认文档分类"
        className={fieldClass}
        value={label || documentType.confirmedLabel || documentType.label || ""}
        onChange={(event) => {
          setLabel(event.target.value);
          setNotice("");
        }}
      >
        {options.map((item) => <option key={item.label} value={item.label}>{item.displayName || item.label}</option>)}
      </select>
      <Button size="sm" loading={confirm.isPending} onClick={() => confirm.mutate()}>确认分类</Button>
      {notice ? <p role="status" className="rounded-lg bg-success-50 p-2 text-sm text-success-700 dark:bg-success-500/10 dark:text-success-400">{notice}</p> : null}
      {confirm.isError ? <p role="alert" className="text-sm text-error-600">{confirm.error.message}</p> : null}
    </div>
  );
}

export function DocumentExtractionReviewForm({
  tenantId,
  projectId,
  documentId,
  onConfirmed,
}: {
  tenantId: string;
  projectId: string;
  documentId: string;
  onConfirmed?: () => Promise<void> | void;
}) {
  const result = useQuery({
    queryKey: ["document-processing-result", tenantId, projectId, documentId],
    queryFn: () => api.getDocumentProcessingResult(tenantId, projectId, documentId),
    retry: false,
  });
  const [values, setValues] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState("");
  const confirm = useMutation({
    mutationFn: async (acceptHighConfidence: boolean) => {
      if (!result.data) throw new Error("处理结果尚未就绪");
      const fields = (result.data.result.extractions ?? []).map((field) => ({
        fieldPath: field.fieldPath,
        confirmedValue: values[field.fieldPath] ?? stringifyFieldValue(field.confirmedValue ?? field.value),
      }));
      return api.confirmDocumentFields(tenantId, projectId, documentId, {
        fields,
        acceptHighConfidence,
        expectedResultVersion: result.data.resultVersion,
      });
    },
    onSuccess: async (_data, acceptHighConfidence) => {
      setNotice(acceptHighConfidence ? "高置信度字段已确认保存。" : "字段确认已保存。");
      await result.refetch();
      await onConfirmed?.();
    },
  });
  const fields = result.data?.result.extractions ?? [];
  if (result.isError) return <p className="text-sm text-gray-500">暂无抽取结果。</p>;
  if (!fields.length) return <p className="text-sm text-gray-500">当前文件没有待确认字段。若分类已确认，状态会变为可用。</p>;
  return (
    <div className="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-gray-900 dark:text-white">字段确认</p>
        <Button size="sm" variant="outline" loading={confirm.isPending} onClick={() => confirm.mutate(true)}>批量确认高置信度</Button>
      </div>
      {fields.map((field) => (
        <label key={field.fieldPath} className="block text-xs font-medium text-gray-700 dark:text-gray-300">
          {field.displayName}
          <span className="ml-2 font-normal text-gray-500">置信度 {Math.round(field.confidence * 100)}% · 机器值保留不可覆盖</span>
          <input
            aria-label={field.displayName}
            className={`mt-2 ${fieldClass}`}
            value={values[field.fieldPath] ?? stringifyFieldValue(field.confirmedValue ?? field.value)}
            onChange={(event) => {
              setNotice("");
              setValues((current) => ({ ...current, [field.fieldPath]: event.target.value }));
            }}
          />
          <DocumentEvidenceViewer evidence={field.evidenceRefs} />
        </label>
      ))}
      <Button size="sm" loading={confirm.isPending} onClick={() => confirm.mutate(false)}>保存字段确认</Button>
      {notice ? <p role="status" className="rounded-lg bg-success-50 p-2 text-sm text-success-700 dark:bg-success-500/10 dark:text-success-400">{notice}</p> : null}
      {confirm.isError ? <p role="alert" className="text-sm text-error-600">{confirm.error.message}</p> : null}
    </div>
  );
}

export function DocumentEvidenceViewer({ evidence }: { evidence: Array<Record<string, unknown>> }) {
  if (!evidence.length) return null;
  return (
    <ul className="mt-2 space-y-1 text-xs font-normal text-gray-500">
      {evidence.slice(0, 3).map((item, index) => {
        const page = typeof item.page === "number" || typeof item.page === "string" ? String(item.page) : null;
        const text = typeof item.text === "string" ? item.text : JSON.stringify(item);
        return (
          <li key={`${page ?? index}-${text.slice(0, 24)}`}>
            证据{page ? ` · 第 ${page} 页` : ""}：{text.slice(0, 120)}
          </li>
        );
      })}
    </ul>
  );
}

function stringifyFieldValue(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

export function DocumentBindingEditor({
  tenantId,
  projectId,
  document,
  workOptions,
  onSaved,
}: {
  tenantId: string;
  projectId: string;
  document: DocumentSnapshot;
  workOptions: Array<{ key: string; label: string }>;
  onSaved?: () => Promise<void> | void;
}) {
  const [workKeys, setWorkKeys] = useState(document.businessWorkKeys);
  const [notice, setNotice] = useState("");
  const save = useMutation({
    mutationFn: () => api.updateDocumentBindings(tenantId, projectId, document.documentId, {
      businessObjectIds: document.businessObjectIds,
      businessWorkKeys: workKeys,
    }),
    onSuccess: async () => {
      setNotice("绑定已保存成功。");
      await onSaved?.();
    },
  });
  return (
    <div className="space-y-3 rounded-lg border border-gray-200 p-4 dark:border-gray-800">
      <div>
        <p className="text-sm font-medium text-gray-900 dark:text-white">业务绑定</p>
        <p className="mt-1 text-xs text-gray-500">只关联业务工作，不会改变「需确认 / 可用」处理状态。</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {workOptions.map((work) => (
          <label key={work.key} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={workKeys.includes(work.key)}
              onChange={() => {
                setNotice("");
                setWorkKeys((current) => current.includes(work.key) ? current.filter((value) => value !== work.key) : [...current, work.key]);
              }}
            />
            {work.label}
          </label>
        ))}
      </div>
      <Button size="sm" loading={save.isPending} onClick={() => save.mutate()}>保存绑定</Button>
      {notice ? <p role="status" className="rounded-lg bg-success-50 p-2 text-sm text-success-700 dark:bg-success-500/10 dark:text-success-400">{notice}</p> : null}
      {save.isError ? <p role="alert" className="text-sm text-error-600">{save.error.message}</p> : null}
    </div>
  );
}

export function DocumentPicker({
  items,
  selectedIds,
  onChange,
}: {
  items: DocumentSnapshot[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}) {
  return (
    <ul className="space-y-2">
      {items.map((item) => {
        const checked = selectedIds.includes(item.documentId);
        return (
          <li key={item.documentId}>
            <label className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm ${checked ? "border-brand-400 bg-brand-50/50" : "border-gray-200 dark:border-gray-800"}`}>
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onChange(checked ? selectedIds.filter((id) => id !== item.documentId) : [...selectedIds, item.documentId])}
              />
              <span>
                <span className="block font-medium text-gray-900 dark:text-white">{item.name}</span>
                <span className="mt-1 block text-xs text-gray-500">{item.status} · {item.category}</span>
              </span>
            </label>
          </li>
        );
      })}
    </ul>
  );
}
