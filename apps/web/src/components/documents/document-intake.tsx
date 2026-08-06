import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Check,
  CircleAlert,
  Download,
  FileText,
  Link2,
  ListChecks,
  LoaderCircle,
  Table2,
  Tags,
  Upload,
  X,
} from "lucide-react";
import { ApiError, api } from "@/api/client";
import type {
  DocumentProcessingEventSnapshot,
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
  const eventItems = events.data?.items ?? [];
  const eventStages = new Set(eventItems.map((event) => event.stage));
  const isReady = processing.data.status === "READY" || eventStages.has("READY");
  const isReviewRequired = !isReady
    && (processing.data.status === "REVIEW_REQUIRED" || eventStages.has("REVIEW_REQUIRED"));
  const isFailed = processing.data.status === "FAILED";
  const isCancelled = processing.data.status === "CANCELLED";
  const isTerminal = isReady || isReviewRequired || isFailed || isCancelled;
  const Icon = isReady ? Check : isFailed ? CircleAlert : LoaderCircle;
  const statusTitle = isReady
    ? "处理完成"
    : isReviewRequired
      ? "自动处理完成，待确认"
      : isCancelled
        ? "处理已取消"
        : processing.data.stageLabel;
  const statusDescription = isReady
    ? "文件内容已完成解析与确认，可以用于后续业务。"
    : isReviewRequired
      ? "系统已完成识别，请确认下方的文档分类和字段。"
      : isFailed
        ? (processing.data.errorDetail || "处理未完成，请重新处理。")
        : isCancelled
          ? "本次处理已取消，可重新发起处理。"
          : "系统正在解析文件，请稍候。";
  const plan = (
    processing.data.provenance?.processingPlan
    && typeof processing.data.provenance.processingPlan === "object"
  ) ? processing.data.provenance.processingPlan as Record<string, unknown> : null;
  const content = result.data?.result.content;
  const packageResult = structured.data?.result;
  const artifacts = packageResult?.artifacts ?? result.data?.result.artifacts ?? [];
  return (
    <div className="space-y-4 rounded-xl border border-gray-200 p-4 text-sm dark:border-gray-800">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="inline-flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
            <Icon className={`size-4 ${!isTerminal ? "animate-spin" : ""}`} />
            {statusTitle}
          </p>
          <p className="mt-1 text-xs leading-5 text-gray-500">{statusDescription}</p>
        </div>
        {!isTerminal ? (
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
      {eventItems.length ? (
        <ProcessingProgress
          events={eventItems}
          currentStage={processing.data.currentStage}
          ready={isReady}
          reviewRequired={isReviewRequired}
          attempt={processing.data.attempt}
          profileRef={processing.data.profileRef}
          plan={plan}
        />
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

const automaticProcessingSteps = [
  { key: "scan", label: "安全检查", stages: ["SCANNING"] },
  { key: "parse", label: "内容解析", stages: ["PARSING"] },
  { key: "classify", label: "分类识别", stages: ["CLASSIFYING"] },
  { key: "extract", label: "字段提取", stages: ["EXTRACTING"] },
  { key: "quality", label: "质量校验", stages: ["QUALITY_CHECK"] },
] as const;

function ProcessingProgress({
  events,
  currentStage,
  ready,
  reviewRequired,
  attempt,
  profileRef,
  plan,
}: {
  events: DocumentProcessingEventSnapshot[];
  currentStage: string;
  ready: boolean;
  reviewRequired: boolean;
  attempt: number;
  profileRef: string;
  plan: Record<string, unknown> | null;
}) {
  const stages = new Set(events.map((event) => event.stage));
  const steps = [
    ...automaticProcessingSteps.map((step) => ({
      ...step,
      complete: step.stages.some((stage) => stages.has(stage)),
      active: step.stages.some((stage) => stage === currentStage),
    })),
    {
      key: "review",
      label: ready ? "确认完成" : "人工确认",
      complete: ready,
      active: reviewRequired,
    },
  ];
  return (
    <div className="space-y-3">
      <p className="text-xs font-medium text-gray-700 dark:text-gray-300">处理进度</p>
      <ol className="grid grid-cols-2 gap-x-3 gap-y-3 sm:grid-cols-3 lg:grid-cols-6">
        {steps.map((step, index) => (
          <li key={step.key} className="flex items-center gap-2">
            <span
              className={`grid size-6 shrink-0 place-items-center rounded-full text-[11px] font-semibold ${
                step.complete
                  ? "bg-success-50 text-success-700 dark:bg-success-500/10 dark:text-success-300"
                  : step.active
                    ? "bg-brand-50 text-brand-600 ring-1 ring-brand-200 dark:bg-brand-500/10 dark:text-brand-300 dark:ring-brand-500/20"
                    : "bg-gray-100 text-gray-400 dark:bg-gray-800"
              }`}
            >
              {step.complete ? <Check className="size-3.5" /> : index + 1}
            </span>
            <span className={`text-xs ${step.complete || step.active ? "font-medium text-gray-700 dark:text-gray-300" : "text-gray-400"}`}>
              {step.label}
            </span>
          </li>
        ))}
      </ol>
      <details className="group border-t border-gray-100 pt-3 dark:border-gray-800">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
          <span>查看处理记录（{events.length} 条）</span>
          <span className="text-[11px]">用于审计与问题排查</span>
        </summary>
        <div className="mt-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-900">
          <p className="mb-3 text-[11px] text-gray-500">
            第 {attempt} 次处理 · 处理方案 {profileRef}
            {plan ? ` · ${processingPlanLabel(plan)}` : ""}
          </p>
          <ol className="space-y-2">
            {events.slice(-12).map((event) => (
              <li key={event.eventId} className="flex items-start justify-between gap-4 text-xs">
                <div className="min-w-0">
                  <p className="font-medium text-gray-700 dark:text-gray-300">{processingEventLabel(event)}</p>
                  <p className="mt-0.5 truncate text-[11px] text-gray-400" title={event.toolRef || event.type}>
                    {event.toolRef || "系统处理"}{event.outputHash ? ` · 校验 ${event.outputHash.slice(0, 8)}…` : ""}
                  </p>
                </div>
                <time className="shrink-0 text-[11px] text-gray-400" dateTime={event.occurredAt}>
                  {new Date(event.occurredAt).toLocaleString("zh-CN")}
                </time>
              </li>
            ))}
          </ol>
        </div>
      </details>
    </div>
  );
}

const processingEventLabels: Record<string, string> = {
  "document.processing.started": "开始处理文件",
  "document.scan.completed": "安全检查完成",
  "document.type.detected": "文件类型识别完成",
  "document.parse.completed": "内容解析完成",
  "document.classification.completed": "文档分类完成",
  "document.extraction.completed": "字段提取完成",
  "document.quality.checked": "质量检查完成",
  "document.result.published": "处理结果已生成",
  "document.review.decided": "确认状态已更新",
};

const processingStageLabels: Record<string, string> = {
  PENDING: "等待处理",
  SCANNING: "安全检查",
  PARSING: "内容解析",
  CLASSIFYING: "文档分类",
  EXTRACTING: "字段提取",
  QUALITY_CHECK: "质量检查",
  REVIEW_REQUIRED: "等待人工确认",
  READY: "处理完成",
};

function processingEventLabel(event: DocumentProcessingEventSnapshot) {
  return processingEventLabels[event.type]
    ?? processingStageLabels[event.stage]
    ?? "处理状态已更新";
}

function processingPlanLabel(plan: Record<string, unknown>) {
  const parts = [plan.largeDocument ? "大文件分片" : "普通文件"];
  if (typeof plan.pageCount === "number") parts.push(`${plan.pageCount} 页`);
  const groupCount = plan.groupCount ?? (Array.isArray(plan.pageBatches) ? plan.pageBatches.length : undefined);
  if (typeof groupCount === "number") parts.push(`${groupCount} 个页组`);
  return parts.join("，");
}

function Metric({ label, value, icon }: { label: string; value: string; icon?: ReactNode }) {
  return (
    <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-900">
      <p className="flex items-center gap-1 text-xs text-gray-500">{icon}{label}</p>
      <p className="mt-1 font-medium text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

function ReviewCard({
  icon,
  title,
  description,
  saved,
  savedLabel = "已保存",
  pendingLabel,
  children,
}: {
  icon: ReactNode;
  title: string;
  description: ReactNode;
  saved: boolean;
  savedLabel?: string;
  pendingLabel?: string;
  children: ReactNode;
}) {
  return (
    <section
      className="rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 px-4 pt-4">
        <div className="flex min-w-0 items-start gap-2.5">
          <span className="mt-0.5 shrink-0 text-brand-500">{icon}</span>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h3>
            <div className="mt-1 text-xs leading-5 text-gray-500">{description}</div>
          </div>
        </div>
        <SaveStateBadge saved={saved} label={savedLabel} pendingLabel={pendingLabel} />
      </div>
      <div className="space-y-3 p-4 pt-3">{children}</div>
    </section>
  );
}

function SaveStateBadge({
  saved,
  label = "已保存",
  pendingLabel = "待保存",
}: {
  saved: boolean;
  label?: string;
  pendingLabel?: string;
}) {
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        saved
          ? "bg-success-50 text-success-700 dark:bg-success-500/10 dark:text-success-300"
          : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
      }`}
    >
      {saved ? <Check className="size-3.5" /> : <span className="size-1.5 rounded-full bg-current" />}
      {saved ? label : pendingLabel}
    </span>
  );
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
      ...(documentType?.confirmedLabel ? [{ label: documentType.confirmedLabel, displayName: documentType.confirmedLabel }] : []),
      ...(documentType?.label ? [{ label: documentType.label, displayName: documentType.displayName }] : []),
      ...(documentType?.alternatives ?? []),
    ];
    return Array.from(new Map(values.map((item) => [item.label, item])).values());
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
  const selectedLabel = label || documentType.confirmedLabel || documentType.label || "";
  const isSaved = Boolean(documentType.confirmedLabel && selectedLabel === documentType.confirmedLabel);
  return (
    <ReviewCard
      icon={<Tags className="size-5" />}
      title="文档分类"
      saved={isSaved}
      pendingLabel={documentType.confirmedLabel ? "有更改" : "待确认"}
      description={(
        <>
          机器结果：{documentType.displayName || documentType.label}（置信度 {Math.round((documentType.confidence ?? 0) * 100)}%）
          {!documentType.confirmedLabel ? " · 确认后才可变为可用" : null}
        </>
      )}
    >
      <div className="flex flex-wrap items-center gap-2">
        <select
          aria-label="确认文档分类"
          className={`${fieldClass} min-w-56 flex-1`}
          value={selectedLabel}
          onChange={(event) => {
            setLabel(event.target.value);
            setNotice("");
          }}
        >
          {options.map((item) => <option key={item.label} value={item.label}>{item.displayName || item.label}</option>)}
        </select>
        {!isSaved ? (
          <Button size="sm" loading={confirm.isPending} onClick={() => confirm.mutate()}>
            {documentType.confirmedLabel ? "保存更改" : "确认分类"}
          </Button>
        ) : null}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {notice ? <p role="status" className="text-sm text-success-700 dark:text-success-400">{notice}</p> : null}
      </div>
      {confirm.isError ? <p role="alert" className="text-sm text-error-600">{confirm.error.message}</p> : null}
    </ReviewCard>
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
  const savedFieldCount = fields.filter((field) => (
    ["AUTO_ACCEPTED", "CONFIRMED", "CORRECTED"].includes(field.reviewStatus)
    && (values[field.fieldPath] === undefined
      || values[field.fieldPath] === stringifyFieldValue(field.confirmedValue ?? field.value))
  )).length;
  const allFieldsSaved = savedFieldCount === fields.length;
  return (
    <ReviewCard
      icon={<ListChecks className="size-5" />}
      title="字段确认"
      saved={allFieldsSaved}
      pendingLabel={savedFieldCount ? `已保存 ${savedFieldCount}/${fields.length}` : undefined}
      description={`共 ${fields.length} 个字段，机器原值始终保留，可安全修正确认值。`}
    >
      {!allFieldsSaved ? (
        <div className="flex justify-end">
          <Button size="sm" variant="outline" loading={confirm.isPending} onClick={() => confirm.mutate(true)}>
            批量确认高置信度
          </Button>
        </div>
      ) : null}
      <div className="divide-y divide-gray-100 border-y border-gray-100 dark:divide-gray-800 dark:border-gray-800">
        {fields.map((field) => {
          const displayedValue = values[field.fieldPath] ?? stringifyFieldValue(field.confirmedValue ?? field.value);
          const fieldSaved = ["AUTO_ACCEPTED", "CONFIRMED", "CORRECTED"].includes(field.reviewStatus)
            && (values[field.fieldPath] === undefined
              || displayedValue === stringifyFieldValue(field.confirmedValue ?? field.value));
          return (
            <label
              key={field.fieldPath}
              className="block py-3 text-xs font-medium"
            >
              <span className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-gray-700 dark:text-gray-300">
                  {field.displayName}
                  <span className="ml-2 font-normal text-gray-500">置信度 {Math.round(field.confidence * 100)}%</span>
                </span>
                {fieldSaved ? <span className="inline-flex items-center gap-1 font-medium text-success-700 dark:text-success-400"><Check className="size-3.5" />已保存</span> : null}
              </span>
              <input
                aria-label={field.displayName}
                className={`mt-2 ${fieldClass}`}
                value={displayedValue}
                onChange={(event) => {
                  setNotice("");
                  setValues((current) => ({ ...current, [field.fieldPath]: event.target.value }));
                }}
              />
              <DocumentEvidenceViewer evidence={field.evidenceRefs} />
            </label>
          );
        })}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {!allFieldsSaved ? (
          <Button size="sm" loading={confirm.isPending} onClick={() => confirm.mutate(false)}>
            {savedFieldCount ? "保存更改" : "保存字段确认"}
          </Button>
        ) : null}
        {notice ? <p role="status" className="text-sm text-success-700 dark:text-success-400">{notice}</p> : null}
      </div>
      {confirm.isError ? <p role="alert" className="text-sm text-error-600">{confirm.error.message}</p> : null}
    </ReviewCard>
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
  const [savedWorkKeys, setSavedWorkKeys] = useState(document.businessWorkKeys);
  const [notice, setNotice] = useState("");
  const isSaved = sameStringSet(workKeys, savedWorkKeys);
  const save = useMutation({
    mutationFn: () => api.updateDocumentBindings(tenantId, projectId, document.documentId, {
      businessObjectIds: document.businessObjectIds,
      businessWorkKeys: workKeys,
    }),
    onSuccess: async () => {
      setSavedWorkKeys(workKeys);
      setNotice("绑定已保存成功。");
      await onSaved?.();
    },
  });
  return (
    <ReviewCard
      icon={<Link2 className="size-5" />}
      title="业务绑定"
      saved={isSaved}
      pendingLabel="有更改"
      description="只关联业务工作，不会改变「需确认 / 可用」处理状态。"
    >
      <div className="grid gap-2 sm:grid-cols-2">
        {workOptions.map((work) => (
          <label key={work.key} className="flex cursor-pointer items-center gap-2.5 rounded-lg bg-gray-50 px-3 py-2.5 text-sm text-gray-700 dark:bg-gray-800/60 dark:text-gray-300">
            <input
              type="checkbox"
              className="size-4 rounded border-gray-300 accent-brand-500"
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
      <div className="flex flex-wrap items-center gap-3">
        {!isSaved ? <Button size="sm" loading={save.isPending} onClick={() => save.mutate()}>保存绑定</Button> : null}
        {notice ? <p role="status" className="text-sm text-success-700 dark:text-success-400">{notice}</p> : null}
      </div>
      {save.isError ? <p role="alert" className="text-sm text-error-600">{save.error.message}</p> : null}
    </ReviewCard>
  );
}

function sameStringSet(left: string[], right: string[]) {
  return left.length === right.length && left.every((value) => right.includes(value));
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
