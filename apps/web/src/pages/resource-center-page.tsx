import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import {
  Check,
  CircleAlert,
  Download,
  Eye,
  FileText,
  Filter,
  LoaderCircle,
  RefreshCw,
  Search,
  Upload,
  X,
} from "lucide-react";
import { api } from "@/api/client";
import type { DocumentSnapshot } from "@/api/types";
import {
  DocumentBindingEditor,
  DocumentClassificationReview,
  DocumentExtractionReviewForm,
  DocumentProcessingStatus,
  DocumentUploadPanel,
} from "@/components/documents/document-intake";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BUSINESS_WORKS } from "@/lib/business-works";
import { useWorkspaceScope } from "@/lib/demo-scope";

const fieldClass = "h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm outline-none focus:border-brand-500 dark:border-gray-700 dark:bg-gray-900";

const categories = [
  { value: "CONTRACT", label: "合同文件" },
  { value: "PERFORMANCE", label: "履约资料" },
  { value: "INVOICE", label: "发票资料" },
  { value: "DEVIATION", label: "偏差资料" },
  { value: "SUPPLIER", label: "供应商资料" },
  { value: "REPORT", label: "报告与成果" },
  { value: "OTHER", label: "其他资料" },
];

const statuses: Record<string, { label: string; tone: string }> = {
  UPLOADING: { label: "上传中", tone: "bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300" },
  PROCESSING: { label: "解析中", tone: "bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300" },
  AVAILABLE: { label: "可用", tone: "bg-success-50 text-success-700 dark:bg-success-500/10 dark:text-success-300" },
  REVIEW_REQUIRED: { label: "需确认", tone: "bg-warning-50 text-warning-700 dark:bg-warning-500/10 dark:text-warning-300" },
  FAILED: { label: "失败", tone: "bg-error-50 text-error-700 dark:bg-error-500/10 dark:text-error-300" },
};

export function DocumentLibraryPage() {
  const { tenantId, projectId } = useWorkspaceScope();
  const queryClient = useQueryClient();
  const [showUpload, setShowUpload] = useState(false);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<DocumentSnapshot | null>(null);
  const documents = useQuery({
    queryKey: ["documents", tenantId, projectId],
    queryFn: () => api.listDocuments(tenantId, projectId),
  });
  const resumeUpload = useMutation({
    mutationFn: (documentId: string) => api.resumeDocumentUpload(tenantId, projectId, documentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["documents", tenantId, projectId] });
    },
  });
  const items = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (documents.data?.items ?? []).filter((item) => {
      const matchesSearch = !needle || `${item.name} ${item.current?.filename ?? ""} ${item.tags.join(" ")}`.toLowerCase().includes(needle);
      return matchesSearch && (!category || item.category === category) && (!status || item.status === status);
    });
  }, [category, documents.data, search, status]);

  return <div className="min-w-0 space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-2xl">
        <p className="text-sm font-medium text-brand-500">业务资料</p>
        <h1 className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">业务资料库</h1>
        <p className="mt-1 text-sm leading-6 text-gray-500">集中上传、解析、确认和绑定业务文件。用户只需处理文件与表单，无需理解内部 Schema 或 Blob ID。</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" onClick={() => void documents.refetch()} loading={documents.isFetching}><RefreshCw />刷新</Button>
        <Button onClick={() => setShowUpload(true)}><Upload />上传文件</Button>
      </div>
    </header>

    {showUpload ? <DocumentUploadPanel
      tenantId={tenantId}
      projectId={projectId}
      context={{ businessWorkKeys: [], category: "CONTRACT" }}
      onClose={() => setShowUpload(false)}
      onCompleted={async () => {
        setShowUpload(false);
        await queryClient.invalidateQueries({ queryKey: ["documents", tenantId, projectId] });
      }}
    /> : null}

    <Card><CardContent className="space-y-4 p-5">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_12rem_10rem]">
        <label className="relative"><span className="sr-only">搜索文件</span><Search className="pointer-events-none absolute left-3 top-2.5 size-5 text-gray-400" /><input aria-label="搜索文件" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索文件名或标签" className={`${fieldClass} pl-10`} /></label>
        <label className="relative"><span className="sr-only">按分类筛选</span><Filter className="pointer-events-none absolute left-3 top-2.5 size-4 text-gray-400" /><select aria-label="按分类筛选" value={category} onChange={(event) => setCategory(event.target.value)} className={`${fieldClass} pl-9`}><option value="">全部分类</option>{categories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
        <select aria-label="按状态筛选" value={status} onChange={(event) => setStatus(event.target.value)} className={fieldClass}><option value="">全部状态</option>{Object.entries(statuses).map(([value, item]) => <option key={value} value={value}>{item.label}</option>)}</select>
      </div>

      {documents.isPending ? <Skeleton className="h-72" /> : null}
      {documents.isError ? <div role="alert" className="rounded-xl border border-error-200 bg-error-50 p-6 text-center dark:border-error-500/20 dark:bg-error-500/10"><CircleAlert className="mx-auto size-7 text-error-600" /><p className="mt-2 font-medium text-error-700">业务资料库加载失败</p><p className="mt-1 text-sm text-error-600">{documents.error.message}</p></div> : null}
      {resumeUpload.isError ? <p role="alert" className="text-sm text-error-600">{resumeUpload.error.message}</p> : null}
      {documents.data && !items.length ? <EmptyDocuments filtered={Boolean(search || category || status)} onUpload={() => setShowUpload(true)} /> : null}
      {items.length ? <DocumentTable
        items={items}
        onSelect={setSelected}
        onResume={(item) => resumeUpload.mutate(item.documentId)}
        resumingId={resumeUpload.isPending ? resumeUpload.variables ?? null : null}
      /> : null}
    </CardContent></Card>

    {selected ? (
      <DocumentDetailsDialog
        tenantId={tenantId}
        projectId={projectId}
        document={selected}
        onClose={() => setSelected(null)}
        onChanged={async () => {
          await queryClient.invalidateQueries({ queryKey: ["documents", tenantId, projectId] });
          const latest = await api.getDocument(tenantId, projectId, selected.documentId);
          setSelected(latest);
        }}
      />
    ) : null}
  </div>;
}

function DocumentTable({
  items,
  onSelect,
  onResume,
  resumingId,
}: {
  items: DocumentSnapshot[];
  onSelect: (value: DocumentSnapshot) => void;
  onResume: (value: DocumentSnapshot) => void;
  resumingId: string | null;
}) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[900px] text-left text-sm"><thead><tr className="border-b border-gray-200 text-xs text-gray-500 dark:border-gray-800"><th className="px-3 py-3 font-medium">文件</th><th className="px-3 py-3 font-medium">类型 / 大小</th><th className="px-3 py-3 font-medium">版本</th><th className="px-3 py-3 font-medium">状态</th><th className="px-3 py-3 font-medium">业务关联</th><th className="px-3 py-3 font-medium">业务工作</th><th className="px-3 py-3 font-medium">更新时间</th><th className="px-3 py-3 font-medium"><span className="sr-only">操作</span></th></tr></thead><tbody>{items.map((item) => <tr key={item.documentId} className="border-b border-gray-100 last:border-0 dark:border-gray-800/70"><td className="px-3 py-3"><div className="flex items-center gap-2"><span className="grid size-9 place-items-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10"><FileText className="size-4" /></span><div className="min-w-0"><p className="max-w-56 truncate font-medium text-gray-900 dark:text-white">{item.name}</p><p className="max-w-56 truncate text-xs text-gray-500">{item.current?.filename ?? "文件已接收，等待完成登记"}</p></div></div></td><td className="px-3 py-3 text-gray-600 dark:text-gray-300">{categoryLabel(item.category)}<span className="block text-xs text-gray-500">{item.current ? formatBytes(item.current.sizeBytes) : "—"}</span></td><td className="px-3 py-3">v{item.currentVersion || "—"}</td><td className="px-3 py-3"><StatusBadge status={item.status} /></td><td className="px-3 py-3 text-xs text-gray-500">{item.businessObjectIds.length ? `${item.businessObjectIds.length} 项关联` : "未关联"}</td><td className="px-3 py-3 text-xs text-gray-500">{item.businessWorkKeys.length ? `${item.businessWorkKeys.length} 项工作` : "待选择"}</td><td className="px-3 py-3 text-xs text-gray-500">{new Date(item.updatedAt).toLocaleString("zh-CN")}</td><td className="px-3 py-3"><div className="flex flex-wrap gap-1">{item.status === "UPLOADING" ? <Button variant="outline" size="sm" loading={resumingId === item.documentId} onClick={() => onResume(item)}>继续完成</Button> : null}<Button variant="ghost" size="sm" onClick={() => onSelect(item)}><Eye />详情</Button></div></td></tr>)}</tbody></table></div>;
}

function DocumentDetailsDialog({
  tenantId,
  projectId,
  document,
  onClose,
  onChanged,
}: {
  tenantId: string;
  projectId: string;
  document: DocumentSnapshot;
  onClose: () => void;
  onChanged: () => Promise<void>;
}) {
  const download = useMutation({
    mutationFn: async () => {
      const result = await api.downloadDocumentVersion(tenantId, projectId, document.documentId, document.currentVersion);
      const url = URL.createObjectURL(result.content);
      const link = globalThis.document.createElement("a");
      link.href = url;
      link.download = result.filename;
      link.click();
      URL.revokeObjectURL(url);
    },
  });
  const reprocess = useMutation({
    mutationFn: () => api.reprocessDocument(tenantId, projectId, document.documentId),
    onSuccess: onChanged,
  });

  return (
    <Dialog.Root
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-gray-950/50 backdrop-blur-[2px]" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100vw-2rem)] max-w-4xl -translate-x-1/2 -translate-y-1/2 outline-none">
          <div className="flex max-h-[92vh] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-theme-xl dark:border-gray-800 dark:bg-gray-900">
            <div className="flex shrink-0 items-start justify-between gap-4 border-b border-gray-100 p-5 dark:border-gray-800">
              <div className="min-w-0">
                <p className="text-xs text-brand-500">文件详情与处理确认</p>
                <Dialog.Title asChild>
                  <h2 className="mt-1 truncate font-semibold text-gray-900 dark:text-white">{document.name}</h2>
                </Dialog.Title>
                <Dialog.Description className="mt-1 text-sm text-gray-500">
                  {document.status === "REVIEW_REQUIRED"
                    ? "当前为需确认：请先确认分类 / 字段，「保存绑定」不会解除该状态。"
                    : "查看处理状态、确认结果，并绑定到业务工作。"}
                </Dialog.Description>
              </div>
              <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
                <StatusBadge status={document.status} />
                {document.current ? (
                  <Button variant="outline" size="sm" loading={download.isPending} onClick={() => download.mutate()}>
                    <Download />下载
                  </Button>
                ) : null}
                <Button variant="outline" size="sm" loading={reprocess.isPending} onClick={() => reprocess.mutate()}>
                  重新处理
                </Button>
                <Dialog.Close asChild>
                  <Button variant="ghost" size="icon" aria-label="关闭文件详情">
                    <X />
                  </Button>
                </Dialog.Close>
              </div>
            </div>

            <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-5">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Detail label="文件类型" value={document.current?.mediaType ?? "等待上传"} />
                <Detail label="文件大小" value={document.current ? formatBytes(document.current.sizeBytes) : "—"} />
                <Detail label="当前版本" value={`v${document.currentVersion || 1}`} />
                <Detail label="校验摘要" value={document.current ? document.current.sha256.slice(0, 16) : "—"} />
              </div>
              <DocumentProcessingStatus tenantId={tenantId} projectId={projectId} documentId={document.documentId} />
              <DocumentClassificationReview
                tenantId={tenantId}
                projectId={projectId}
                documentId={document.documentId}
                onConfirmed={onChanged}
              />
              <DocumentExtractionReviewForm
                tenantId={tenantId}
                projectId={projectId}
                documentId={document.documentId}
                onConfirmed={onChanged}
              />
              <DocumentBindingEditor
                tenantId={tenantId}
                projectId={projectId}
                document={document}
                workOptions={BUSINESS_WORKS.map((work) => ({ key: work.key, label: work.shortName }))}
                onSaved={onChanged}
              />
              {download.isError ? <p role="alert" className="text-sm text-error-600">{download.error.message}</p> : null}
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function EmptyDocuments({ filtered, onUpload }: { filtered: boolean; onUpload: () => void }) {
  return <div className="flex min-h-64 flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 px-6 text-center dark:border-gray-800"><span className="grid size-12 place-items-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-500/10"><FileText /></span><h2 className="mt-3 font-medium text-gray-900 dark:text-white">{filtered ? "没有匹配的文件" : "还没有业务资料"}</h2><p className="mt-1 max-w-md text-sm text-gray-500">{filtered ? "调整搜索或筛选条件后再试。" : "上传文件并完成解析确认后，即可绑定到业务工作。"}</p>{!filtered ? <Button className="mt-4" onClick={onUpload}><Upload />上传第一个文件</Button> : null}</div>;
}

function StatusBadge({ status }: { status: string }) {
  const item = statuses[status] ?? { label: status, tone: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300" };
  const Icon = status === "AVAILABLE" ? Check : status === "UPLOADING" || status === "PROCESSING" ? LoaderCircle : CircleAlert;
  return <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${item.tone}`}><Icon className={`size-3.5 ${status === "UPLOADING" || status === "PROCESSING" ? "animate-spin" : ""}`} />{item.label}</span>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-900"><p className="text-xs text-gray-500">{label}</p><p className="mt-1 truncate text-sm font-medium text-gray-800 dark:text-gray-200" title={value}>{value}</p></div>;
}

function categoryLabel(value: string) {
  return categories.find((item) => item.value === value)?.label ?? value;
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export async function sha256File(file: File) {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
}

export const ResourceCenterPage = DocumentLibraryPage;
