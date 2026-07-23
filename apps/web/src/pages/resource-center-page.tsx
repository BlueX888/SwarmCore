import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
        <p className="mt-1 text-sm leading-6 text-gray-500">集中管理项目文件、业务关联和业务工作绑定。上传后即可选择这些文件将用于哪些工作。</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" onClick={() => void documents.refetch()} loading={documents.isFetching}><RefreshCw />刷新</Button>
        <Button onClick={() => setShowUpload(true)}><Upload />上传文件</Button>
      </div>
    </header>

    {showUpload ? <UploadPanel tenantId={tenantId} projectId={projectId} onClose={() => setShowUpload(false)} onSaved={async () => {
      setShowUpload(false);
      await queryClient.invalidateQueries({ queryKey: ["documents", tenantId, projectId] });
    }} /> : null}

    <Card><CardContent className="space-y-4 p-5">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_12rem_10rem]">
        <label className="relative"><span className="sr-only">搜索文件</span><Search className="pointer-events-none absolute left-3 top-2.5 size-5 text-gray-400" /><input aria-label="搜索文件" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索文件名或标签" className={`${fieldClass} pl-10`} /></label>
        <label className="relative"><span className="sr-only">按分类筛选</span><Filter className="pointer-events-none absolute left-3 top-2.5 size-4 text-gray-400" /><select aria-label="按分类筛选" value={category} onChange={(event) => setCategory(event.target.value)} className={`${fieldClass} pl-9`}><option value="">全部分类</option>{categories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
        <select aria-label="按状态筛选" value={status} onChange={(event) => setStatus(event.target.value)} className={fieldClass}><option value="">全部状态</option>{Object.entries(statuses).map(([value, item]) => <option key={value} value={value}>{item.label}</option>)}</select>
      </div>

      {documents.isPending ? <Skeleton className="h-72" /> : null}
      {documents.isError ? <div role="alert" className="rounded-xl border border-error-200 bg-error-50 p-6 text-center dark:border-error-500/20 dark:bg-error-500/10"><CircleAlert className="mx-auto size-7 text-error-600" /><p className="mt-2 font-medium text-error-700">业务资料库加载失败</p><p className="mt-1 text-sm text-error-600">{documents.error.message}</p></div> : null}
      {documents.data && !items.length ? <EmptyDocuments filtered={Boolean(search || category || status)} onUpload={() => setShowUpload(true)} /> : null}
      {items.length ? <DocumentTable items={items} onSelect={setSelected} /> : null}
    </CardContent></Card>

    {selected ? <DocumentDetails tenantId={tenantId} projectId={projectId} document={selected} onClose={() => setSelected(null)} /> : null}
  </div>;
}

function UploadPanel({ tenantId, projectId, onClose, onSaved }: { tenantId: string; projectId: string; onClose: () => void; onSaved: () => Promise<void> }) {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [category, setCategory] = useState("CONTRACT");
  const [tags, setTags] = useState("");
  const [objectType, setObjectType] = useState("");
  const [objectKey, setObjectKey] = useState("");
  const [workKeys, setWorkKeys] = useState<string[]>([]);
  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("请选择要上传的文件。");
      let businessObjectIds: string[] = [];
      if (objectType.trim() || objectKey.trim()) {
        if (!objectType.trim() || !objectKey.trim()) throw new Error("请同时填写业务对象类型和业务编号。");
        const object = await api.createBusinessObject(tenantId, projectId, {
          objectType: objectType.trim(),
          canonicalKey: objectKey.trim(),
          schemaRef: `schema://business/${objectType.trim()}@1`,
          data: { title: objectKey.trim() },
          provenance: { source: "document-library" },
        });
        businessObjectIds = [object.businessObjectId];
      }
      const digest = await sha256File(file);
      const handle = await api.initiateDocument(tenantId, projectId, {
        name: name.trim() || file.name,
        category,
        tags: tags.split(/[,，]/).map((value) => value.trim()).filter(Boolean),
        filename: file.name,
        mediaType: file.type || "application/octet-stream",
        sizeBytes: file.size,
        sha256: digest,
        businessObjectIds,
        businessWorkKeys: workKeys,
      });
      await api.uploadDocumentContent(handle, file);
      return api.completeDocument(tenantId, projectId, handle.uploadId, digest);
    },
    onSuccess: onSaved,
  });

  const toggleWork = (key: string) => setWorkKeys((current) => current.includes(key) ? current.filter((value) => value !== key) : [...current, key]);

  return <Card><CardContent className="space-y-5 p-5">
    <div className="flex items-start justify-between gap-3"><div><h2 className="font-semibold text-gray-900 dark:text-white">上传文件</h2><p className="mt-1 text-sm text-gray-500">选择文件、业务关联和需要使用它的业务工作，然后保存。</p></div><Button variant="ghost" size="icon" aria-label="关闭上传表单" onClick={onClose}><X /></Button></div>
    <div className="grid gap-4 lg:grid-cols-2">
      <label className="lg:col-span-2 rounded-xl border border-dashed border-gray-300 p-5 text-sm dark:border-gray-700"><span className="font-medium text-gray-800 dark:text-gray-200">选择文件</span><input aria-label="选择文件" type="file" className="mt-3 block w-full text-sm text-gray-500 file:mr-3 file:rounded-lg file:border-0 file:bg-brand-50 file:px-3 file:py-2 file:text-brand-700" onChange={(event) => { const next = event.target.files?.[0] ?? null; setFile(next); if (next && !name) setName(next.name); }} /><span className="mt-2 block text-xs text-gray-500">{file ? `${file.name} · ${formatBytes(file.size)}` : "支持项目允许的常见文档格式"}</span></label>
      <Field label="资料名称" value={name} onChange={setName} placeholder="默认使用文件名" />
      <label className="text-xs font-medium text-gray-700 dark:text-gray-300">文件分类<select aria-label="文件分类" value={category} onChange={(event) => setCategory(event.target.value)} className={`mt-2 ${fieldClass}`}>{categories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
      <Field label="标签" value={tags} onChange={setTags} placeholder="采购，2026，待评审" help="多个标签用逗号分隔" />
      <div className="grid grid-cols-2 gap-2"><Field label="业务对象类型" value={objectType} onChange={setObjectType} placeholder="contract" /><Field label="业务编号" value={objectKey} onChange={setObjectKey} placeholder="HT-2026-001" /></div>
    </div>
    <fieldset><legend className="text-xs font-medium text-gray-700 dark:text-gray-300">使用这些资料的业务工作</legend><p className="mt-1 text-xs text-gray-500">可多选；系统执行时会按分类和业务关联自动匹配。</p><div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{BUSINESS_WORKS.map((work) => <label key={work.key} className={`flex cursor-pointer items-start gap-2 rounded-lg border p-3 text-sm ${workKeys.includes(work.key) ? "border-brand-400 bg-brand-50/60 dark:bg-brand-500/10" : "border-gray-200 dark:border-gray-800"}`}><input type="checkbox" checked={workKeys.includes(work.key)} onChange={() => toggleWork(work.key)} className="mt-0.5" /><span><span className="block font-medium text-gray-800 dark:text-gray-200">{work.shortName}</span><span className="mt-0.5 block text-xs text-gray-500">{work.summary}</span></span></label>)}</div></fieldset>
    {upload.isError ? <p role="alert" className="text-sm text-error-600">{upload.error.message}</p> : null}
    <div className="flex flex-wrap justify-end gap-2"><Button variant="outline" onClick={onClose}>取消</Button><Button loading={upload.isPending} disabled={!file || !workKeys.length} onClick={() => upload.mutate()}><Upload />保存资料</Button></div>
  </CardContent></Card>;
}

function DocumentTable({ items, onSelect }: { items: DocumentSnapshot[]; onSelect: (value: DocumentSnapshot) => void }) {
  return <div className="overflow-x-auto"><table className="w-full min-w-[900px] text-left text-sm"><thead><tr className="border-b border-gray-200 text-xs text-gray-500 dark:border-gray-800"><th className="px-3 py-3 font-medium">文件</th><th className="px-3 py-3 font-medium">类型 / 大小</th><th className="px-3 py-3 font-medium">版本</th><th className="px-3 py-3 font-medium">状态</th><th className="px-3 py-3 font-medium">业务关联</th><th className="px-3 py-3 font-medium">业务工作</th><th className="px-3 py-3 font-medium">更新时间</th><th className="px-3 py-3 font-medium"><span className="sr-only">操作</span></th></tr></thead><tbody>{items.map((item) => <tr key={item.documentId} className="border-b border-gray-100 last:border-0 dark:border-gray-800/70"><td className="px-3 py-3"><div className="flex items-center gap-2"><span className="grid size-9 place-items-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10"><FileText className="size-4" /></span><div className="min-w-0"><p className="max-w-56 truncate font-medium text-gray-900 dark:text-white">{item.name}</p><p className="max-w-56 truncate text-xs text-gray-500">{item.current?.filename ?? "等待上传完成"}</p></div></div></td><td className="px-3 py-3 text-gray-600 dark:text-gray-300">{categoryLabel(item.category)}<span className="block text-xs text-gray-500">{item.current ? formatBytes(item.current.sizeBytes) : "—"}</span></td><td className="px-3 py-3">v{item.currentVersion || 1}</td><td className="px-3 py-3"><StatusBadge status={item.status} /></td><td className="px-3 py-3 text-xs text-gray-500">{item.businessObjectIds.length ? `${item.businessObjectIds.length} 项关联` : "未关联"}</td><td className="px-3 py-3 text-xs text-gray-500">{item.businessWorkKeys.length ? `${item.businessWorkKeys.length} 项工作` : "待选择"}</td><td className="px-3 py-3 text-xs text-gray-500">{new Date(item.updatedAt).toLocaleString("zh-CN")}</td><td className="px-3 py-3"><Button variant="ghost" size="sm" onClick={() => onSelect(item)}><Eye />详情</Button></td></tr>)}</tbody></table></div>;
}

function DocumentDetails({ tenantId, projectId, document, onClose }: { tenantId: string; projectId: string; document: DocumentSnapshot; onClose: () => void }) {
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
  return <Card><CardContent className="space-y-4 p-5"><div className="flex items-start justify-between gap-3"><div><p className="text-xs text-brand-500">文件详情与预览</p><h2 className="mt-1 font-semibold text-gray-900 dark:text-white">{document.name}</h2></div><div className="flex gap-2">{document.current ? <Button variant="outline" size="sm" loading={download.isPending} onClick={() => download.mutate()}><Download />下载当前版本</Button> : null}<Button variant="ghost" size="icon" aria-label="关闭文件详情" onClick={onClose}><X /></Button></div></div><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Detail label="文件类型" value={document.current?.mediaType ?? "等待上传"} /><Detail label="文件大小" value={document.current ? formatBytes(document.current.sizeBytes) : "—"} /><Detail label="当前版本" value={`v${document.currentVersion || 1}`} /><Detail label="校验摘要" value={document.current ? document.current.sha256.slice(0, 16) : "—"} /></div><div><p className="text-xs font-medium text-gray-500">业务工作</p><div className="mt-2 flex flex-wrap gap-2">{document.businessWorkKeys.map((key) => <span key={key} className="rounded-full bg-gray-100 px-2.5 py-1 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">{BUSINESS_WORKS.find((work) => work.key === key)?.shortName ?? key}</span>)}</div></div>{download.isError ? <p role="alert" className="text-sm text-error-600">{download.error.message}</p> : null}<p className="rounded-lg bg-gray-50 p-3 text-xs leading-5 text-gray-500 dark:bg-gray-900">在线预览会在文件上传完成且格式受支持后提供；原始文件下载始终使用已冻结的具体版本。</p></CardContent></Card>;
}

function EmptyDocuments({ filtered, onUpload }: { filtered: boolean; onUpload: () => void }) {
  return <div className="flex min-h-64 flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 px-6 text-center dark:border-gray-800"><span className="grid size-12 place-items-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-500/10"><FileText /></span><h2 className="mt-3 font-medium text-gray-900 dark:text-white">{filtered ? "没有匹配的文件" : "还没有业务资料"}</h2><p className="mt-1 max-w-md text-sm text-gray-500">{filtered ? "调整搜索或筛选条件后再试。" : "上传文件并选择业务关联和业务工作，即可开始使用。"}</p>{!filtered ? <Button className="mt-4" onClick={onUpload}><Upload />上传第一个文件</Button> : null}</div>;
}

function StatusBadge({ status }: { status: string }) {
  const item = statuses[status] ?? { label: status, tone: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300" };
  const Icon = status === "AVAILABLE" ? Check : status === "UPLOADING" || status === "PROCESSING" ? LoaderCircle : CircleAlert;
  return <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${item.tone}`}><Icon className={`size-3.5 ${status === "UPLOADING" || status === "PROCESSING" ? "animate-spin" : ""}`} />{item.label}</span>;
}

function Field({ label, value, onChange, placeholder, help }: { label: string; value: string; onChange: (value: string) => void; placeholder?: string; help?: string }) {
  return <label className="text-xs font-medium text-gray-700 dark:text-gray-300">{label}<input aria-label={label} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} className={`mt-2 ${fieldClass}`} />{help ? <span className="mt-1 block font-normal text-gray-500">{help}</span> : null}</label>;
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

// Compatibility export for imports that have not yet moved to the product name.
export const ResourceCenterPage = DocumentLibraryPage;
